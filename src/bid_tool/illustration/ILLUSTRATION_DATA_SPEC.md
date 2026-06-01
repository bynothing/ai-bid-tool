# 插图数据规范 — AI 生成高质量投标配图指南

本文档定义了生成精美 SVG/HTML 投标插图所需的完整数据格式。AI 在生成插图数据时应遵循此规范，以确保渲染器能产出专业品质的图形。

## 通用要求

每条插图的数据对象均需包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 图表标题，应精确描述图表内容 |
| `subtitle` | string | ✅ | 副标题，补充说明图表用途或范围 |
| `note` | string | | 底部注释，说明数据来源、假设或限制 |
| `requirements` | array | | 底部合规/要求条，每项含 `title` + `desc` |
| `safeguards` | array | | 底部保障措施，同 requirements 格式 |

### 颜色语义

所有 `style` 字段取值及含义：

| style | 颜色 | 语义 | 适用场景 |
|-------|------|------|---------|
| `default` | 蓝色 | 通用/常态 | 默认项 |
| `accent` | 深蓝 | 重点强调 | 核心组件、关键流程、重点模块 |
| `success` | 绿色 | 成功/达标 | 完成节点、达标指标、验收环节 |
| `warning` | 琥珀 | 注意/风险 | 判断分支、风险项、待确认项 |
| `danger` | 红色 | 危险/紧急 | 故障、告警、紧急处置 |
| `purple` | 紫色 | 外部/协同 | 第三方接口、外部系统 |
| `cyan` | 青色 | 数据/分析 | 数据层、分析引擎 |
| `teal` | 蓝绿 | 辅助/支撑 | 缓存、队列、中间件 |
| `gold` | 金色 | 同步/反馈 | 回执、确认、审计 |

### 可用图标

每个 `icon` 字段可从以下列表选择（共 40+ 个）：

```
server    数据库/服务    cloud      云/网络      shield     安全/防护
lock      锁定/加密      key        密钥/权限    user       用户/人员
users     用户组         admin      管理员       monitor    监控/大屏
settings  设置/配置      code       代码/开发    database   数据库
file      文件/文档      folder     文件夹       search     搜索/查询
chart     图表/统计      calendar   日历/计划    bell       通知/告警
alert_triangle  警告     check      通过/完成    form       表单/工单
report    报告/报表      dashboard  仪表盘       gps        定位/导航
camera    摄像头/监控    sensor     传感器       wifi       无线/网络
radio     物联网/信号    smartphone 移动端       link       连接/对接
map_pin   地图/位置      truck      车辆/运输    zap        闪电/实时
cpu       处理器/算力    hard_drive 存储         video      视频/影像
trending_up 增长        activity   活动/流程    grid       网格/矩阵
briefcase 业务/办公     send       发送/推送    download   下载/接收
refresh_cw 刷新/同步    clipboard  剪贴板       bookmark   书签
trash_2   删除/废弃     target     目标/指标    wind       通风/气流
droplet   水滴/液体     thermometer 温度        shield_off 防火墙
```

---

## 图型详细规范

### 1. `architecture.layered` — 分层架构图

**用途**: 系统总体架构、技术架构、能力分层。展示从用户到基础设施的完整层次结构。

**完整 Schema**:

