# 稳定 SVG 渲染方案技术方案

> 适用范围:投标配图工具 Tier 1「冻结 SVG 模板 + 契约生成」路径的渲染与校验实现。
> 目标:让模板路径产出的 SVG **稳定**(零文字爆框 / 零元素重叠 / 跨环境一致)且**精美**,把图 3-2 那种质量上限稳定复制到每一张图。

---

## 1. 背景与问题

对现有 5 张参考图的实测发现:

- 文字换行由生成时**按字符硬切**并以多个独立 `<text>` 摆放(源码零 `tspan`、零 `foreignObject`),导致 mid-word 断词("Unified ide | ntity"、"respon | se")。
- 切出的多行超出固定框高,与相邻元素、内部子框、卡片相撞。
- manifest 却报 `fit_score: 1.0` / `violations: 0` / `needs_human_review: false`——**校验在逻辑层(数字符),失败在几何层(渲染溢出)**,成功判断失真。
- SVG **未内嵌字体**,依赖系统 `Microsoft YaHei / Arial`,换环境度量漂移、溢出加剧。
- 另有与文字无关的真实模板缺陷:副标题重复绘制、序号/状态徽标压标题、卫星卡压圆环与底条、分区胶囊裁切标题。

**根因一句话:生成时按假设的字体度量"猜"宽度,且校验对象错配。**

---

## 2. 设计原则

1. **测量,而不是猜测。** 一套字体 + 一个测量引擎,被「换行 / 校验 / 渲染」三处共用,三者度量必须**完全一致**;算出来的宽度即渲染出来的宽度。
2. **几何即真相。** "fit" 以渲染几何(bbox)判定,不以字符数判定。任何溢出/重叠都不得报成功。
3. **冻结与填充分离。** 模板的几何与视觉(背景、边框、锚点、图标位、槽位矩形)冻结;运行时只填充槽位文字、图标 id 选择、主题色。
4. **自包含、可移植。** 字体子集化内嵌、图标内嵌为矢量,SVG 不依赖任何外部资源。
5. **装不下时改写,不硬切。** 缩字号后仍不合规,走 LLM 保意改写 → 变体阶梯 → 降级;绝不静默断词或溢出。

---

## 3. 总体架构

```
契约填充数据
  → 绑定(Bind)            将内容映射到槽位/图标位/连线
  → 排版(Layout)          MeasureEngine 测量 → 词级换行 → 缩字号 → 算 bbox
  → 几何校验(Validate)     超框/重叠/锚点/对比度;违规即拦截
       ├─ 通过 → 生成(Emit)  输出 tspan / use / 连线 / 徽标
       └─ 违规 → 改写 → 变体阶梯 → 降级(每步留痕)
  → 栅格化 QA(可选兜底)     渲染后像素复检
```

落点(现有模块):

| 职责 | 模块 | 性质 |
| --- | --- | --- |
| 字体加载 / 测量 / 换行 / 缩放 | `core/text_measure.py` | **新增** |
| 槽位绑定 + 排版 | `core/normalize.py` | 扩展 |
| 几何校验 | `core/validator.py` | 扩展为几何级 |
| SVG 注入渲染(tspan/use/连线/徽标) | `renderers/svg_v2.py` | 扩展 |
| 字体子集化 + 内嵌 | 构建步骤 / `renderers/_assets.py` | **新增** |
| 决策与降级 | `core/decision.py`、`core/router.py` | 既有 |

---

## 4. 字体地基

### 4.1 选型与子集化

选一款覆盖中英、可商用内嵌的字体(推荐 `Noto Sans CJK SC` / `Source Han Sans SC`)。构建期用 `fontTools.subset` 仅保留实际用到的字形,导出 `woff2`,base64 内嵌。

```python
from fontTools import subset
# 子集化:只保留文档中出现的字符,极大压缩体积
opt = subset.Options(flavor="woff2", desubroutinize=True)
font = subset.load_font("NotoSansCJKsc.otf", opt)
subsetter = subset.Subsetter(opt)
subsetter.populate(text="".join(used_chars))   # 全文用字集合
subsetter.subset(font)
subset.save_font(font, "subset.woff2", opt)     # → base64 内嵌
```

