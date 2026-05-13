PROVINCE_CITY_DATA = """当前系统中可选的省份、城市和区县数据如下：
{
        "北京市": {
            "code": "110000",
            "cities": {
                "北京市": {"code": "110100", "districts": ["东城区", "西城区", "朝阳区", "丰台区", "石景山区", "海淀区",
                        "门头沟区", "房山区", "通州区", "顺义区", "昌平区", "大兴区",
                        "怀柔区", "平谷区", "密云区", "延庆区"]}
            }
        },
        "天津市": {
            "code": "120000",
            "cities": {
                "天津市": {"code": "120100", "districts": ["和平区", "河东区", "河西区", "南开区", "河北区", "红桥区",
                        "东丽区", "西青区", "津南区", "北辰区", "武清区", "宝坻区",
                        "滨海新区", "宁河区", "静海区", "蓟州区"]}
            }
        },
        "河北省": {
            "code": "130000",
            "cities": {
                "石家庄市": {"code": "130100", "districts": []},
                "唐山市": {"code": "130200", "districts": []},
                "秦皇岛市": {"code": "130300", "districts": []},
                "邯郸市": {"code": "130400", "districts": []},
                "邢台市": {"code": "130500", "districts": []},
                "保定市": {"code": "130600", "districts": []},
                "张家口市": {"code": "130700", "districts": []},
                "承德市": {"code": "130800", "districts": []},
                "沧州市": {"code": "130900", "districts": []},
                "廊坊市": {"code": "131000", "districts": []},
                "衡水市": {"code": "131100", "districts": []}
            }
        },
        "山西省": {
            "code": "140000",
            "cities": {
                "太原市": {"code": "140100", "districts": []},
                "大同市": {"code": "140200", "districts": []},
                "阳泉市": {"code": "140300", "districts": []},
                "长治市": {"code": "140400", "districts": []},
                "晋城市": {"code": "140500", "districts": []},
                "朔州市": {"code": "140600", "districts": []},
                "晋中市": {"code": "140700", "districts": []},
                "运城市": {"code": "140800", "districts": []},
                "忻州市": {"code": "140900", "districts": []},
                "临汾市": {"code": "141000", "districts": []},
                "吕梁市": {"code": "141100", "districts": []}
            }
        },
        "内蒙古自治区": {
            "code": "150000",
            "cities": {
                "呼和浩特市": {"code": "150100", "districts": []},
                "包头市": {"code": "150200", "districts": []},
                "乌海市": {"code": "150300", "districts": []},
                "赤峰市": {"code": "150400", "districts": []},
                "通辽市": {"code": "150500", "districts": []},
                "鄂尔多斯市": {"code": "150600", "districts": []},
                "呼伦贝尔市": {"code": "150700", "districts": []},
                "巴彦淖尔市": {"code": "150800", "districts": []},
                "乌兰察布市": {"code": "150900", "districts": []},
                "兴安盟": {"code": "152200", "districts": []},
                "锡林郭勒盟": {"code": "152500", "districts": []},
                "阿拉善盟": {"code": "152900", "districts": []}
            }
        },
        "辽宁省": {
            "code": "210000",
            "cities": {
                "沈阳市": {"code": "210100", "districts": []},
                "大连市": {"code": "210200", "districts": []},
                "鞍山市": {"code": "210300", "districts": []},
                "抚顺市": {"code": "210400", "districts": []},
                "本溪市": {"code": "210500", "districts": []},
                "丹东市": {"code": "210600", "districts": []},
                "锦州市": {"code": "210700", "districts": []},
                "营口市": {"code": "210800", "districts": []},
                "阜新市": {"code": "210900", "districts": []},
                "辽阳市": {"code": "211000", "districts": []},
                "盘锦市": {"code": "211100", "districts": []},
                "铁岭市": {"code": "211200", "districts": []},
                "朝阳市": {"code": "211300", "districts": []},
                "葫芦岛市": {"code": "211400", "districts": []}
            }
        },
        "吉林省": {
            "code": "220000",
            "cities": {
                "长春市": {"code": "220100", "districts": []},
                "吉林市": {"code": "220200", "districts": []},
                "四平市": {"code": "220300", "districts": []},
                "辽源市": {"code": "220400", "districts": []},
                "通化市": {"code": "220500", "districts": []},
                "白山市": {"code": "220600", "districts": []},
                "松原市": {"code": "220700", "districts": []},
                "白城市": {"code": "220800", "districts": []},
                "延边朝鲜族自治州": {"code": "222400", "districts": []}
            }
        },
        "黑龙江省": {
            "code": "230000",
            "cities": {
                "哈尔滨市": {"code": "230100", "districts": []},
                "齐齐哈尔市": {"code": "230200", "districts": []},
                "鸡西市": {"code": "230300", "districts": []},
                "鹤岗市": {"code": "230400", "districts": []},
                "双鸭山市": {"code": "230500", "districts": []},
                "大庆市": {"code": "230600", "districts": []},
                "伊春市": {"code": "230700", "districts": []},
                "佳木斯市": {"code": "230800", "districts": []},
                "七台河市": {"code": "230900", "districts": []},
                "牡丹江市": {"code": "231000", "districts": []},
                "黑河市": {"code": "231100", "districts": []},
                "绥化市": {"code": "231200", "districts": []},
                "大兴安岭地区": {"code": "232700", "districts": []}
            }
        },
        "上海市": {
            "code": "310000",
            "cities": {
                "上海市": {"code": "310100", "districts": ["黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区",
                         "杨浦区", "闵行区", "宝山区", "嘉定区", "浦东新区", "金山区",
                         "松江区", "青浦区", "奉贤区", "崇明区"]}
            }
        },
        "江苏省": {
            "code": "320000",
            "cities": {
                "南京市": {"code": "320100", "districts": []},
                "无锡市": {"code": "320200", "districts": []},
                "徐州市": {"code": "320300", "districts": []},
                "常州市": {"code": "320400", "districts": []},
                "苏州市": {"code": "320500", "districts": []},
                "南通市": {"code": "320600", "districts": []},
                "连云港市": {"code": "320700", "districts": []},
                "淮安市": {"code": "320800", "districts": []},
                "盐城市": {"code": "320900", "districts": []},
                "扬州市": {"code": "321000", "districts": []},
                "镇江市": {"code": "321100", "districts": []},
                "泰州市": {"code": "321200", "districts": []},
                "宿迁市": {"code": "321300", "districts": []}
            }
        },
        "浙江省": {
            "code": "330000",
            "cities": {
                "杭州市": {"code": "330100", "districts": []},
                "宁波市": {"code": "330200", "districts": []},
                "温州市": {"code": "330300", "districts": []},
                "嘉兴市": {"code": "330400", "districts": []},
                "湖州市": {"code": "330500", "districts": []},
                "绍兴市": {"code": "330600", "districts": []},
                "金华市": {"code": "330700", "districts": []},
                "衢州市": {"code": "330800", "districts": []},
                "舟山市": {"code": "330900", "districts": []},
                "台州市": {"code": "331000", "districts": []},
                "丽水市": {"code": "331100", "districts": []}
            }
        },
        "安徽省": {
            "code": "340000",
            "cities": {
                "合肥市": {"code": "340100", "districts": []},
                "芜湖市": {"code": "340200", "districts": []},
                "蚌埠市": {"code": "340300", "districts": []},
                "淮南市": {"code": "340400", "districts": []},
                "马鞍山市": {"code": "340500", "districts": []},
                "淮北市": {"code": "340600", "districts": []},
                "铜陵市": {"code": "340700", "districts": []},
                "安庆市": {"code": "340800", "districts": []},
                "黄山市": {"code": "341000", "districts": []},
                "滁州市": {"code": "341100", "districts": []},
                "阜阳市": {"code": "341200", "districts": []},
                "宿州市": {"code": "341300", "districts": []},
                "六安市": {"code": "341500", "districts": []},
                "亳州市": {"code": "341600", "districts": []},
                "池州市": {"code": "341700", "districts": []},
                "宣城市": {"code": "341800", "districts": []}
            }
        },
        "福建省": {
            "code": "350000",
            "cities": {
                "福州市": {"code": "350100", "districts": []},
                "厦门市": {"code": "350200", "districts": []},
                "莆田市": {"code": "350300", "districts": []},
                "三明市": {"code": "350400", "districts": []},
                "泉州市": {"code": "350500", "districts": []},
                "漳州市": {"code": "350600", "districts": []},
                "南平市": {"code": "350700", "districts": []},
                "龙岩市": {"code": "350800", "districts": []},
                "宁德市": {"code": "350900", "districts": []}
            }
        },
        "江西省": {
            "code": "360000",
            "cities": {
                "南昌市": {"code": "360100", "districts": []},
                "景德镇市": {"code": "360200", "districts": []},
                "萍乡市": {"code": "360300", "districts": []},
                "九江市": {"code": "360400", "districts": []},
                "新余市": {"code": "360500", "districts": []},
                "鹰潭市": {"code": "360600", "districts": []},
                "赣州市": {"code": "360700", "districts": []},
                "吉安市": {"code": "360800", "districts": []},
                "宜春市": {"code": "360900", "districts": []},
                "抚州市": {"code": "361000", "districts": []},
                "上饶市": {"code": "361100", "districts": []}
            }
        },
        "山东省": {
            "code": "370000",
            "cities": {
                "济南市": {"code": "370100", "districts": []},
                "青岛市": {"code": "370200", "districts": []},
                "淄博市": {"code": "370300", "districts": []},
                "枣庄市": {"code": "370400", "districts": []},
                "东营市": {"code": "370500", "districts": []},
                "烟台市": {"code": "370600", "districts": []},
                "潍坊市": {"code": "370700", "districts": []},
                "济宁市": {"code": "370800", "districts": []},
                "泰安市": {"code": "370900", "districts": []},
                "威海市": {"code": "371000", "districts": []},
                "日照市": {"code": "371100", "districts": []},
                "临沂市": {"code": "371300", "districts": []},
                "德州市": {"code": "371400", "districts": []},
                "聊城市": {"code": "371500", "districts": []},
                "滨州市": {"code": "371600", "districts": []},
                "菏泽市": {"code": "371700", "districts": []}
            }
        },
        "河南省": {
            "code": "410000",
            "cities": {
                "郑州市": {"code": "410100", "districts": []},
                "开封市": {"code": "410200", "districts": []},
                "洛阳市": {"code": "410300", "districts": []},
                "平顶山市": {"code": "410400", "districts": []},
                "安阳市": {"code": "410500", "districts": []},
                "鹤壁市": {"code": "410600", "districts": []},
                "新乡市": {"code": "410700", "districts": []},
                "焦作市": {"code": "410800", "districts": []},
                "濮阳市": {"code": "410900", "districts": []},
                "许昌市": {"code": "411000", "districts": []},
                "漯河市": {"code": "411100", "districts": []},
                "三门峡市": {"code": "411200", "districts": []},
                "南阳市": {"code": "411300", "districts": []},
                "商丘市": {"code": "411400", "districts": []},
                "信阳市": {"code": "411500", "districts": []},
                "周口市": {"code": "411600", "districts": []},
                "驻马店市": {"code": "411700", "districts": []},
                "济源市": {"code": "419001", "districts": []}
            }
        },
        "湖北省": {
            "code": "420000",
            "cities": {
                "武汉市": {"code": "420100", "districts": []},
                "黄石市": {"code": "420200", "districts": []},
                "十堰市": {"code": "420300", "districts": []},
                "宜昌市": {"code": "420500", "districts": []},
                "襄阳市": {"code": "420600", "districts": []},
                "鄂州市": {"code": "420700", "districts": []},
                "荆门市": {"code": "420800", "districts": []},
                "孝感市": {"code": "420900", "districts": []},
                "荆州市": {"code": "421000", "districts": []},
                "黄冈市": {"code": "421100", "districts": []},
                "咸宁市": {"code": "421200", "districts": []},
                "随州市": {"code": "421300", "districts": []},
                "恩施土家族苗族自治州": {"code": "422800", "districts": []},
                "仙桃市": {"code": "429004", "districts": []},
                "潜江市": {"code": "429005", "districts": []},
                "天门市": {"code": "429006", "districts": []}
            }
        },
        "湖南省": {
            "code": "430000",
            "cities": {
                "长沙市": {"code": "430100", "districts": []},
                "株洲市": {"code": "430200", "districts": []},
                "湘潭市": {"code": "430300", "districts": []},
                "衡阳市": {"code": "430400", "districts": []},
                "邵阳市": {"code": "430500", "districts": []},
                "岳阳市": {"code": "430600", "districts": []},
                "常德市": {"code": "430700", "districts": []},
                "张家界市": {"code": "430800", "districts": []},
                "益阳市": {"code": "430900", "districts": []},
                "郴州市": {"code": "431000", "districts": []},
                "永州市": {"code": "431100", "districts": []},
                "怀化市": {"code": "431200", "districts": []},
                "娄底市": {"code": "431300", "districts": []},
                "湘西土家族苗族自治州": {"code": "433100", "districts": []}
            }
        },
        "广东省": {
            "code": "440000",
            "cities": {
                "广州市": {"code": "440100", "districts": []},
                "韶关市": {"code": "440200", "districts": []},
                "深圳市": {"code": "440300", "districts": []},
                "珠海市": {"code": "440400", "districts": []},
                "汕头市": {"code": "440500", "districts": []},
                "佛山市": {"code": "440600", "districts": []},
                "江门市": {"code": "440700", "districts": []},
                "湛江市": {"code": "440800", "districts": []},
                "茂名市": {"code": "440900", "districts": []},
                "肇庆市": {"code": "441200", "districts": []},
                "惠州市": {"code": "441300", "districts": []},
                "梅州市": {"code": "441400", "districts": []},
                "汕尾市": {"code": "441500", "districts": []},
                "河源市": {"code": "441600", "districts": []},
                "阳江市": {"code": "441700", "districts": []},
                "清远市": {"code": "441800", "districts": []},
                "东莞市": {"code": "441900", "districts": []},
                "中山市": {"code": "442000", "districts": []},
                "潮州市": {"code": "445100", "districts": []},
                "揭阳市": {"code": "445200", "districts": []},
                "云浮市": {"code": "445300", "districts": []}
            }
        },
        "广西壮族自治区": {
            "code": "450000",
            "cities": {
                "南宁市": {"code": "450100", "districts": []},
                "柳州市": {"code": "450200", "districts": []},
                "桂林市": {"code": "450300", "districts": []},
                "梧州市": {"code": "450400", "districts": []},
                "北海市": {"code": "450500", "districts": []},
                "防城港市": {"code": "450600", "districts": []},
                "钦州市": {"code": "450700", "districts": []},
                "贵港市": {"code": "450800", "districts": []},
                "玉林市": {"code": "450900", "districts": []},
                "百色市": {"code": "451000", "districts": []},
                "贺州市": {"code": "451100", "districts": []},
                "河池市": {"code": "451200", "districts": []},
                "来宾市": {"code": "451300", "districts": []},
                "崇左市": {"code": "451400", "districts": []}
            }
        },
        "海南省": {
            "code": "460000",
            "cities": {
                "海口市": {"code": "460100", "districts": []},
                "三亚市": {"code": "460200", "districts": []},
                "三沙市": {"code": "460300", "districts": []},
                "儋州市": {"code": "460400", "districts": []}
            }
        },
        "重庆市": {
            "code": "500000",
            "cities": {
                "重庆市": {"code": "500100", "districts": ["万州区", "涪陵区", "渝中区", "大渡口区", "江北区", "沙坪坝区",
                         "九龙坡区", "南岸区", "北碚区", "綦江区", "大足区", "渝北区",
                         "巴南区", "黔江区", "长寿区", "江津区", "合川区", "永川区",
                         "南川区", "璧山区", "铜梁区", "潼南区", "荣昌区", "开州区",
                         "梁平区", "武隆区", "城口县", "丰都县", "垫江县", "忠县",
                         "云阳县", "奉节县", "巫山县", "巫溪县", "石柱土家族自治县",
                         "秀山土家族苗族自治县", "酉阳土家族苗族自治县",
                         "彭水苗族土家族自治县"]}
            }
        },
        "四川省": {
            "code": "510000",
            "cities": {
                "成都市": {"code": "510100", "districts": []},
                "自贡市": {"code": "510300", "districts": []},
                "攀枝花市": {"code": "510400", "districts": []},
                "泸州市": {"code": "510500", "districts": []},
                "德阳市": {"code": "510600", "districts": []},
                "绵阳市": {"code": "510700", "districts": []},
                "广元市": {"code": "510800", "districts": []},
                "遂宁市": {"code": "510900", "districts": []},
                "内江市": {"code": "511000", "districts": []},
                "乐山市": {"code": "511100", "districts": []},
                "南充市": {"code": "511300", "districts": []},
                "眉山市": {"code": "511400", "districts": []},
                "宜宾市": {"code": "511500", "districts": []},
                "广安市": {"code": "511600", "districts": []},
                "达州市": {"code": "511700", "districts": []},
                "雅安市": {"code": "511800", "districts": []},
                "巴中市": {"code": "511900", "districts": []},
                "资阳市": {"code": "512000", "districts": []},
                "阿坝藏族羌族自治州": {"code": "513200", "districts": []},
                "甘孜藏族自治州": {"code": "513300", "districts": []},
                "凉山彝族自治州": {"code": "513400", "districts": []}
            }
        },
        "贵州省": {
            "code": "520000",
            "cities": {
                "贵阳市": {"code": "520100", "districts": []},
                "六盘水市": {"code": "520200", "districts": []},
                "遵义市": {"code": "520300", "districts": []},
                "安顺市": {"code": "520400", "districts": []},
                "毕节市": {"code": "520500", "districts": []},
                "铜仁市": {"code": "520600", "districts": []},
                "黔西南布依族苗族自治州": {"code": "522300", "districts": []},
                "黔东南苗族侗族自治州": {"code": "522600", "districts": []},
                "黔南布依族苗族自治州": {"code": "522700", "districts": []}
            }
        },
        "云南省": {
            "code": "530000",
            "cities": {
                "昆明市": {"code": "530100", "districts": []},
                "曲靖市": {"code": "530300", "districts": []},
                "玉溪市": {"code": "530400", "districts": []},
                "保山市": {"code": "530500", "districts": []},
                "昭通市": {"code": "530600", "districts": []},
                "丽江市": {"code": "530700", "districts": []},
                "普洱市": {"code": "530800", "districts": []},
                "临沧市": {"code": "530900", "districts": []},
                "楚雄彝族自治州": {"code": "532300", "districts": []},
                "红河哈尼族彝族自治州": {"code": "532500", "districts": []},
                "文山壮族苗族自治州": {"code": "532600", "districts": []},
                "西双版纳傣族自治州": {"code": "532800", "districts": []},
                "大理白族自治州": {"code": "532900", "districts": []},
                "德宏傣族景颇族自治州": {"code": "533100", "districts": []},
                "怒江傈僳族自治州": {"code": "533300", "districts": []},
                "迪庆藏族自治州": {"code": "533400", "districts": []}
            }
        },
        "西藏自治区": {
            "code": "540000",
            "cities": {
                "拉萨市": {"code": "540100", "districts": []},
                "日喀则市": {"code": "540200", "districts": []},
                "昌都市": {"code": "540300", "districts": []},
                "林芝市": {"code": "540400", "districts": []},
                "山南市": {"code": "540600", "districts": []},
                "那曲市": {"code": "540500", "districts": []},
                "阿里地区": {"code": "542500", "districts": []}
            }
        },
        "陕西省": {
            "code": "610000",
            "cities": {
                "西安市": {"code": "610100", "districts": []},
                "铜川市": {"code": "610200", "districts": []},
                "宝鸡市": {"code": "610300", "districts": []},
                "咸阳市": {"code": "610400", "districts": []},
                "渭南市": {"code": "610500", "districts": []},
                "延安市": {"code": "610600", "districts": []},
                "汉中市": {"code": "610700", "districts": []},
                "榆林市": {"code": "610800", "districts": []},
                "安康市": {"code": "610900", "districts": []},
                "商洛市": {"code": "611000", "districts": []}
            }
        },
        "甘肃省": {
            "code": "620000",
            "cities": {
                "兰州市": {"code": "620100", "districts": []},
                "嘉峪关市": {"code": "620200", "districts": []},
                "金昌市": {"code": "620300", "districts": []},
                "白银市": {"code": "620400", "districts": []},
                "天水市": {"code": "620500", "districts": []},
                "武威市": {"code": "620600", "districts": []},
                "张掖市": {"code": "620700", "districts": []},
                "平凉市": {"code": "620800", "districts": []},
                "酒泉市": {"code": "620900", "districts": []},
                "庆阳市": {"code": "621000", "districts": []},
                "定西市": {"code": "621100", "districts": []},
                "陇南市": {"code": "621200", "districts": []},
                "临夏回族自治州": {"code": "622900", "districts": []},
                "甘南藏族自治州": {"code": "623000", "districts": []}
            }
        },
        "青海省": {
            "code": "630000",
            "cities": {
                "西宁市": {"code": "630100", "districts": []},
                "海东市": {"code": "630200", "districts": []},
                "海北藏族自治州": {"code": "632200", "districts": []},
                "黄南藏族自治州": {"code": "632300", "districts": []},
                "海南藏族自治州": {"code": "632500", "districts": []},
                "果洛藏族自治州": {"code": "632600", "districts": []},
                "玉树藏族自治州": {"code": "632700", "districts": []},
                "海西蒙古族藏族自治州": {"code": "632800", "districts": []}
            }
        },
        "宁夏回族自治区": {
            "code": "640000",
            "cities": {
                "银川市": {"code": "640100", "districts": []},
                "石嘴山市": {"code": "640200", "districts": []},
                "吴忠市": {"code": "640300", "districts": []},
                "固原市": {"code": "640400", "districts": []},
                "中卫市": {"code": "640500", "districts": []}
            }
        },
        "新疆维吾尔自治区": {
            "code": "650000",
            "cities": {
                "乌鲁木齐市": {"code": "650100", "districts": []},
                "克拉玛依市": {"code": "650200", "districts": []},
                "吐鲁番市": {"code": "650400", "districts": []},
                "哈密市": {"code": "650500", "districts": []},
                "昌吉回族自治州": {"code": "652300", "districts": []},
                "博尔塔拉蒙古自治州": {"code": "652700", "districts": []},
                "巴音郭楞蒙古自治州": {"code": "652800", "districts": []},
                "阿克苏地区": {"code": "652900", "districts": []},
                "克孜勒苏柯尔克孜自治州": {"code": "653000", "districts": []},
                "喀什地区": {"code": "653100", "districts": []},
                "和田地区": {"code": "653200", "districts": []},
                "伊犁哈萨克自治州": {"code": "654000", "districts": []},
                "塔城地区": {"code": "654200", "districts": []},
                "阿勒泰地区": {"code": "654300", "districts": []},
                "石河子市": {"code": "659001", "districts": []},
                "阿拉尔市": {"code": "659002", "districts": []},
                "图木舒克市": {"code": "659003", "districts": []},
                "五家渠市": {"code": "659004", "districts": []},
                "北屯市": {"code": "659005", "districts": []},
                "铁门关市": {"code": "659006", "districts": []},
                "双河市": {"code": "659007", "districts": []},
                "可克达拉市": {"code": "659008", "districts": []},
                "昆玉市": {"code": "659009", "districts": []},
                "胡杨河市": {"code": "659010", "districts": []}
            }
        }
    }
"""