```json
{
  "title": "智能城市运营中心总体架构图",
  "subtitle": "端·边·云·数·智·用 六层协同体系",
  "note": "红色虚线框为建设重点；本架构满足等保三级要求",
  "actors": [
    {"title": "城市管理者",  "desc": "市长驾驶舱 · 区县分舱",         "icon": "users"},
    {"title": "委办局用户",  "desc": "公安 · 交通 · 城管 · 应急",     "icon": "briefcase"},
    {"title": "公众市民",    "desc": "随手拍 · 12345热线 · APP",     "icon": "smartphone"},
    {"title": "上级平台",    "desc": "省级城市运管服平台数据对接",      "icon": "link"}
  ],
  "layers": [
    {
      "label": "应用层 · 城市治理场景",
      "en": "APPLICATION LAYER",
      "style": "dark",
      "columns": 5,
      "items": [
        {"title": "城市运行监测",  "desc": "交通·环境·能源实时态势",          "icon": "activity",    "style": "accent"},
        {"title": "应急指挥调度",  "desc": "预案管理·资源调度·一键联动",        "icon": "alert_triangle","style": "danger"},
        {"title": "社会治理协同",  "desc": "网格管理·事件流转·闭环考评",        "icon": "grid",        "style": "accent"},
        {"title": "产业经济分析",  "desc": "企业画像·产业链图谱·招商推荐",       "icon": "trending_up"},
        {"title": "公众服务门户",  "desc": "政务服务·便民查询·互动反馈",        "icon": "smartphone"}
      ]
    },
    {
      "label": "数字平台层 · 能力中台",
      "en": "PLATFORM LAYER",
      "columns": 4,
      "items": [
        {"title": "IoT 物联网平台", "desc": "设备管理·协议适配·百万级并发",      "icon": "radio"},
        {"title": "视频AI分析平台", "desc": "人脸·车辆·行为·烟火检测",          "icon": "video"},
        {"title": "地理信息服务",   "desc": "二维/三维GIS·空间分析·路径规划",    "icon": "map_pin"},
        {"title": "大数据计算平台", "desc": "实时流计算·离线批处理·数据治理",     "icon": "database",   "style": "success"},
        {"title": "人工智能平台",   "desc": "模型训练·推理服务·算法市场",        "icon": "cpu",        "style": "success"},
        {"title": "区块链存证平台", "desc": "数据确权·溯源审计·智能合约",        "icon": "lock"},
        {"title": "低代码开发平台", "desc": "表单设计·流程编排·大屏搭建",        "icon": "code"},
        {"title": "统一身份认证",   "desc": "SSO·权限管理·操作审计",           "icon": "shield"}
      ]
    },
    {
      "label": "数据资源层 · 城市大脑",
      "en": "DATA LAYER",
      "style": "dark",
      "items": [
        {"title": "城市基础库",   "desc": "人口·法人·地理·宏观经济",   "icon": "database", "style": "accent"},
        {"title": "主题专题库",   "desc": "交通·环境·安全·民生",      "icon": "folder"},
        {"title": "实时数据流",   "desc": "Kafka·Flink·百万条/秒",  "icon": "zap"},
        {"title": "数据湖存储",   "desc": "HDFS·MinIO·百PB级",      "icon": "hard_drive"},
        {"title": "数据治理中心", "desc": "质量·标准·目录·血缘",      "icon": "settings"}
      ]
    },
    {
      "label": "云基础设施层 · 多云纳管",
      "en": "INFRASTRUCTURE LAYER",
      "columns": 3,
      "items": [
        {"title": "政务云（主中心）","desc": "鲲鹏/昇腾 · 信创适配",    "icon": "server",   "style": "success"},
        {"title": "公有云（弹性）",  "desc": "峰值扩容 · 灾备切换",     "icon": "cloud"},
        {"title": "边缘计算节点",    "desc": "区县下沉 · 低延迟处理",   "icon": "cpu"},
        {"title": "5G 专网",        "desc": "高带宽 · 低时延 · 大连接", "icon": "wifi"},
        {"title": "网络安全防护",    "desc": "WAF·防火墙·零信任",      "icon": "shield_off","style": "warning"},
        {"title": "灾备中心",        "desc": "异地备份 RPO<1min RTO<15min","icon":"refresh_cw","style":"warning"}
      ]
    },
    {
      "label": "感知层 · 城市神经元",
      "en": "SENSING LAYER",
      "columns": 5,
      "items": [
        {"title": "视频监控",    "desc": "5万路 · AI解析",        "icon": "camera"},
        {"title": "环境监测",    "desc": "空气·水质·噪声",        "icon": "thermometer"},
        {"title": "交通感知",    "desc": "地磁·雷达·电子警察",     "icon": "truck"},
        {"title": "物联终端",    "desc": "井盖·路灯·垃圾桶·消防栓", "icon": "radio"},
        {"title": "无人机巡检",  "desc": "违法建筑·河道巡查",       "icon": "send"}
      ]
    }
  ],
  "integrations": [
    {"title": "省级城市运管服平台", "desc": "数据上报 · 指令接收"},
    {"title": "公安人口库",       "desc": "身份核验 · 重点人员"},
    {"title": "交通委信号系统",    "desc": "信号灯控制 · 态势感知"},
    {"title": "气象局预报接口",    "desc": "极端天气预警 · 小时级更新"}
  ],
  "requirements": [
    {"title": "等保三级",        "desc": "安全计算环境+安全通信网络"},
    {"title": "密码应用安全性评估","desc": "国密算法SM2/SM3/SM4"},
    {"title": "数据安全法合规",   "desc": "分级分类·脱敏·审计"},
    {"title": "可用性 ≥ 99.99%",  "desc": "双活数据中心·自动切换"},
    {"title": "接口响应 ≤ 200ms", "desc": "P95延迟·全链路监控"},
    {"title": "信创适配",        "desc": "鲲鹏CPU·麒麟OS·达梦DB"}
  ]
}
```