### 4.2 内嵌到 SVG

```svg
<defs><style>
@font-face{font-family:'BidSans';font-weight:400;
  src:url(data:font/woff2;base64,XXXX) format('woff2');}
@font-face{font-family:'BidSans';font-weight:600;
  src:url(data:font/woff2;base64,YYYY) format('woff2');}
text{font-family:'BidSans',sans-serif;}
</style></defs>
```

### 4.3 测量引擎(与渲染同源)

用与内嵌字体**完全相同的文件**做测量。SVG 1:1 渲染时,`font-size=S` 用户单位对应像素宽度 = 该字体在 `S px` 下的字形步进宽度。

```python
from PIL import ImageFont

class MeasureEngine:
    def __init__(self, font_paths: dict):      # {(weight): path}
        self._cache = {}
        self._paths = font_paths
    def _font(self, size, weight=400):
        key = (size, weight)
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(self._paths[weight], size)
        return self._cache[key]
    def width(self, text, size, weight=400) -> float:
        return self._font(size, weight).getlength(text)
    def vmetrics(self, size, weight=400):
        asc, desc = self._font(size, weight).getmetrics()
        return asc, desc                        # 像素
```

> 关键不变式:`MeasureEngine` 加载的字体 = 内嵌进 SVG 的字体 = 渲染所用字体。三者同源,几何才可预测。

---

## 5. 文本槽规范(主战场)

### 5.1 槽位定义(冻结于模板)

```jsonc
{
  "id": "card1.bullet1",
  "x": 80, "y": 220, "w": 220, "h": 56,   // 槽位矩形(冻结)
  "align": "left",                         // left | center | right
  "weight": 400,
  "font_max": 16, "font_min": 12, "font_step": 1,
  "line_height": 1.3,
  "max_lines": 2,
  "color_var": "text-primary",             // 引用主题变量
  "overflow_policy": "shrink_then_rewrite"  // 见 5.5
}
```

### 5.2 词级换行(杜绝 mid-word)

分词规则:拉丁文按空格/连字符切词,词内不断;CJK 每字可断;混排按字符类型分段。

```python
def tokenize(text):
    toks, buf = [], ""
    for ch in text:
        if is_cjk(ch):
            if buf: toks.append(buf); buf = ""
            toks.append(ch)                 # CJK 单字成词
        elif ch == " ":
            if buf: toks.append(buf); buf = ""
            toks.append(" ")
        else:
            buf += ch                       # 拉丁词聚合
    if buf: toks.append(buf)
    return toks

def wrap(text, max_w, size, weight, m: MeasureEngine):
    lines, cur = [], ""
    for tok in tokenize(text):
        trial = cur + tok
        if not cur.strip() or m.width(trial.strip(), size, weight) <= max_w:
            cur = trial
        else:
            lines.append(cur.strip()); cur = tok if tok != " " else ""
    if cur.strip(): lines.append(cur.strip())
    return lines
```

单个拉丁词本身超宽时(罕见),按字符兜底断并加连字符,或交由缩字号/改写解决。

### 5.3 适配算法(measure → wrap → shrink → 失败上交)

```python
def fit(slot, text, m: MeasureEngine):
    size = slot.font_max
    while size >= slot.font_min:
        lines = wrap(text, slot.w, size, slot.weight, m)
        lh = size * slot.line_height
        total_h = len(lines) * lh
        widest = max((m.width(l, size, slot.weight) for l in lines), default=0)
        if (slot.max_lines is None or len(lines) <= slot.max_lines) \
           and total_h <= slot.h and widest <= slot.w:
            return Layout(lines=lines, size=size, ok=True)
        size -= slot.font_step
    return Layout(lines=None, size=slot.font_min, ok=False)   # 上交:改写/变体/降级
```

### 5.4 输出(真正的多行 tspan,垂直居中)

