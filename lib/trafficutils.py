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
        }

        self.jrwdesti = {
            "関西空港/和歌山方面": "関西空港・和歌山"
        }

    #convert_destination
    def convert_destination(self, desti: str) -> str:
        d = self.jrwdesti.get(desti, desti)
        return d

    #convert_rapids
    def convert_rapids(self, rapid: str) -> str:
        d = self.jrwrapids.get(rapid, rapid)
        return d