**字段说明**:

| 字段 | 层级 | 说明 |
|------|------|------|
| `actors` | 顶层 | 服务对象行，建议 2-5 个 |
| `actors[].title/desc/icon` | 每个 actor | 名称/描述/图标 |
| `layers` | 顶层 | 核心分层，建议 3-7 层 |
| `layers[].label` | 每层 | 中文层名，建议含编号或类别 |
| `layers[].en` | 每层 | 英文层名 |
| `layers[].style` | 每层 | `"dark"` 则深色标题栏，否则浅色 |
| `layers[].columns` | 每层 | 最多容纳列数，默认自动 |
| `layers[].items` | 每层 | 卡片数组，建议 3-8 个 |
| `items[].title` | 每个 | 卡片标题，**必填** |
| `items[].desc` | 每个 | 卡片描述，强烈建议填写以丰富画面 |
| `items[].icon` | 每个 | 语义图标，强烈建议填写 |
| `items[].style` | 每个 | 语义颜色，核心项用 `accent`，关键项用 `success` |
| `integrations` | 顶层 | 右侧外部系统对接列表 |
| `requirements` | 顶层 | 底部合规要求（最多6个） |

---

### 2. `process.flowchart` — 流程图

**用途**: 业务流程、施工工序、审批流转、运维处置流程。

**完整 Schema**:

```json
{
  "title": "隐蔽工程验收流程图",
  "subtitle": "从施工单位自检到发包人最终验收的完整闭环",
  "note": "关键控制节点用红色标注，虚线为可选路径",
  "nodes": [
    {
      "id": "n01",
      "row": 0,
      "col": 0,
      "title": "施工单位自检",
      "desc": "按设计图纸和规范完成自检\n填写隐蔽工程验收记录表",
      "icon": "clipboard",
      "kind": "process",
      "style": "accent"
    },
    {
      "id": "n02",
      "row": 0,
      "col": 1,
      "title": "监理单位初验",
      "desc": "现场核查施工质量\n签署初验意见",
      "icon": "search",
      "kind": "decision"
    },
    {
      "id": "n03",
      "row": 0,
      "col": 2,
      "title": "不合格整改",
      "desc": "限期整改并重新报验",
      "icon": "refresh_cw",
      "kind": "process",
      "style": "warning"
    },
    {
      "id": "n04",
      "row": 1,
      "col": 1,
      "title": "发包人终验",
      "desc": "组织监理·施工·设计联合验收\n签署隐蔽工程验收合格证",
      "icon": "users",
      "kind": "process",
      "style": "success"
    },
    {
      "id": "n05",
      "row": 1,
      "col": 2,
      "title": "归档备案",
      "desc": "验收资料归档\n录入质量管理信息系统",
      "icon": "folder",
      "kind": "success",
      "style": "success"
    }
  ],
  "edges": [
    {"from": "n01", "to": "n02", "label": "提交报验", "relation": "flow"},
    {"from": "n02", "to": "n03", "label": "不合格",    "relation": "alert"},
    {"from": "n02", "to": "n04", "label": "合格",      "relation": "flow"},
    {"from": "n03", "to": "n02", "label": "整改完成",  "relation": "sync"},
    {"from": "n04", "to": "n05", "label": "通过",      "relation": "flow"}
  ],
  "requirements": [
    {"title": "验收合格率 100%", "desc": ""},
    {"title": "整改闭环率 100%", "desc": ""},
    {"title": "资料归档完整",   "desc": ""}
  ]
}
```

**字段说明**:

| 字段 | 说明 |
|------|------|
| `nodes[].id` | **必填**，唯一标识，格式 `n01`, `n02`... |
| `nodes[].row` | 行号（从0开始），同一行节点水平排列 |
| `nodes[].col` | 列号（从0开始） |
| `nodes[].kind` | `process`(普通) / `decision`(判断·菱形) / `success`(完成) / `failure`(失败) / `external`(外部) |
| `nodes[].desc` | 描述文本，支持换行 `\n` |
| `nodes[].icon` | 图标标识 |
| `nodes[].style` | 语义颜色（覆盖 kind 的默认颜色） |
| `edges[].relation` | `flow`(实线蓝) / `data`(虚线青) / `control`(虚线紫) / `alert`(粗线红) / `sync`(虚线金) |