**禁止把一行拆成多个独立 `<text>`。** 用单个 `<text>` + 每行一个 `<tspan>`(`dy` 为相对行距,`x` 统一对齐):

```python
def emit_text(slot, layout, m: MeasureEngine):
    asc, _ = m.vmetrics(layout.size, slot.weight)
    lh = layout.size * slot.line_height
    total_h = len(layout.lines) * lh
    top = slot.y + (slot.h - total_h) / 2
    y0 = top + asc                              # 首行基线
    cx = {"left": slot.x, "center": slot.x + slot.w/2,
          "right": slot.x + slot.w}[slot.align]
    anchor = {"left":"start","center":"middle","right":"end"}[slot.align]
    parts = [f'<text x="{cx:.1f}" y="{y0:.1f}" text-anchor="{anchor}" '
             f'font-size="{layout.size}" font-weight="{slot.weight}" '
             f'fill="var(--{slot.color_var})">']
    for i, line in enumerate(layout.lines):
        dy = 0 if i == 0 else lh
        parts.append(f'<tspan x="{cx:.1f}" dy="{dy:.1f}">{xml_escape(line)}</tspan>')
    parts.append("</text>")
    return "".join(parts)
```

### 5.5 溢出策略

| policy | 行为 |
| --- | --- |
| `wrap_only` | 仅换行,不缩字号(适合高度充裕的多行槽) |
| `shrink` | 换行 + 缩字号到 `font_min` |
| `shrink_then_rewrite` | 缩到底仍不行 → 触发 LLM 保意改写,再排;有界重试 |
| `clamp` | 单行强约束:`textLength` + `lengthAdjust="spacingAndGlyphs"` 微缩(用于胶囊/徽标内固定单行) |
| `fail` | 直接判失败,交决策层走变体阶梯 / 降级 |

保意改写请求体:`{slot_id, original_text, target_max_width_px, current_size, keywords_must_keep}`,要求 LLM 产出更短、不丢关键词的合规文本;返回后重跑 `fit`,仍失败则降级。

---

## 6. 箭头与连线

### 6.1 锚点(冻结于盒子)

每个盒子预定义命名锚点;连线只声明端点与样式,路径由渲染器算。

```jsonc
// 盒子锚点(模板冻结)
"anchors": { "right_mid": [300,140], "left_mid": [60,140],
             "bottom_mid": [180,200], "top_mid": [180,80] }

// 连线声明(填充)
{ "from": "boxA.right_mid", "to": "boxB.left_mid",
  "style": "solid",            // solid | dashed
  "color_var": "flow-1",
  "route": "auto",             // straight | orthogonal | auto
  "label": { "text": "HTTPS JSON", "slot": "mid" }  // 可选
}
```

### 6.2 路径与箭头

- 两端各留 `gap`(默认 8–10px)不触盒子边,防箭头压框。
- `route=auto`:直线若与任一盒子 bbox 相交 → 自动改 L 形正交绕行。
- 箭头 marker 统一定义于 `<defs>`,`orient="auto"`,颜色随线(按色预置 marker 或 `context-stroke`)。

```svg
<defs>
  <marker id="arrow-flow1" markerWidth="12" markerHeight="9" refX="11" refY="4.5"
          orient="auto"><path d="M0,0 L12,4.5 L0,9 Z" fill="var(--flow-1)"/></marker>
</defs>
<path d="M308,140 L520,140" stroke="var(--flow-1)" stroke-width="3"
      fill="none" marker-end="url(#arrow-flow1)"/>
```

### 6.3 连线标签

- 标签放在连线**预留区**(中点上方固定偏移),作为独立校验对象;
- 校验保证标签 bbox 不与箭头三角、不与任一盒子相交;
- 优先把语义写进盒子,减少浮动标签。

---

## 7. 图标

### 7.1 内嵌符号库 + 引用

图标集作为 `<symbol>` 内嵌共享 `<defs>`(纯 path,无外链),模板以 `<use>` 放在固定图标位:

```svg
<defs>
  <symbol id="ic-server" viewBox="0 0 24 24"><path d="..."/></symbol>
  <symbol id="ic-database" viewBox="0 0 24 24"><path d="..."/></symbol>
</defs>
...
<use href="#ic-server" x="60" y="118" width="24" height="24"
     fill="var(--icon)"/>
```

### 7.2 白名单与契约绑定

- 契约的 `icon` 字段白名单 = 符号库 id 集合;生成只能从中选。
- 图标位的 `x/y/width/height` 冻结于模板,运行时只替换引用的 id。
- 纯矢量、与字体无关、跨环境一致;严禁图标字体或外部 URL。

---

## 8. 背景 / 边框 / 徽标

### 8.1 冻结几何与 z 序

绘制顺序固定:**背景 → 区域边框 → 连线 → 内容文字/图标 → 徽标**。徽标(序号圆标、状态标、分区胶囊)只放在内容布局**主动预留的角区**。

### 8.2 徽标与标签二选一自适应(根治"压字/裁切")

- **徽标自适应**:胶囊宽度 = `MeasureEngine.width(label) + 2*padding`,随标签放大;或
- **标签受约束**:固定徽标尺寸,标签走 `clamp`/改写。

二者必居其一,**不得两端都写死**(当前"Leve|l 1"、胶囊裁切即两端写死所致)。

### 8.3 主题(与几何正交)

颜色全部走 CSS 变量,主题 = 一组变量值,注入不改任何几何:

```svg
<defs><style>
:root{ --text-primary:#10253f; --flow-1:#1f78b4; --flow-2:#3f8f5f;
       --icon:#1f78b4; --frame:#9bb7d4; --bg-region:#f4f8fc; }
</style></defs>
```

---

## 9. 几何校验门禁(让"成功"诚实)

排版后用 `MeasureEngine` 计算每个元素 bbox(**无需先栅格化**),逐条判定。任一违规都不得报 `fit_score 1.0`,而是交决策层走 改写 → 变体 → 降级,并写入 manifest。

### 9.1 元素 bbox

```python
def text_bbox(slot, layout, m):
    widest = max(m.width(l, layout.size, slot.weight) for l in layout.lines)
    lh = layout.size * slot.line_height
    total_h = len(layout.lines) * lh
    top = slot.y + (slot.h - total_h)/2
    x = {"left":slot.x, "center":slot.x+(slot.w-widest)/2,
         "right":slot.x+slot.w-widest}[slot.align]
    return Rect(x, top, widest, total_h)
```

### 9.2 检查项与判据

| 检查 | 判据 | 容差 |
| --- | --- | --- |
| 超框 | `text_bbox ⊄ slot_rect` | 1px |
| 行数 | `len(lines) > max_lines` | — |
| 重叠 | 非父子元素 `bbox` 相交面积 > 阈值 | 1px |
| 锚点 | `dist(连线端点, 锚点) > gap+ε` | 2px |
| 对比度 | 文字色 vs 所在背景色 WCAG 比 < 4.5(大字 3.0) | — |

```python
def intersects(a, b, eps=1.0):
    return not (a.x+a.w <= b.x+eps or b.x+b.w <= a.x+eps or
                a.y+a.h <= b.y+eps or b.y+b.h <= a.y+eps)

def contrast_ratio(fg_rgb, bg_rgb):
    def lin(c): c/=255; return c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    def L(rgb): r,g,b=map(lin,rgb); return 0.2126*r+0.7152*g+0.0722*b
    l1,l2=sorted([L(fg_rgb),L(bg_rgb)],reverse=True)
    return (l1+0.05)/(l2+0.05)
```

> 注:图 6-1 的重复副标题会在此被两个近乎相同的 bbox 判为"重叠违规"而拦下。

### 9.3 栅格化兜底(可选)

几何校验通过后,可选地栅格化 + 像素扫描(检测意外裁切/字体回退),作为最后一道防线。日常以几何校验为准(无需渲染、更快)。

---

## 10. 关键数据结构

