(function () {
  "use strict";

  var theme = {
    navy: "#073b72",
    blue: "#007bb5",
    teal: "#00877c",
    orange: "#ba7000",
    red: "#c9363e",
    purple: "#7047b8",
    text: "#062b52",
    subtext: "#365b82",
    line: "#d3e3f2",
    wash: "#edf8ff"
  };
  var typeNames = {
    bar_line: "柱线组合图",
    radar: "雷达图",
    sankey: "Sankey 流向图"
  };
  var state = {
    pkg: clone(window.DEMO_CHART_PACKAGE),
    index: 0,
    option: null,
    chart: null
  };

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function htmlEscape(value) {
    return String(value || "").replace(/[&<>"']/g, function (char) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char];
    });
  }

  function commonOption(spec) {
    return {
      backgroundColor: "#ffffff",
      animation: false,
      color: [theme.blue, theme.teal, theme.orange, theme.purple, theme.red],
      title: {
        left: 42,
        top: 28,
        text: spec.title,
        subtext: spec.subtitle || "",
        textStyle: { color: theme.navy, fontFamily: "Microsoft YaHei", fontSize: 36, fontWeight: 700 },
        subtextStyle: { color: theme.subtext, fontFamily: "Microsoft YaHei", fontSize: 19, lineHeight: 31 }
      },
      tooltip: { trigger: "item" },
      graphic: [
        {
          type: "rect",
          left: 30,
          bottom: 24,
          shape: { width: 1335, height: 44, r: 7 },
          style: { fill: "#ffffff", stroke: theme.line, lineWidth: 1 }
        },
        {
          type: "text",
          left: 49,
          bottom: 45,
          style: {
            text: "注：" + spec.note,
            fill: theme.subtext,
            font: '18px "Microsoft YaHei"'
          }
        },
        {
          type: "text",
          right: 49,
          bottom: 45,
          style: {
            text: "来源：" + spec.source + (spec.dataNotice ? " / " + spec.dataNotice : ""),
            fill: theme.subtext,
            font: '18px "Microsoft YaHei"',
            textAlign: "right"
          }
        }
      ]
    };
  }

  function buildBarLine(spec) {
    var option = commonOption(spec);
    option.legend = {
      top: 111,
      right: 50,
      textStyle: { color: theme.text, fontFamily: "Microsoft YaHei", fontSize: 19 }
    };
    option.grid = { left: 72, right: 82, top: 154, bottom: 112, containLabel: true };
    option.xAxis = {
      type: "category",
      data: spec.categories,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#9ec2e3" } },
      axisLabel: { color: theme.text, fontFamily: "Microsoft YaHei", fontSize: 19 }
    };
    option.yAxis = [
      {
        type: "value",
        name: spec.bar.unit,
        nameTextStyle: { color: theme.subtext },
        splitLine: { lineStyle: { color: "#e2edf6" } },
        axisLabel: { color: theme.subtext }
      },
      {
        type: "value",
        name: spec.line.unit,
        max: 100,
        nameTextStyle: { color: theme.subtext },
        splitLine: { show: false },
        axisLabel: { color: theme.subtext, formatter: "{value}%" }
      }
    ];
    option.series = [
      {
        name: spec.bar.name,
        type: "bar",
        barWidth: 52,
        itemStyle: { color: theme.blue, borderRadius: [5, 5, 0, 0] },
        label: { show: true, position: "top", color: theme.text },
        data: spec.bar.values
      },
      {
        name: spec.line.name,
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        symbolSize: 10,
        lineStyle: { color: theme.orange, width: 3 },
        itemStyle: { color: theme.orange },
        label: { show: true, formatter: "{c}%", color: theme.orange, position: "top" },
        data: spec.line.values
      }
    ];
    return option;
  }

  function buildRadar(spec) {
    var option = commonOption(spec);
    option.legend = {
      top: 118,
      right: 56,
      orient: "vertical",
      textStyle: { color: theme.text, fontFamily: "Microsoft YaHei", fontSize: 19 }
    };
    option.radar = {
      center: ["47%", "53%"],
      radius: "58%",
      indicator: spec.indicators,
      splitNumber: 5,
      axisName: { color: theme.text, fontSize: 20, fontFamily: "Microsoft YaHei" },
      splitArea: { areaStyle: { color: ["#ffffff", "#f7fbff"] } },
      splitLine: { lineStyle: { color: "#c8dded" } },
      axisLine: { lineStyle: { color: "#b8d3e7" } }
    };
    option.series = [{
      type: "radar",
      data: spec.series.map(function (series, index) {
        return {
          name: series.name,
          value: series.values,
          symbolSize: 7,
          lineStyle: { width: index === 0 ? 3 : 2, type: index === 0 ? "solid" : "dashed" },
          areaStyle: { opacity: index === 0 ? 0.16 : 0.04 }
        };
      })
    }];
    return option;
  }

  function buildSankey(spec) {
    var option = commonOption(spec);
    option.tooltip = { trigger: "item", formatter: function (params) {
      return params.dataType === "edge"
        ? params.data.source + " → " + params.data.target + "<br>" + params.data.value + " " + spec.unit
        : params.name;
    }};
    option.series = [{
      type: "sankey",
      left: 80,
      right: 95,
      top: 145,
      bottom: 112,
      nodeWidth: 24,
      nodeGap: 28,
      draggable: false,
      layoutIterations: 32,
      emphasis: { focus: "adjacency" },
      label: { color: theme.text, fontFamily: "Microsoft YaHei", fontSize: 20 },
      lineStyle: { color: "gradient", curveness: 0.48, opacity: 0.38 },
      itemStyle: { borderColor: "#ffffff", borderWidth: 1 },
      data: spec.nodes,
      links: spec.links,
      levels: [
        { depth: 0, itemStyle: { color: theme.blue } },
        { depth: 1, itemStyle: { color: theme.teal } },
        { depth: 2, itemStyle: { color: theme.orange } },
        { depth: 3, itemStyle: { color: theme.purple } }
      ]
    }];
    return option;
  }

  function buildOption(spec) {
    if (spec.type === "bar_line") return buildBarLine(spec);
    if (spec.type === "radar") return buildRadar(spec);
    if (spec.type === "sankey") return buildSankey(spec);
    throw new Error("不支持的 ECharts 图型: " + spec.type);
  }

  function validatePackage(pkg) {
    if (!pkg || !Array.isArray(pkg.charts) || pkg.charts.length === 0) {
      throw new Error("JSON 中必须包含非空 charts 数组。");
    }
    var ids = {};
    pkg.charts.forEach(function (chart, index) {
      ["id", "type", "title", "note", "source"].forEach(function (key) {
        if (!chart[key]) throw new Error("图件缺少字段: " + key);
      });
      if (ids[chart.id]) throw new Error("图件 id 不可重复: " + chart.id);
      ids[chart.id] = true;
      if (!typeNames[chart.type]) throw new Error("当前页面不支持图型: " + chart.type);
      if (chart.type === "bar_line") {
        validateBarLine(chart, index);
      }
      if (chart.type === "radar") {
        validateRadar(chart, index);
      }
      if (chart.type === "sankey") {
        validateSankey(chart, index);
      }
    });
  }

  function requireArray(value, message) {
    if (!Array.isArray(value) || value.length === 0) throw new Error(message);
  }

  function requireNumbers(values, message) {
    requireArray(values, message);
    if (values.some(function (value) { return typeof value !== "number" || !isFinite(value); })) {
      throw new Error(message);
    }
  }

  function validateBarLine(chart) {
    requireArray(chart.categories, "柱线组合图必须包含非空 categories。");
    if (!chart.bar || !chart.line) throw new Error("柱线组合图必须包含 bar 和 line。");
    requireNumbers(chart.bar.values, "柱线组合图 bar.values 必须为数值数组。");
    requireNumbers(chart.line.values, "柱线组合图 line.values 必须为数值数组。");
    if (chart.categories.length !== chart.bar.values.length ||
        chart.categories.length !== chart.line.values.length) {
      throw new Error("柱线组合图 categories、bar.values 与 line.values 的数量必须一致。");
    }
  }

  function validateRadar(chart) {
    requireArray(chart.indicators, "雷达图必须包含非空 indicators。");
    requireArray(chart.series, "雷达图必须包含非空 series。");
    chart.indicators.forEach(function (indicator) {
      if (!indicator.name || typeof indicator.max !== "number" || !isFinite(indicator.max) || indicator.max <= 0) {
        throw new Error("雷达图每个 indicator 必须包含名称和正数 max。");
      }
    });
    chart.series.forEach(function (series) {
      requireNumbers(series.values, "雷达图 series.values 必须为数值数组。");
      if (!series.name || series.values.length !== chart.indicators.length) {
        throw new Error("雷达图每组 series 必须有名称，且 values 数量与 indicators 一致。");
      }
    });
  }

  function validateSankey(chart) {
    requireArray(chart.nodes, "Sankey 图必须包含非空 nodes。");
    requireArray(chart.links, "Sankey 图必须包含非空 links。");
    var names = {};
    chart.nodes.forEach(function (node) {
      if (!node.name || names[node.name]) throw new Error("Sankey 节点名称不可为空或重复。");
      names[node.name] = true;
    });
    chart.links.forEach(function (link) {
      if (!names[link.source] || !names[link.target]) {
        throw new Error("Sankey link 的 source 和 target 必须引用已有节点。");
      }
      if (typeof link.value !== "number" || !isFinite(link.value) || link.value < 0) {
        throw new Error("Sankey link.value 必须为非负数。");
      }
    });
  }

  function renderTabs() {
    var tabs = document.getElementById("chart-tabs");
    tabs.innerHTML = state.pkg.charts.map(function (spec, index) {
      return '<button class="chart-tab ' + (index === state.index ? "active" : "") +
        '" data-index="' + index + '"><strong>' + htmlEscape(spec.title) +
        '</strong><small>' + htmlEscape(typeNames[spec.type]) + '</small></button>';
    }).join("");
    Array.prototype.forEach.call(tabs.querySelectorAll(".chart-tab"), function (tab) {
      tab.addEventListener("click", function () {
        state.index = Number(tab.getAttribute("data-index"));
        renderTabs();
        renderChart();
      });
    });
  }

  function renderChart() {
    var spec = state.pkg.charts[state.index];
    document.getElementById("chart-type").textContent = typeNames[spec.type];
    document.getElementById("placement").textContent = spec.placement ? "建议位置：" + spec.placement : "";
    if (!state.chart) {
      state.chart = echarts.init(document.getElementById("chart-stage"), null, { renderer: "svg" });
    }
    state.option = buildOption(spec);
    state.chart.setOption(state.option, true);
  }

  function safeFilename(value) {
    return value.replace(/[\\/:*?"<>|]/g, "_").replace(/\s+/g, "_");
  }

  function saveBlob(blob, filename) {
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function saveDataUrl(dataUrl, filename) {
    var link = document.createElement("a");
    link.href = dataUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  function bindActions() {
    document.getElementById("download-svg").addEventListener("click", function () {
      var spec = state.pkg.charts[state.index];
      var svg = state.chart.renderToSVGString();
      saveBlob(new Blob([svg], { type: "image/svg+xml;charset=utf-8" }), safeFilename(spec.title) + ".svg");
    });
    document.getElementById("download-png").addEventListener("click", function () {
      var spec = state.pkg.charts[state.index];
      var holder = document.createElement("div");
      holder.style.cssText = "position:fixed;left:-20000px;top:0;width:1600px;height:960px;background:#fff;";
      document.body.appendChild(holder);
      var canvasChart = echarts.init(holder, null, { renderer: "canvas", width: 1600, height: 960 });
      canvasChart.setOption(state.option, true);
      var dataUrl = canvasChart.getDataURL({ type: "png", pixelRatio: 2, backgroundColor: "#ffffff" });
      saveDataUrl(dataUrl, safeFilename(spec.title) + ".png");
      canvasChart.dispose();
      holder.remove();
    });
    document.getElementById("download-spec").addEventListener("click", function () {
      var current = state.pkg.charts[state.index];
      var output = { documentTitle: state.pkg.documentTitle, charts: [current] };
      saveBlob(new Blob([JSON.stringify(output, null, 2)], { type: "application/json;charset=utf-8" }),
        safeFilename(current.title) + ".json");
    });
    document.getElementById("reset-demo").addEventListener("click", function () {
      state.pkg = clone(window.DEMO_CHART_PACKAGE);
      state.index = 0;
      setMessage("已恢复内置演示图件。", false);
      renderTabs();
      renderChart();
    });
    document.getElementById("file-input").addEventListener("change", function (event) {
      var file = event.target.files[0];
      if (!file) return;
      file.text().then(function (content) {
        var pkg = JSON.parse(content);
        validatePackage(pkg);
        state.pkg = pkg;
        state.index = 0;
        setMessage("已导入 " + pkg.charts.length + " 张 AI 数据图描述。", false);
        renderTabs();
        renderChart();
      }).catch(function (error) {
        setMessage("导入失败：" + error.message, true);
      });
      event.target.value = "";
    });
    window.addEventListener("resize", function () {
      if (state.chart) state.chart.resize();
    });
  }

  function setMessage(message, error) {
    var target = document.getElementById("import-message");
    target.textContent = message;
    target.className = "message" + (error ? " error" : "");
  }

  validatePackage(state.pkg);
  bindActions();
  renderTabs();
  renderChart();
}());
