window.DEMO_CHART_PACKAGE = {
  "documentTitle": "高风险放射源监管平台投标技术方案",
  "charts": [
    {
      "title": "监测接入规模与覆盖率趋势图",
      "subtitle": "柱状展示接入点位，折线展示覆盖率",
      "source": "投标测算数据",
      "dataNotice": "示例数据，正式投标文件中需替换为确认口径",
      "categories": [
        "一期",
        "二期",
        "三期",
        "四期",
        "五期"
      ],
      "bar": {
        "name": "接入点位",
        "unit": "个",
        "values": [
          126,
          198,
          286,
          358,
          426
        ]
      },
      "line": {
        "name": "重点源覆盖率",
        "unit": "%",
        "values": [
          46,
          62,
          78,
          91,
          98
        ]
      }
    },
    {
      "title": "监管数据汇聚与应用流向图",
      "subtitle": "展示数据来源、治理汇聚与业务应用之间的流向关系",
      "source": "投标测算数据",
      "unit": "数据流量权重",
      "nodes": [
        {
          "name": "定位终端",
          "title": "定位终端",
          "desc": "",
          "id": "n00"
        },
        {
          "name": "涉源单位",
          "title": "涉源单位",
          "desc": "",
          "id": "n01"
        },
        {
          "name": "上级平台",
          "title": "上级平台",
          "desc": "",
          "id": "n02"
        },
        {
          "name": "接入交换",
          "title": "接入交换",
          "desc": "",
          "id": "n03"
        },
        {
          "name": "监管数据资源池",
          "title": "监管数据资源池",
          "desc": "",
          "id": "n04"
        },
        {
          "name": "实时监控",
          "title": "实时监控",
          "desc": "",
          "id": "n05"
        },
        {
          "name": "风险预警",
          "title": "风险预警",
          "desc": "",
          "id": "n06"
        },
        {
          "name": "统计分析",
          "title": "统计分析",
          "desc": "",
          "id": "n07"
        }
      ],
      "links": [
        {
          "source": "定位终端",
          "target": "接入交换",
          "value": 38
        },
        {
          "source": "涉源单位",
          "target": "接入交换",
          "value": 26
        },
        {
          "source": "上级平台",
          "target": "接入交换",
          "value": 14
        },
        {
          "source": "接入交换",
          "target": "监管数据资源池",
          "value": 78
        },
        {
          "source": "监管数据资源池",
          "target": "实时监控",
          "value": 30
        },
        {
          "source": "监管数据资源池",
          "target": "风险预警",
          "value": 25
        },
        {
          "source": "监管数据资源池",
          "target": "统计分析",
          "value": 23
        }
      ]
    }
  ]
};
