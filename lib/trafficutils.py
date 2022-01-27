import asyncio
import json
import urllib

class TrafficUtils:

    def __init__(self) -> None:
        self.jrwlines = {
            "北陸線": "hokuriku",
            "琵琶湖線": "hokurikubiwako",
            "京都線": "kyoto",
            "神戸線": "kobesanyo",
            "赤穂線": "ako",
            "湖西線": "kosei",
            "草津線": "kusatsu",
            "奈良線": "nara",
            "嵯峨野山陰線": "sagano",
            "山陰1線": "sanin1",
            "山陰2線": "sanin2",
            "おおさか東線": "osakahigashi",
            "宝塚線": "takarazuka",
            "福知山線": "fukuchiyama",
            "東西線": "tozai",
            "学研都市線": "gakkentoshi",
            "播但線": "bantan",
            "舞鶴線": "maizuru",
            "大阪環状線": "osakaloop",
            "ゆめ咲線": "yumesaki",
            "大和路線": "yamatoji",
            "阪和線": "hanwahagoromo",
            "関西空港線": "kansaiairport",
            "和歌山2線": "wakayama2",
            "和歌山1線": "wakayama1",
            "万葉まほろば線": "manyomahoroba",
            "関西線": "kansai",
            "きのくに線": "kinokuni",
            "宇野みなと線": "unominato",
            "瀬戸大橋線": "setoohashi",
            "山陽1線": "sanyo1",
            "伯備1線": "hakubi1",
            "可部線": "kabe",
            "山陽2線": "sanyo2",
            "山陽3線": "sanyo3",
            "呉線": "kure",
            "山陰3線": "sanin3",
            "因美線": "imbi1",
            "山陰4線": "sanin4",
            "伯備2線": "hakubi2"
        }

        self.jrwlinelists = {
            "wakayama1": "和歌山線 (五条 〜 和歌山)",
            "wakayama2": "和歌山線 (王寺 〜 五条)",
            "sanin1": "山陰線 (園部 〜 福知山)",
            "sanin2": "山陰線 (福知山 〜 居組)",
            "sanin3": "山陰線 (諸寄 〜 米子)",
            "sanin4": "山陰線 (米子 〜 益田)",
            "sanyo1": "山陽線 (上郡 〜 三原)",
            "sanyo2": "山陽線 (糸崎 〜 南岩国)",
            "sanyo3": "山陽線 (岩国 〜 下関)",
            "hakubi1": "伯備線 (倉敷 〜 新郷)",
            "hakubi2": "伯備線 (新郷 〜 伯耆大山)"
        }

        self.jrwrapids = {
            "大和路快": "大和路快速",
            "丹波路快": "丹波路快速",
            "みやこ快": "みやこ路快速",
            "関空紀州": "関空・紀州路快速",
            "関空快": "関空快速",
            "紀州路快": "紀州路快速",
            "快": "快速",
            "直快": "直通快速",
            "区快": "区間快速",
            "新快": "新快速",
            "特": "特急",
            "普通2": "普通 (JRゆめ咲線直通)"
        }

        self.jrwdesti = {
            "関西空港/和歌山方面": "関西空港・和歌山"
        }

        self.api_url = {
            "base": "https://www.train-guide.westjr.co.jp/api/v3",
            "lineinfo": "https://www.train-guide.westjr.co.jp/api/v3/{}.json",
            "stationinfo": "https://www.train-guide.westjr.co.jp/api/v3/{}_st.json",
            "maintenance": "https://www.train-guide.westjr.co.jp/api/v3/{}_maintenance.json",
            "areainfo": "https://www.train-guide.westjr.co.jp/api/v3/area_{}_master.json",
            "nowtime": "https://www.train-guide.westjr.co.jp/api/v3/currenttime.txt",
            "areatrafficinfo": "https://www.train-guide.westjr.co.jp/api/v3/area_{}_trafficinfo.json"
        }

    #convert_linename
    def convert_linename(self, line: str) -> str:
        d = self.jrwlinelists.get(line, line)
        return d

    #convert_destination
    def convert_destination(self, desti: str) -> str:
        d = self.jrwdesti.get(desti, desti)
        return d

    #convert_rapids
    def convert_rapids(self, rapid: str) -> str:
        d = self.jrwrapids.get(rapid, rapid)
        return d

    #get_delay_info
    async def get_delay_info(self, line: str):
        ret = urllib.request.urlopen(self.api_url["lineinfo"].format(line))
        ret_station = urllib.request.urlopen(self.api_url["stationinfo"].format(line))
        ret = json.loads(ret.read().decode("utf-8"))
        ret_station = json.loads(ret_station.read().decode("utf-8"))

        desti = None
        data = {}
        jsondata = {}

        for i in ret_station["stations"]:
            data[s["info"]["code"]] = s["info"]["name"]
        for i in ret["trains"]:
            if i["delayMinutes"] > 0:
                st = i["pos"].split("_")

                try:
                    desti = data[st[0]] + "辺り"
                except KeyError:
                    desti = "不明"

                type = self.convert_rapids(i["displayType"], i["displayType"])
                if type in "特急":
                    type = f"{type} {i['nickname']}"
                jsondata[str(type)] = {
                    "for": f"{self.convert_destination(i['dest']['text'], i['dest']]'text'])} 行き",
                    "delay": f"約{i['delayMinutes']}分遅れ (走行位置: {desti})"
                }
        return jsondata