> **简化写法**: 如果流程是线性的，可以用 `flows` 代替 `nodes`+`edges`，引擎会自动生成节点和顺序连线：
> ```json
> "flows": [
>   {"title": "步骤1", "desc": "...", "icon": "...", "style": "accent"},
>   {"title": "步骤2", "desc": "...", "kind": "decision"}
> ]
> ```

---

### 3. `capability.map` — 能力地图

**用途**: 功能模块分组、服务能力展示、响应能力矩阵。

```json
{
  "title": "项目管理能力矩阵",
  "subtitle": "五大管理领域 · 二十项核心能力",
  "columns": 3,
  "groups": [
    {
      "label": "进度管理",
      "icon": "calendar",
      "style": "accent",
      "items": [
        {"title": "WBS 工作分解",   "desc": "四级分解·责任到人"},
        {"title": "关键路径分析",   "desc": "CPM·动态调整·预警"},
        {"title": "里程碑管控",     "desc": "三级节点·月度考核"},
        {"title": "资源平衡",       "desc": "人机料法环·动态调配"}
      ]
    },
    {
      "label": "质量管理",
      "icon": "shield",
      "style": "success",
      "items": [
        {"title": "三检制度",       "desc": "自检·互检·专检"},
        {"title": "材料进场验收",   "desc": "五步验收·见证取样"},
        {"title": "BIM 协同",       "desc": "碰撞检查·虚拟建造"},
        {"title": "质量追溯",       "desc": "二维码·区块链存证"}
      ]
    },
    {
      "label": "安全管理",
      "icon": "alert_triangle",
      "style": "danger",
      "items": [
        {"title": "危险源辨识",     "desc": "LEC法·动态更新"},
        {"title": "特种作业管控",   "desc": "7类许可·持证上岗"},
        {"title": "应急管理",       "desc": "1+4预案体系·季度演练"},
        {"title": "HSE考核",        "desc": "日巡查·周例会·月考评"}
      ]
    },
    {
      "label": "成本管理",
      "icon": "chart",
      "style": "gold",
      "items": [
        {"title": "预算编制",       "desc": "清单计价·市场询价"},
        {"title": "过程管控",       "desc": "挣值分析·偏差预警"},
        {"title": "变更管理",       "desc": "分级审批·签证留痕"}
      ]
    },
    {
      "label": "合同管理",
      "icon": "file",
      "style": "purple",
      "items": [
        {"title": "招标采购",       "desc": "公开招标·电子评标"},
        {"title": "履约管理",       "desc": "进度款·质保金"},
        {"title": "索赔管理",       "desc": "证据链·时限管控"}
      ]
    }
  ],
  "requirements": [
    {"title": "ISO 9001:2015 认证"},
    {"title": "GB/T 50430 规范"},
    {"title": "PMBOK 方法论"}
  ]
}
```

**字段说明**:

| 字段 | 说明 |
|------|------|
| `groups` | 能力分组，建议 3-6 个 |
| `groups[].icon` | 分组图标 |
| `groups[].style` | 分组颜色语义 |
| `groups[].items[].title` | 能力项名称 |
| `groups[].items[].desc` | 能力项描述（建议10-30字） |
| `columns` | 网格列数，默认3 |

---

### 4. `process.swimlane` — 泳道流程图

**用途**: 多角色、多部门、多系统协同流程。

