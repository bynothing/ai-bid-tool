window.DEMO_CHART_PACKAGE = {
  "documentTitle": "放射源监管平台数据型图件演示",
  "charts": [
    {
      "id": "coverage_trend",
      "type": "bar_line",
      "placement": "2.3 建设成效与覆盖能力",
      "title": "监测接入规模与覆盖率趋势图",
      "subtitle": "柱状展示接入点位，折线展示覆盖率",
      "categories": ["一期", "二期", "三期", "四期", "五期"],
      "bar": { "name": "接入点位", "unit": "个", "values": [126, 198, 286, 358, 426] },
      "line": { "name": "重点源覆盖率", "unit": "%", "values": [46, 62, 78, 91, 98] },
      "note": "演示数据，仅用于验证 AI 数据描述到标书统计图的生成效果。",
      "source": "排版测试模拟数据",
      "dataNotice": "非项目正式统计口径"
    },
    {
      "id": "capability_radar",
      "type": "radar",
      "placement": "4.1 平台能力响应",
      "title": "监管平台能力响应雷达图",
      "subtitle": "多维能力成熟度对比展示",
      "indicators": [
        { "name": "实时监测", "max": 100 }, { "name": "风险预警", "max": 100 },
        { "name": "闭环处置", "max": 100 }, { "name": "数据交换", "max": 100 },
        { "name": "审计追溯", "max": 100 }, { "name": "移动应用", "max": 100 }
      ],
      "series": [
        { "name": "本方案响应能力", "unit": "分", "values": [94, 90, 92, 86, 91, 84] },
        { "name": "基础要求基线", "unit": "分", "values": [70, 70, 70, 70, 70, 70] }
      ],
      "note": "雷达维度及分值为绘图能力演示，不代表最终投标评分承诺。",
      "source": "排版测试模拟数据",
      "dataNotice": "正式标书使用前需替换为确认口径"
    },
    {
      "id": "data_sankey",
      "type": "sankey",
      "placement": "3.2 数据资源与共享设计",
      "title": "监管数据汇聚与应用流向图",
      "subtitle": "展示数据来源、治理汇聚与业务应用之间的流向关系",
      "unit": "数据流量权重",
      "nodes": [
        { "name": "定位终端" }, { "name": "涉源单位" }, { "name": "上级平台" },
        { "name": "接入交换" }, { "name": "监管数据资源池" }, { "name": "实时监控" },
        { "name": "风险预警" }, { "name": "统计分析" }, { "name": "数据上报" }
      ],
      "links": [
        { "source": "定位终端", "target": "接入交换", "value": 42 },
        { "source": "涉源单位", "target": "接入交换", "value": 27 },
        { "source": "上级平台", "target": "接入交换", "value": 14 },
        { "source": "接入交换", "target": "监管数据资源池", "value": 83 },
        { "source": "监管数据资源池", "target": "实时监控", "value": 30 },
        { "source": "监管数据资源池", "target": "风险预警", "value": 22 },
        { "source": "监管数据资源池", "target": "统计分析", "value": 18 },
        { "source": "监管数据资源池", "target": "数据上报", "value": 13 }
      ],
      "note": "流向权重为绘图演示数据，真实项目应依据数据交换清单和统计口径配置。",
      "source": "排版测试模拟数据",
      "dataNotice": "非实际流量统计"
    }
  ]
};