```python
@dataclass
class Rect: x:float; y:float; w:float; h:float

@dataclass
class TextSlot:
    id:str; x:float; y:float; w:float; h:float
    align:str="left"; weight:int=400
    font_max:int=16; font_min:int=12; font_step:int=1
    line_height:float=1.3; max_lines:int|None=None
    color_var:str="text-primary"; overflow_policy:str="shrink_then_rewrite"

@dataclass
class IconSlot: id:str; x:float; y:float; size:float; allowed:list[str]

@dataclass
class Connector:
    frm:str; to:str; style:str="solid"; color_var:str="flow-1"
    route:str="auto"; label:dict|None=None

@dataclass
class Layout: lines:list[str]|None; size:int; ok:bool

@dataclass
class ValidationIssue: kind:str; element:str; detail:str   # overflow/overlap/anchor/contrast

@dataclass
class RenderResult:
    svg:str; issues:list[ValidationIssue]
    fit_score:float; needs_human_review:bool
```

`fit_score` 由违规数与严重度反推(零违规=1.0;有违规<1.0 并触发降级),**不再恒为 1.0**。

---

## 11. 端到端渲染流程(伪代码)

```python
def render_template_svg(template, fill, m, theme) -> RenderResult:
    issues, layouts = [], {}
    # 1. 文本槽:测量→换行→缩放
    for slot in template.text_slots:
        lay = fit(slot, fill.text[slot.id], m)
        if not lay.ok:
            rewritten = constrained_rewrite(slot, fill.text[slot.id], m)   # 有界重试
            lay = fit(slot, rewritten, m) if rewritten else lay
        if not lay.ok:
            return degrade(template, fill, reason=f"{slot.id} overflow")   # 变体/降级
        layouts[slot.id] = lay
    # 2. 几何校验
    boxes = collect_bboxes(template, layouts, fill, m)
    issues += check_overflow(template, layouts, m)
    issues += check_overlap(boxes)
    issues += check_anchors(template, fill)
    issues += check_contrast(template, fill, theme)
    if issues:
        return degrade(template, fill, issues=issues)
    # 3. 生成
    svg = assemble_svg(template, layouts, fill, theme, embed_font=True)
    return RenderResult(svg, [], fit_score=1.0, needs_human_review=False)
```

---

## 12. 实现要点与坑

- **三处同源**:测量字体、内嵌字体、渲染字体必须同一文件;任何一处不一致,稳定性即失效。
- **基线 vs 居中**:`<text>` 的 `y` 是基线;垂直居中需用 `ascent` 换算(见 5.4),不要用 `dominant-baseline` 凑近似,跨渲染器表现不一。
- **CJK 无空格**:换行须按字符可断,拉丁词内不可断;混排分段处理。
- **woff2 体积**:务必子集化;全文用字集合通常使单字重内嵌降到几十 KB,5 张图可共享同一子集集合。
- **数值精度**:坐标保留 1 位小数即可,避免长浮点污染体积与 diff。
- **决定性**:同一输入 + 同一字体 → 同一输出,便于黄金回归快照。

---

## 13. 验收标准

- 同一批真实投标内容渲染:**零文字超框、零非预期重叠、零裁切**。
- 在**无系统字体**的干净环境渲染,结果与作者环境一致(内嵌字体生效)。
- 任一槽位装不下时,能自动走改写或降级,且 `fit_score < 1.0`、`needs_human_review` 正确置位;**不再出现破图却报 1.0**。
- 同一张图切换 3 套主题,几何不变。
- 每模板黄金回归快照稳定。

---

## 14. 附:最小参考实现骨架

落地顺序建议:先实现 `MeasureEngine` + `tokenize/wrap/fit/emit_text`(消灭本次约 80% 缺陷),再补字体内嵌与几何校验,最后接改写/降级。上文 4.3 / 5.2 / 5.3 / 5.4 / 9.1 / 9.2 / 11 的代码可直接作为 `core/text_measure.py`、`renderers/svg_v2.py`、`core/validator.py` 的起点。