```json
{
  "title": "设计变更管理流程",
  "subtitle": "施工单位发起 → 监理审核 → 设计确认 → 发包人审批",
  "lanes": [
    {"id": "L1", "title": "施工单位",    "icon": "truck",   "style": "default"},
    {"id": "L2", "title": "监理单位",    "icon": "search",  "style": "accent"},
    {"id": "L3", "title": "设计单位",    "icon": "code",    "style": "purple"},
    {"id": "L4", "title": "发包人/业主", "icon": "briefcase","style": "success"}
  ],
  "steps": [
    {"id": "S01", "lane": "L1", "order": 0, "title": "提出变更申请",  "desc": "填写变更申请单\n附变更依据和费用估算", "icon": "form"},
    {"id": "S02", "lane": "L2", "order": 1, "title": "监理审核",     "desc": "审核变更必要性\n评估对质量/安全/工期影响", "icon": "search", "style": "warning"},
    {"id": "S03", "lane": "L3", "order": 2, "title": "设计确认方案",  "desc": "出具设计变更方案\n计算工程量变化", "icon": "settings"},
    {"id": "S04", "lane": "L4", "order": 3, "title": "发包人审批",    "desc": "审批变更申请\n签署变更令", "icon": "check", "style": "success"},
    {"id": "S05", "lane": "L1", "order": 4, "title": "实施变更",     "desc": "按变更令执行\n更新施工日志", "icon": "clipboard"},
    {"id": "S06", "lane": "L2", "order": 5, "title": "变更验收",     "desc": "核实变更完成情况\n签署验收意见", "icon": "shield", "style": "success"}
  ],
  "edges": [
    {"from": "S01", "to": "S02", "label": "提交"},
    {"from": "S02", "to": "S03", "label": "通过"},
    {"from": "S03", "to": "S04", "label": "报送"},
    {"from": "S04", "to": "S05", "label": "批准"},
    {"from": "S05", "to": "S06", "label": "完成"}
  ]
}
```

---

### 5. `interaction.sequence` — 时序图

**用途**: 接口调用、消息传递、事件交互的时序表达。

```json
{
  "title": "第三方支付对接时序图",
  "subtitle": "用户端 → 业务系统 → 支付网关 → 银行核心",
  "participants": [
    {"id": "P1", "title": "移动端APP",    "desc": "用户操作入口", "icon": "smartphone"},
    {"id": "P2", "title": "业务系统",     "desc": "订单处理中心", "icon": "server",    "style": "accent"},
    {"id": "P3", "title": "支付网关",     "desc": "路由与风控",   "icon": "shield",    "style": "warning"},
    {"id": "P4", "title": "银行核心系统",  "desc": "账务处理",     "icon": "database",  "style": "success"}
  ],
  "messages": [
    {"from": "P1", "to": "P2", "label": "1. 提交支付请求",          "relation": "flow"},
    {"from": "P2", "to": "P3", "label": "2. 转发支付（签名+加密）",  "relation": "data"},
    {"from": "P3", "to": "P4", "label": "3. 扣款请求",              "relation": "control"},
    {"from": "P4", "to": "P3", "label": "4. 扣款结果回执",          "relation": "sync"},
    {"from": "P3", "to": "P2", "label": "5. 支付结果通知",          "relation": "sync"},
    {"from": "P2", "to": "P1", "label": "6. 展示支付结果",          "relation": "flow"}
  ]
}
```

---

### 6. `relationship.domain` — 关系图

**用途**: 系统间关系、组件依赖、实体关系、数据表关联。

```json
{
  "title": "智慧工地系统集成关系图",
  "subtitle": "五大子系统数据流与协同关系",
  "columns": 3,
  "containers": [
    {
      "id": "C01",
      "title": "人员管理系统",
      "icon": "users",
      "style": "accent",
      "row": 0, "col": 0,
      "nodes": [
        {"id": "n11", "title": "实名制考勤",  "desc": "人脸识别·闸机通行"},
        {"id": "n12", "title": "特种人员管理", "desc": "证书核验·到期预警"},
        {"id": "n13", "title": "安全教育培训", "desc": "三级教育·在线考核"}
      ]
    },
    {
      "id": "C02",
      "title": "设备监控系统",
      "icon": "cpu",
      "style": "teal",
      "row": 0, "col": 1,
      "nodes": [
        {"id": "n21", "title": "塔吊监测",   "desc": "力矩·高度·回转"},
        {"id": "n22", "title": "升降机监测", "desc": "载重·速度·门锁"},
        {"id": "n23", "title": "环境监测",   "desc": "PM2.5·噪声·风速"}
      ]
    },
    {
      "id": "C03",
      "title": "视频AI系统",
      "icon": "camera",
      "style": "purple",
      "row": 1, "col": 0,
      "nodes": [
        {"id": "n31", "title": "安全帽检测",  "desc": "未佩戴实时告警"},
        {"id": "n32", "title": "烟火检测",    "desc": "明火·烟雾·温度异常"},
        {"id": "n33", "title": "入侵检测",    "desc": "电子围栏·越界告警"}
      ]
    },
    {
      "id": "C04",
      "title": "质量管理系统",
      "icon": "shield",
      "style": "success",
      "row": 1, "col": 1,
      "nodes": [
        {"id": "n41", "title": "材料追溯",   "desc": "进场验收·见证取样"},
        {"id": "n42", "title": "工序验收",   "desc": "APP填报·拍照留痕"},
        {"id": "n43", "title": "BIM协同",    "desc": "模型对比·进度模拟"}
      ]
    },
    {
      "id": "C05",
      "title": "综合管理平台",
      "icon": "dashboard",
      "style": "gold",
      "row": 2, "col": 0,
      "nodes": [
        {"id": "n51", "title": "指挥大屏",   "desc": "数据汇聚·态势展示"},
        {"id": "n52", "title": "预警中心",   "desc": "规则引擎·分级推送"},
        {"id": "n53", "title": "报表中心",   "desc": "日报·周报·月报自动生成"}
      ]
    }
  ],
  "edges": [
    {"from": "n13", "to": "n11", "relation": "data", "label": "考核结果"},
    {"from": "n21", "to": "n51", "relation": "data", "label": "运行数据"},
    {"from": "n31", "to": "n51", "relation": "data", "label": "告警事件"},
    {"from": "n41", "to": "n51", "relation": "data", "label": "质量数据"},
    {"from": "n51", "to": "n52", "relation": "flow", "label": "告警下发"},
    {"from": "n32", "to": "n51", "relation": "alert", "label": "火灾告警"}
  ]
}
```

**字段说明**:

| 字段 | 说明 |
|------|------|
| `containers` | 域/分组，建议 3-8 个 |
| `containers[].id` | 容器唯一ID，`C01` 格式 |
| `containers[].row/col` | 网格行列位置 |
| `containers[].nodes` | 容器内节点数组 |
| `nodes[].id` | 节点唯一ID，`nXX` 格式 |
| `edges` | 跨容器关系连线 |
| `edges[].relation` | `flow`/`data`/`control`/`alert`/`sync` |

---

### 7. `integration.interface_map` — 接口关系与数据交互图

**用途**: 双平台/多平台之间的数据推送、回执、安全校验和异常补传机制。

```json
{
  "title": "数据交互规则适配架构与接口关系",
  "subtitle": "业务系统、监管平台与数据链路的接口关系",
  "leftPlatform": {
    "title": "承建单位业务平台",
    "subtitle": "采集、治理、推送",
    "icon": "server",
    "layers": [
      {"title": "业务应用层", "items": ["项目管理", "巡检填报", "问题闭环", "统计分析"]},
      {"title": "数据服务层", "items": ["数据清洗", "规则校验", "接口封装", "消息队列"]},
      {"title": "安全支撑层", "items": ["身份认证", "签名验签", "日志审计", "异常告警"]},
      {"title": "基础资源层", "items": ["数据库", "应用服务", "备份恢复", "网络接入"]}
    ]
  },
  "rightPlatform": {
    "title": "监管/业主集成平台",
    "subtitle": "接收、核验、反馈",
    "icon": "government",
    "layers": [
      {"title": "接口接入区", "items": ["HTTPS API", "批量文件", "消息回执", "状态查询"]},
      {"title": "数据核验区", "items": ["字段完整性", "规则一致性", "重复校验", "时效校验"]},
      {"title": "监管应用区", "items": ["综合看板", "问题督办", "报表归档", "趋势研判"]},
      {"title": "安全审计区", "items": ["访问审计", "脱敏留痕", "权限管控", "风险告警"]}
    ]
  },
  "flows": [
    {"title": "基础数据同步",   "protocol": "HTTPS + JSON / 每日增量",     "style": "default", "ackLabel": "接收回执"},
    {"title": "巡检结果上报",   "protocol": "API实时推送 / 批量补传",      "style": "accent",  "ackLabel": "校验结果反馈"},
    {"title": "问题工单回传",   "protocol": "状态变更事件 / 闭环节点",      "style": "warning", "ackLabel": "处理状态确认"},
    {"title": "审计日志归档",   "protocol": "签名文件 + 摘要校验",         "style": "success", "ackLabel": "归档编号反馈"}
  ],
  "requirements": [
    {"title": "统一身份认证",   "style": "default"},
    {"title": "字段规则校验",   "style": "accent"},
    {"title": "失败重试补传",   "style": "warning"},
    {"title": "全链路审计",     "style": "success"}
  ],
  "notes": [
    {"title": "数据标准", "icon": "form",   "style": "default", "items": ["统一编码", "字段字典", "版本兼容"]},
    {"title": "安全策略", "icon": "shield", "style": "success", "items": ["传输加密", "签名验签", "最小权限"]},
    {"title": "异常处理", "icon": "alert",  "style": "warning", "items": ["失败重试", "人工复核", "日志追踪"]}
  ],
  "note": "接口关系图需要同时体现方向、协议、回执、安全约束与异常补传机制。"
}
```

---

### 8. `operation.inspection_taxonomy` — 巡检分类图

```json
{
  "title": "日常运维巡检体系分类",
  "subtitle": "例行巡检、专项巡检和异常触发巡检的触发方式与输出",
  "summary": "通过分类巡检机制，保障系统稳定运行、数据质量达标、接口畅通、终端在线可用。",
  "categories": [
    {
      "index": 1,
      "title": "季度例行巡检",
      "subtitle": "底线要求",
      "style": "success",
      "icon": "calendar",
      "trigger": "按季度计划执行\n每季度不少于1次",
      "content": ["系统访问与页面使用检查", "数据接收、解析、入库与展示检查", "接口上报、返回结果与联通性检查", "终端在线状态与心跳检测"],
      "checks": ["数据上传率 ≥ 90%", "接口成功率、延迟、错误码统计", "异常、离线、延迟数据清单核查"],
      "output": "《季度巡检报告》+ 问题清单与整改建议"
    },
    {
      "index": 2,
      "title": "专项巡检",
      "subtitle": "接口/数据/终端状态",
      "style": "default",
      "icon": "settings",
      "trigger": "按专题计划执行\n或阶段性重点工作需要",
      "content": ["接口专项巡检", "数据质量专项巡检", "终端状态专项巡检", "历史数据一致性核查"],
      "checks": ["专题指标达标情况", "字段映射、格式、签名符合性", "异常原因分析与影响范围评估"],
      "output": "《专项巡检报告》+ 问题分析与整改方案"
    },
    {
      "index": 3,
      "title": "异常触发巡检",
      "subtitle": "快速响应",
      "style": "warning",
      "icon": "bell",
      "trigger": "由监控告警、异常事件\n或监管通报触发",
      "content": ["针对告警定向巡检", "数据链路追踪", "接口·终端·网络联动检查", "异常影响评估与应急处置"],
      "checks": ["异常现象复现与定位", "根因分析与影响范围", "处置措施有效性验证"],
      "output": "《异常巡检报告》+ 处置记录与整改建议"
    }
  ],
  "outputs": ["巡检计划与执行记录", "问题清单与整改闭环", "数据与指标趋势分析", "巡检报告归档与可追溯"],
  "note": "发现-处理-验证-归档-改进的持续优化闭环。"
}
```

---

### 9. `operation.incident_response` — 故障分级响应与闭环图

```json
{
  "title": "故障分级响应与问题闭环流程",
  "subtitle": "分级标准、响应时限、处置时限与持续改进",
  "headers": ["级别", "故障定义", "典型场景示例", "响应时限", "处理时限", "服务方式", "升级条件"],
  "levels": [
    {
      "level": "一级", "name": "较重大问题",
      "style": "danger", "icon": "alert",
      "definition": "导致监管业务中断或大量数据中断，存在较高安全风险",
      "scenes": ["平台完全不可访问", "大量终端数据中断", "上级平台上报中断"],
      "response": "2小时内响应", "handling": "4小时内恢复或提供临时方案",
      "service": "7x24小时现场/远程协同处理", "upgrade": "影响范围扩大或超时未恢复"
    },
    {
      "level": "二级", "name": "一般异常",
      "style": "warning", "icon": "bell",
      "definition": "部分功能异常或数据异常，未造成监管业务中断",
      "scenes": ["部分模块异常", "终端数据延迟", "接口返回异常"],
      "response": "1个工作日内响应", "handling": "2个工作日内处理完成",
      "service": "工作时间内远程支持为主", "upgrade": "问题升级为一级故障"
    },
    {
      "level": "三级", "name": "普通事项",
      "style": "success", "icon": "check",
      "definition": "咨询、优化建议或轻微问题，不影响系统正常运行",
      "scenes": ["操作咨询", "界面显示优化建议", "日志查询、数据核对"],
      "response": "2个工作日内响应", "handling": "5个工作日内处理完成",
      "service": "远程支持工单处理", "upgrade": "问题演变为二级或一级"
    }
  ],
  "steps": [
    {"title": "问题发现", "icon": "search",    "desc": "通过监控告警、巡检发现、用户反馈等渠道发现问题", "output": "问题初步信息"},
    {"title": "问题登记", "icon": "form",      "desc": "登记问题信息，明确现象、影响范围、发生时间等",   "output": "问题工单"},
    {"title": "分类定位", "icon": "gps",       "desc": "按故障分级标准分类，进行初步分析定位",            "output": "问题分类结果"},
    {"title": "处理解决", "icon": "settings",  "desc": "制定处理方案并实施解决，必要时协调升级处理",      "output": "处理记录", "style": "accent"},
    {"title": "复核验证", "icon": "shield",    "desc": "复核验证问题是否解决，功能及数据恢复是否正常",    "output": "验证结果"},
    {"title": "关闭归档", "icon": "file",      "desc": "问题关闭，归档工单、处理记录、日志等资料",        "output": "归档记录"},
    {"title": "总结改进", "icon": "dashboard", "desc": "定期汇总分析，形成问题报告并优化流程",            "output": "改进建议"}
  ],
  "safeguards": [
    {"title": "专人负责", "desc": "明确责任人与联络人", "icon": "user"},
    {"title": "全程跟踪", "desc": "工单状态实时跟踪",   "icon": "calendar"},
    {"title": "留痕可追溯","desc": "全过程记录可追溯",   "icon": "audit"},
    {"title": "合规可审计","desc": "满足监管审计要求",  "icon": "shield"},
    {"title": "数据驱动",  "desc": "用数据驱动持续改进", "icon": "chart"}
  ]
}
```

---

### 10. `architecture.security_ring` — 安全体系环形图

```json
{
  "title": "数据安全保密保障体系架构",
  "subtitle": "五大核心措施 · 多层协同防护 · 全流程闭环管理",
  "core": {
    "title": "数据安全保密\n保障体系",
    "desc": "合规为基 · 技术为盾 · 管理为纲 · 闭环可控",
    "icon": "lock"
  },
  "measures": [
    {
      "index": 1, "title": "账号权限与访问控制",
      "style": "default",
      "items": ["统一身份认证（SSO）", "角色分级授权", "多因素认证（MFA）", "敏感操作二次校验"]
    },
    {
      "index": 2, "title": "数据导出与使用控制",
      "style": "success",
      "items": ["数据导出分级审批", "敏感数据脱敏处理", "单次/批量导出限制", "水印标识与追溯"]
    },
    {
      "index": 3, "title": "接口认证与传输安全",
      "style": "warning",
      "items": ["JWT/HMAC接口认证", "TLS 1.2+传输加密", "数字签名与防重放", "IP白名单与访问控制"]
    },
    {
      "index": 4, "title": "日志审计与行为追溯",
      "style": "purple",
      "items": ["操作日志全量记录", "登录/操作/导出审计", "日志防篡改与留存", "异常行为实时告警"]
    },
    {
      "index": 5, "title": "监管数据防外泄",
      "style": "cyan",
      "items": ["数据分级分类管理", "敏感数据加密存储", "外发数据严格管控", "屏幕水印与打印控制"]
    }
  ],
  "loop": [
    {"title": "制度规范", "icon": "contract"},
    {"title": "技术防护", "icon": "settings"},
    {"title": "监测审计", "icon": "monitor"},
    {"title": "风险处置", "icon": "shield"},
    {"title": "评估优化", "icon": "report"}
  ]
}
```

---

## AI 生成检查清单

生成插图数据后，请逐项确认：

- [ ] 每条 `items` 中的对象都包含 `title`（必填）和 `desc`（强烈建议）
- [ ] 核心/重点项设置了 `style: "accent"` 使其视觉突出
- [ ] 关键路径节点设置了 `icon`（从上述40+图标中选取）
- [ ] 底部添加了 `requirements` 或 `safeguards` 丰富画面底部
- [ ] `subtitle` 为图表添加了精确定位说明
- [ ] 流程图节点间距合理（同层 ≤5个，避免过于拥挤）
- [ ] 架构图层数 3-7 层，每层卡片 3-8 个
- [ ] 关系图包含具体的 `edges` 描述跨域数据流
- [ ] 接口图包含双向流和 ACK 回执标签
