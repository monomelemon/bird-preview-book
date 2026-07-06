const DATA_FILES = {
  metadata: "data/metadata.json",
  species: "data/species.json",
  taxonomy: "data/taxonomy.json",
  locations: "data/locations.json",
  occurrences: "data/occurrences.json",
  media: "data/media.json",
  identification: "data/identification.json",
  similar: "data/similar.json"
};

const DATA_CACHE_VERSION = "v2-fix-2026-07-02-taxonomy-image-fallback";

const STORAGE_KEYS = {
  lists: "birdPreviewBook:lists",
  checks: (listId) => `birdPreviewBook:checks:${listId}`,
  notes: (listId) => `birdPreviewBook:notes:${listId}`
};

const ORDER_ZH_BY_LATIN = {
  Pterocliformes: "沙鸡目"
};

const FAMILY_ZH_BY_LATIN = {
  Accipitridae: "鹰科",
  Acrocephalidae: "苇莺科",
  Aegithalidae: "长尾山雀科",
  Aegithinidae: "雀鹎科",
  Alaudidae: "百灵科",
  Alcedinidae: "翠鸟科",
  Alcidae: "海雀科",
  Anatidae: "鸭科",
  Anhingidae: "蛇鹈科",
  Apodidae: "雨燕科",
  Ardeidae: "鹭科",
  Artamidae: "燕鵙科",
  Bucerotidae: "犀鸟科",
  Burhinidae: "石鸻科",
  Campephagidae: "山椒鸟科",
  Caprimulgidae: "夜鹰科",
  Certhiidae: "旋木雀科",
  Cettiidae: "树莺科",
  Charadriidae: "鸻科",
  Chloropseidae: "叶鹎科",
  Ciconiidae: "鹳科",
  Cinclidae: "河乌科",
  Cisticolidae: "扇尾莺科",
  Columbidae: "鸠鸽科",
  Coraciidae: "佛法僧科",
  Corvidae: "鸦科",
  Cuculidae: "杜鹃科",
  Dicaeidae: "啄花鸟科",
  Dicruridae: "卷尾科",
  Emberizidae: "鹀科",
  Estrildidae: "梅花雀科",
  Eurylaimidae: "阔嘴鸟科",
  Falconidae: "隼科",
  Fregatidae: "军舰鸟科",
  Fringillidae: "燕雀科",
  Glareolidae: "燕鸻科",
  Gruidae: "鹤科",
  Hemiprocnidae: "树燕科",
  Hirundinidae: "燕科",
  Icteridae: "拟鹂科",
  Indicatoridae: "响蜜䴕科",
  Irenidae: "和平鸟科",
  Jacanidae: "水雉科",
  Laniidae: "伯劳科",
  Laridae: "鸥科",
  Leiothrichidae: "噪鹛科",
  Locustellidae: "蝗莺科",
  Megalaimidae: "拟啄木鸟科",
  Meropidae: "蜂虎科",
  Monarchidae: "王鹟科",
  Motacillidae: "鹡鸰科",
  Muscicapidae: "鹟科",
  Nectariniidae: "太阳鸟科",
  Oriolidae: "黄鹂科",
  Otididae: "鸨科",
  Paradoxornithidae: "鸦雀科",
  Paridae: "山雀科",
  Passerellidae: "雀鹀科",
  Passeridae: "雀科",
  Pelecanidae: "鹈鹕科",
  Pellorneidae: "画眉科",
  Phaethontidae: "鹲科",
  Phalacrocoracidae: "鸬鹚科",
  Phasianidae: "雉科",
  Phylloscopidae: "柳莺科",
  Picidae: "啄木鸟科",
  Pittidae: "八色鸫科",
  Ploceidae: "织布鸟科",
  Pnoepygidae: "短翅莺科",
  Podargidae: "蟆口鸱科",
  Procellariidae: "鹱科",
  Prunellidae: "岩鹨科",
  Psittaculidae: "鹦鹉科",
  Pteroclidae: "沙鸡科",
  Pycnonotidae: "鹎科",
  Rallidae: "秧鸡科",
  Recurvirostridae: "反嘴鹬科",
  Remizidae: "攀雀科",
  Rhipiduridae: "扇尾鹟科",
  Scolopacidae: "鹬科",
  Sittidae: "鳾科",
  Stenostiridae: "仙鹟科",
  Strigidae: "鸱鸮科",
  Sturnidae: "椋鸟科",
  Sylviidae: "莺鹛科",
  Threskiornithidae: "鹮科",
  Timaliidae: "林鹛科",
  Trogonidae: "咬鹃科",
  Turdidae: "鸫科",
  Turnicidae: "三趾鹑科",
  Tytonidae: "仓鸮科",
  Urocynchramidae: "朱鹀科",
  Vangidae: "钩嘴鵙科",
  Vireonidae: "莺雀科",
  Zosteropidae: "绣眼鸟科"
};

const ALL_MONTHS = [1,2,3,4,5,6,7,8,9,10,11,12];
const app = document.querySelector("#app");
let appData = null;
let state = { imageIndex: 0, matchResults: [], imageFailures: {} };
let _lastRouteName = "";

const $html = (strings, ...values) => strings.reduce((out, str, i) => out + str + (values[i] ?? ""), "");
const esc = (value) => String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
const birdCheckIcon = (checked) => `<svg class="bird-icon ${checked ? "bird-solid" : "bird-outline"}" viewBox="0 0 24 24"><path d="M16 7h.01"/><path d="M3.4 18H12a8 8 0 0 0 8-8V7a4 4 0 0 0-7.28-2.3L2 20"/><path d="m20 7 2 .5-2 .5"/><path d="M10 18v3"/><path d="M14 17.75V21"/><path d="M7 18a6 6 0 0 0 3.84-10.61"/></svg>`;
const nowISO = () => new Date().toISOString();
const safeParse = (text, fallback) => { if (text == null) return fallback; try { return JSON.parse(text); } catch { return fallback; } };
const TRAD_TO_SIMP = {
  "並":"并",
  "乾":"干",
  "亂":"乱",
  "亞":"亚",
  "佈":"布",
  "併":"并",
  "來":"来",
  "侶":"侣",
  "係":"系",
  "倉":"仓",
  "個":"个",
  "們":"们",
  "倫":"伦",
  "側":"侧",
  "偽":"伪",
  "傳":"传",
  "傾":"倾",
  "僅":"仅",
  "儘":"尽",
  "優":"优",
  "內":"内",
  "兩":"两",
  "凍":"冻",
  "別":"别",
  "則":"则",
  "剛":"刚",
  "劃":"划",
  "劍":"剑",
  "動":"动",
  "勞":"劳",
  "勢":"势",
  "匯":"汇",
  "區":"区",
  "協":"协",
  "卻":"却",
  "參":"参",
  "叢":"丛",
  "員":"员",
  "問":"问",
  "啞":"哑",
  "啟":"启",
  "喪":"丧",
  "喬":"乔",
  "單":"单",
  "嗶":"哔",
  "嘯":"啸",
  "嘰":"叽",
  "嚇":"吓",
  "嚨":"咙",
  "嚴":"严",
  "囂":"嚣",
  "國":"国",
  "圍":"围",
  "園":"园",
  "圓":"圆",
  "圖":"图",
  "堊":"垩",
  "報":"报",
  "場":"场",
  "塊":"块",
  "墊":"垫",
  "壞":"坏",
  "壯":"壮",
  "夠":"够",
  "夾":"夹",
  "奧":"奥",
  "奪":"夺",
  "學":"学",
  "實":"实",
  "寬":"宽",
  "寵":"宠",
  "寶":"宝",
  "將":"将",
  "專":"专",
  "尋":"寻",
  "對":"对",
  "導":"导",
  "層":"层",
  "屬":"属",
  "岡":"冈",
  "島":"岛",
  "峽":"峡",
  "嶼":"屿",
  "帶":"带",
  "幣":"币",
  "幾":"几",
  "庫":"库",
  "廣":"广",
  "強":"强",
  "彎":"弯",
  "後":"后",
  "從":"从",
  "徵":"征",
  "恆":"恒",
  "愛":"爱",
  "態":"态",
  "慣":"惯",
  "慮":"虑",
  "慶":"庆",
  "憂":"忧",
  "應":"应",
  "懸":"悬",
  "掛":"挂",
  "採":"采",
  "換":"换",
  "搖":"摇",
  "撾":"挝",
  "擁":"拥",
  "擇":"择",
  "擊":"击",
  "擔":"担",
  "據":"据",
  "擬":"拟",
  "擴":"扩",
  "擺":"摆",
  "擾":"扰",
  "攝":"摄",
  "數":"数",
  "斷":"断",
  "於":"于",
  "時":"时",
  "會":"会",
  "東":"东",
  "條":"条",
  "棲":"栖",
  "業":"业",
  "極":"极",
  "榮":"荣",
  "構":"构",
  "樂":"乐",
  "標":"标",
  "樣":"样",
  "樫":"㭴",
  "樹":"树",
  "機":"机",
  "橫":"横",
  "權":"权",
  "欖":"榄",
  "歐":"欧",
  "歡":"欢",
  "歲":"岁",
  "歷":"历",
  "歸":"归",
  "殺":"杀",
  "殼":"壳",
  "氣":"气",
  "沒":"没",
  "況":"况",
  "淺":"浅",
  "減":"减",
  "測":"测",
  "準":"准",
  "溝":"沟",
  "溫":"温",
  "滅":"灭",
  "滿":"满",
  "漁":"渔",
  "漢":"汉",
  "漸":"渐",
  "漿":"浆",
  "潑":"泼",
  "潛":"潜",
  "潤":"润",
  "澤":"泽",
  "濃":"浓",
  "濕":"湿",
  "濟":"济",
  "濱":"滨",
  "瀕":"濒",
  "灘":"滩",
  "灣":"湾",
  "為":"为",
  "烏":"乌",
  "無":"无",
  "熱":"热",
  "爭":"争",
  "爲":"为",
  "爾":"尔",
  "牠":"它",
  "狀":"状",
  "狹":"狭",
  "猶":"犹",
  "獨":"独",
  "獲":"获",
  "獵":"猎",
  "現":"现",
  "瑪":"玛",
  "環":"环",
  "產":"产",
  "畢":"毕",
  "畫":"画",
  "異":"异",
  "當":"当",
  "發":"发",
  "盜":"盗",
  "眾":"众",
  "確":"确",
  "磯":"矶",
  "禦":"御",
  "禿":"秃",
  "種":"种",
  "稱":"称",
  "穀":"谷",
  "積":"积",
  "穩":"稳",
  "窩":"窝",
  "窪":"洼",
  "競":"竞",
  "筆":"笔",
  "節":"节",
  "範":"范",
  "築":"筑",
  "簑":"蓑",
  "簡":"简",
  "籠":"笼",
  "粵":"粤",
  "紀":"纪",
  "約":"约",
  "紅":"红",
  "紋":"纹",
  "納":"纳",
  "紐":"纽",
  "純":"纯",
  "紛":"纷",
  "細":"细",
  "結":"结",
  "絕":"绝",
  "給":"给",
  "絨":"绒",
  "統":"统",
  "絲":"丝",
  "經":"经",
  "綠":"绿",
  "綬":"绶",
  "維":"维",
  "綴":"缀",
  "緋":"绯",
  "線":"线",
  "緣":"缘",
  "緬":"缅",
  "緯":"纬",
  "練":"练",
  "緻":"致",
  "縣":"县",
  "縫":"缝",
  "縮":"缩",
  "縱":"纵",
  "繞":"绕",
  "繽":"缤",
  "續":"续",
  "纖":"纤",
  "羅":"罗",
  "義":"义",
  "習":"习",
  "翹":"翘",
  "聖":"圣",
  "聞":"闻",
  "聯":"联",
  "聲":"声",
  "脅":"胁",
  "脇":"胁",
  "脈":"脉",
  "脹":"胀",
  "腦":"脑",
  "腳":"脚",
  "膚":"肤",
  "臉":"脸",
  "臘":"腊",
  "臨":"临",
  "臺":"台",
  "與":"与",
  "興":"兴",
  "舊":"旧",
  "艦":"舰",
  "艷":"艳",
  "茲":"兹",
  "莖":"茎",
  "華":"华",
  "萊":"莱",
  "萬":"万",
  "葉":"叶",
  "著":"着",
  "葦":"苇",
  "蒼":"苍",
  "蓋":"盖",
  "蓽":"荜",
  "薑":"姜",
  "薩":"萨",
  "藍":"蓝",
  "藝":"艺",
  "蘆":"芦",
  "蘇":"苏",
  "蘭":"兰",
  "處":"处",
  "號":"号",
  "蝦":"虾",
  "螞":"蚂",
  "蟲":"虫",
  "蟻":"蚁",
  "蠣":"蛎",
  "術":"术",
  "衛":"卫",
  "衝":"冲",
  "裏":"里",
  "裝":"装",
  "裡":"里",
  "複":"复",
  "襲":"袭",
  "見":"见",
  "規":"规",
  "覓":"觅",
  "視":"视",
  "親":"亲",
  "覺":"觉",
  "觀":"观",
  "計":"计",
  "訓":"训",
  "記":"记",
  "訪":"访",
  "許":"许",
  "評":"评",
  "詛":"诅",
  "詞":"词",
  "話":"话",
  "該":"该",
  "認":"认",
  "語":"语",
  "誤":"误",
  "說":"说",
  "説":"说",
  "調":"调",
  "論":"论",
  "諧":"谐",
  "諾":"诺",
  "證":"证",
  "識":"识",
  "譜":"谱",
  "譯":"译",
  "議":"议",
  "護":"护",
  "變":"变",
  "讓":"让",
  "豎":"竖",
  "豐":"丰",
  "豔":"艳",
  "豬":"猪",
  "貓":"猫",
  "負":"负",
  "貨":"货",
  "責":"责",
  "貴":"贵",
  "貿":"贸",
  "賀":"贺",
  "資":"资",
  "賊":"贼",
  "賓":"宾",
  "賞":"赏",
  "賴":"赖",
  "贏":"赢",
  "趨":"趋",
  "跡":"迹",
  "蹠":"跖",
  "蹤":"踪",
  "蹺":"跷",
  "軍":"军",
  "軟":"软",
  "軼":"轶",
  "較":"较",
  "輕":"轻",
  "輪":"轮",
  "轉":"转",
  "農":"农",
  "這":"这",
  "連":"连",
  "週":"周",
  "進":"进",
  "過":"过",
  "達":"达",
  "遜":"逊",
  "遠":"远",
  "適":"适",
  "遷":"迁",
  "選":"选",
  "遺":"遗",
  "還":"还",
  "邊":"边",
  "郵":"邮",
  "鄉":"乡",
  "釋":"释",
  "釐":"厘",
  "針":"针",
  "鈷":"钴",
  "銀":"银",
  "銅":"铜",
  "銳":"锐",
  "鋒":"锋",
  "鋸":"锯",
  "錄":"录",
  "錐":"锥",
  "錫":"锡",
  "鎮":"镇",
  "鏡":"镜",
  "鐮":"镰",
  "鐵":"铁",
  "鑽":"钻",
  "長":"长",
  "閉":"闭",
  "開":"开",
  "閒":"闲",
  "間":"间",
  "闊":"阔",
  "關":"关",
  "陸":"陆",
  "際":"际",
  "隨":"随",
  "隱":"隐",
  "隻":"只",
  "雖":"虽",
  "雙":"双",
  "雛":"雏",
  "雜":"杂",
  "雞":"鸡",
  "離":"离",
  "難":"难",
  "雲":"云",
  "電":"电",
  "靈":"灵",
  "韓":"韩",
  "響":"响",
  "頁":"页",
  "頂":"顶",
  "項":"项",
  "須":"须",
  "頗":"颇",
  "領":"领",
  "頭":"头",
  "頰":"颊",
  "頸":"颈",
  "頻":"频",
  "顆":"颗",
  "題":"题",
  "額":"额",
  "顏":"颜",
  "顛":"颠",
  "類":"类",
  "顧":"顾",
  "顯":"显",
  "風":"风",
  "飛":"飞",
  "飲":"饮",
  "飼":"饲",
  "飾":"饰",
  "養":"养",
  "餘":"余",
  "餵":"喂",
  "馬":"马",
  "馮":"冯",
  "體":"体",
  "鬍":"胡",
  "鬚":"须",
  "魚":"鱼",
  "魯":"鲁",
  "鮮":"鲜",
  "鰲":"鳌",
  "鳥":"鸟",
  "鳧":"凫",
  "鳩":"鸠",
  "鳳":"凤",
  "鳴":"鸣",
  "鳶":"鸢",
  "鴉":"鸦",
  "鴒":"鸰",
  "鴓":"䴓",
  "鴛":"鸳",
  "鴝":"鸲",
  "鴞":"鸮",
  "鴟":"鸱",
  "鴣":"鸪",
  "鴦":"鸯",
  "鴨":"鸭",
  "鴴":"鸻",
  "鴷":"䴕",
  "鴻":"鸿",
  "鴿":"鸽",
  "鵐":"鹀",
  "鵑":"鹃",
  "鵒":"鹆",
  "鵓":"鹁",
  "鵜":"鹈",
  "鵝":"鹅",
  "鵟":"𫛭",
  "鵠":"鹄",
  "鵪":"鹌",
  "鵯":"鹎",
  "鵰":"雕",
  "鵲":"鹊",
  "鶇":"鸫",
  "鶉":"鹑",
  "鶊":"鹒",
  "鶖":"鹙",
  "鶘":"鹕",
  "鶚":"鹗",
  "鶡":"鹖",
  "鶥":"鹛",
  "鶬":"鸧",
  "鶯":"莺",
  "鶲":"鹟",
  "鶴":"鹤",
  "鶺":"鹡",
  "鶻":"鹘",
  "鷂":"鹞",
  "鷊":"鹝",
  "鷗":"鸥",
  "鷦":"鹪",
  "鷯":"鹩",
  "鷲":"鹫",
  "鷳":"鹇",
  "鷴":"鹇",
  "鷸":"鹬",
  "鷹":"鹰",
  "鷺":"鹭",
  "鷿":"䴙",
  "鸂":"㶉",
  "鸊":"䴘",
  "鸐":"𬸘",
  "鸕":"鸬",
  "鸗":"𬸶",
  "鸝":"鹂",
  "鹹":"咸",
  "鹼":"碱",
  "麗":"丽",
  "麥":"麦",
  "麼":"么",
  "黃":"黄",
  "點":"点",
  "齒":"齿",
  "龍":"龙",
  "龐":"庞",
  "龜":"龟"
};
function toSimplified(text) {
  text = String(text || "");
  let result = "";
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    result += TRAD_TO_SIMP[c] || c;
  }
  return result;
}

const normalize = (text) => toSimplified(text).trim().toLowerCase();

const PINYIN_INITIALS = String.raw`
a:阿啊鹌
b:八百白斑半宝北背本鼻比币碧扁冰滨波伯薄布瓣暴壁杓鸨膀鹎
c:仓草叉茶长朝潮彻匙翅崇丑出楚川锤雌赐粗簇翠村纯苍藏赤橙池察彩塍鹑鹚
d:达大代带丹淡岛道地滇典点雕顶东冬董豆独渡短断对多戴旦杜稻端钝鸫
e:俄峨额厄鄂鹗耳洱二恶鹅
f:发番翻凡反饭范方飞非绯斐粉丰风冯凤佛夫弗浮福斧附复凫缝翡腹蜂费
g:盖干甘刚高鸽歌格各庚工公狗古谷骨瓜关冠鹳灌光广龟贵桂郭哥孤钩鬼鸪
h:哈海邯寒汉旱杭毫禾合河貉褐鹤黑恒横衡红虹鸿喉厚狐胡湖虎花华滑画槐环鹮黄蝗灰辉徽火荒贺鸻鹕鹱
j:叽鸡姬基极急棘几计纪季济加佳家甲尖间肩剪碱剑涧暗健箭江将交角脚教接揭节洁捷靛金锦近经颈九酒旧居菊巨鹃卷绢军椒矶舰颊鲣鳽鵙鸠䳭鹡鹪鹫
k:卡开堪坎看康科壳可克肯空口苦库矿阔孔眶颏鵟
l:拉蓝朗浪老勒雷类黎篱李里理力历丽栗笠连帘镰脸链良两根亮辽猎鬣林临鳞灵岭另琉硫鹨六龙隆娄卢芦鸬鹭绿峦轮罗裸乐兰利劳旅柳椋流璃蛎蜡领鸰鹂鹠鹩䴕
m:麻马毛矛茅铆煤美门蒙猛梦迷米密绵冕面苗民闽名明鸣摸末漠墨牡木牧棉眉蜜鹛鹲麦
n:南瑙内尼泥拟鸟宁牛农浓弄努女暖诺拿
o:欧鸥
p:爬帕牌攀盘胖刨炮佩盆蓬皮片漂拼品平瓶普䴙圃琵蹼
q:七齐奇旗企启千迁前潜浅茜强墙悄翘鞘亲秦青清庆琼丘秋鸲曲全拳雀群栖球琴祁鹊
r:日绒
s:萨鳃三散沙沙山珊陕善上勺少蛇社深神升生声圣尸十石食史始鹬寿书舒疏鼠曙树数双水睡丝四松苏宿虽穗隼蓑缩索思扇氏胜色䴓
t:台苔太泰滩檀唐塘陶特提天田铁通同铜童头秃图土团屯驼椭䴘他腿臀鹈
w:瓦弯玩晚万王网苇尾位魏文问翁乌无吴五鹉雾兀哇纹维鹀鹟
x:西吸希昔溪锡蟋习喜细瞎峡狭下先仙咸显线乡香湘想项小楔蝎斜谢心新星兴行杏胸熊修绣须旭悬雪血信啸巽旋玄相稀笑胁锈靴鸮鸺鹇
y:鸦鸭崖亚烟岩沿眼艳燕秧杨洋仰腰摇冶野叶夜一伊衣遗疑以异翼阴银隐印莺鹰迎影映硬勇尤有幼渝鱼羽雨玉鸢元园原圆缘远约月岳越云陨鹦咬渔游疣蚁阳雁页鸯鸳鹞
z:杂在赞灶泽贼增扎窄展占张章爪找赵赭浙针珍真枕震镇正郑枝织直志雉中肿重帚朱珠猪竹主煮住注柱砖妆壮追锥缀准卓资子紫棕纵走嘴最遵座啄喳噪榛沼洲足趾鹧
`.trim().split("\n").reduce((map, line) => {
  const [initial, chars] = line.split(":");
  for (const c of chars) map[c] = initial;
  return map;
}, {});

const PINYIN_INITIAL_OVERRIDES = {
  // Bird names use "藏" overwhelmingly in the Tibetan sense (zang), not cang.
  "藏": "z",
  "暗": "a",
  "靛": "d",
  "鹬": "y"
};

const PINYIN_INITIAL_ALIASES = {
  // Accept both common initials for a few ambiguous bird-name characters.
  "藏": ["c"],
  "长": ["z"]
};

const PINYIN_INITIAL_EXTRAS = {
  "埃": "a",
  "岸": "a",
  "澳": "a",
  "捕": "b",
  "辫": "b",
  "垂": "c",
  "鸱": "c",
  "度": "d",
  "德": "d",
  "甸": "d",
  "尔": "e",
  "帆": "f",
  "法": "f",
  "国": "g",
  "岗": "g",
  "果": "g",
  "和": "h",
  "槲": "h",
  "皇": "h",
  "霍": "h",
  "及": "j",
  "疆": "j",
  "距": "j",
  "宽": "k",
  "盔": "k",
  "来": "l",
  "瘤": "l",
  "路": "l",
  "梅": "m",
  "玫": "m",
  "缅": "m",
  "蟆": "m",
  // Bird names only use "泊" in "尼泊尔", which is pronounced "bo".
  "泊": "b",
  "蒲": "p",
  "钳": "q",
  "肉": "r",
  "僧": "s",
  "梢": "s",
  "森": "s",
  "肃": "s",
  "薮": "s",
  "赛": "s",
  "黍": "s",
  "塔": "t",
  "条": "t",
  "梯": "t",
  "韦": "w",
  "休": "x",
  "响": "x",
  "犀": "x",
  "域": "y",
  "幽": "y",
  "侏": "z",
  "支": "z",
  "皱": "z",
  "蛛": "z"
};

function getPinyinInitials(chineseText) {
  let result = "";
  for (const c of chineseText || "") {
    const primary = PINYIN_INITIAL_OVERRIDES[c] || PINYIN_INITIALS[c] || PINYIN_INITIAL_EXTRAS[c] || "";
    result += primary;
  }
  return result;
}

function matchesPinyinInitials(chineseText, query) {
  const normalizedQuery = String(query || "").toLowerCase().replace(/\s/g, "");
  if (!normalizedQuery) return false;

  let index = 0;
  for (const c of chineseText || "") {
    if (index >= normalizedQuery.length) return true;

    const primary = PINYIN_INITIAL_OVERRIDES[c] || PINYIN_INITIALS[c] || PINYIN_INITIAL_EXTRAS[c] || "";
    const options = [primary, ...(PINYIN_INITIAL_ALIASES[c] || [])]
      .filter(Boolean)
      .map(initial => initial.toLowerCase());
    if (!options.includes(normalizedQuery[index])) return false;
    index += 1;
  }

  return index >= normalizedQuery.length;
}

function matchesAnyPinyinInitials(values, query) {
  return (values || []).some(value => matchesPinyinInitials(value, query));
}

function hashString(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) hash = ((hash << 5) + hash) + str.charCodeAt(i);
  return Math.abs(hash >>> 0).toString(36);
}

function base64urlEncode(obj) {
  const json = JSON.stringify(obj);
  const bytes = new TextEncoder().encode(json);
  let binary = "";
  bytes.forEach(b => binary += String.fromCharCode(b));
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64urlDecode(text) {
  const padded = text.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((text.length + 3) % 4);
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}

function formatMonths(months) {
  if (!months || months.length === 0) return "全年";
  if (months.length === 12) return "";
  return months.map(m => `${m}月`).join("、");
}

function hasChineseText(value) {
  return /[\u3400-\u9fff]/.test(String(value || ""));
}

function normalizeOrderZh(orderZh, orderEn) {
  return ORDER_ZH_BY_LATIN[orderZh] || ORDER_ZH_BY_LATIN[orderEn] || orderZh || orderEn || "";
}

function normalizeFamilyZh(familyZh, familyEn) {
  if (hasChineseText(familyZh)) return familyZh;
  return FAMILY_ZH_BY_LATIN[familyZh] || FAMILY_ZH_BY_LATIN[familyEn] || familyZh || familyEn || "";
}

function normalizeSpeciesTaxonomy(species) {
  return {
    ...species,
    order: {
      ...(species.order || {}),
      zh: normalizeOrderZh(species?.order?.zh, species?.order?.en)
    },
    family: {
      ...(species.family || {}),
      zh: normalizeFamilyZh(species?.family?.zh, species?.family?.en)
    }
  };
}

function normalizeTaxonomyFamilies(families, species, orderSortMap) {
  const normalized = [];
  const seen = new Map();
  const nextSortByOrder = new Map();

  (families || []).forEach(family => {
    const orderZh = normalizeOrderZh(family.orderZh, family.orderEn);
    const zh = normalizeFamilyZh(family.zh, family.en);
    const item = { ...family, zh, orderZh };
    if (!seen.has(zh)) {
      seen.set(zh, item);
      normalized.push(item);
    }
    nextSortByOrder.set(orderZh, Math.max(nextSortByOrder.get(orderZh) || 0, item.sortOrder || 0));
  });

  species.forEach(sp => {
    const zh = sp?.family?.zh;
    const orderZh = sp?.order?.zh || "";
    if (!zh || seen.has(zh)) return;
    const baseSort = (orderSortMap.get(orderZh) || 999) * 10;
    const nextSort = Math.max(nextSortByOrder.get(orderZh) || baseSort, baseSort) + 1;
    nextSortByOrder.set(orderZh, nextSort);
    const item = {
      zh,
      en: sp?.family?.en || zh,
      orderZh,
      sortOrder: nextSort
    };
    seen.set(zh, item);
    normalized.push(item);
  });

  normalized.sort((a, b) => (a.sortOrder || 9999) - (b.sortOrder || 9999) || String(a.zh || "").localeCompare(String(b.zh || ""), "zh-Hans-CN"));
  return normalized;
}

function getWorkingImageIndex(images, currentIndex, failedSet) {
  if (!images.length || failedSet.size >= images.length) return -1;
  for (let step = 0; step < images.length; step += 1) {
    const index = (currentIndex + step) % images.length;
    if (!failedSet.has(index)) return index;
  }
  return -1;
}

function getFailedImages(birdId) {
  if (!state.imageFailures[birdId]) state.imageFailures[birdId] = new Set();
  return state.imageFailures[birdId];
}

function markImageFailure(birdId, index) {
  const failedImages = getFailedImages(birdId);
  failedImages.add(index);
  return failedImages;
}

function formatTaxonomy(species) {
  return `${species?.order?.zh || "暂无可靠数据"} > ${species?.family?.zh || "暂无可靠数据"}`;
}

window._unsavedPreview = null;

function showModal({ title, message, buttons }) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
  overlay.innerHTML = $html`
    <div class="modal-box">
      ${title ? `<h3>${esc(title)}</h3>` : ""}
      ${message ? `<p>${esc(message)}</p>` : ""}
      <div class="row" style="justify-content:flex-end;margin-top:12px;">${buttons.map((b, i) => `<button id="modalBtn${i}" class="${b.cls !== undefined ? b.cls : 'secondary'}">${esc(b.label)}</button>`).join("")}</div>
    </div>
  `;
  document.body.appendChild(overlay);
  buttons.forEach((b, i) => {
    overlay.querySelector(`#modalBtn${i}`).onclick = () => { overlay.remove(); if (b.action) b.action(); };
  });
}

async function loadData() {
  const entries = await Promise.all(Object.entries(DATA_FILES).map(async ([key, url]) => {
    const res = await fetch(`${url}?v=${DATA_CACHE_VERSION}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`无法加载 ${url}`);
    return [key, await res.json()];
  }));
  return buildIndexes(Object.fromEntries(entries));
}

function buildIndexes(data) {
  const species = (data.species || []).map(normalizeSpeciesTaxonomy);
  const orders = (data.taxonomy?.orders || []).map(order => ({
    ...order,
    zh: normalizeOrderZh(order.zh, order.en)
  }));
  const orderSortMap = new Map(orders.map(order => [order.zh, order.sortOrder]));
  const families = normalizeTaxonomyFamilies(data.taxonomy?.families || [], species, orderSortMap);
  const taxonomy = { ...(data.taxonomy || {}), orders, families };
  const speciesById = new Map();
  const speciesByChineseName = new Map();
  const speciesByAlias = new Map();
  const speciesByScientificName = new Map();
  const speciesByEnglishName = new Map();
  const occurrencesByBirdId = new Map();
  const taxonomySortMap = new Map();
  const locationsByCode = new Map();

  species.forEach(sp => {
    speciesById.set(sp.birdId, sp);
    speciesByChineseName.set(normalize(sp.chineseName), sp);
    speciesByScientificName.set(normalize(sp.scientificName), sp);
    speciesByEnglishName.set(normalize(sp.englishName), sp);
    (sp.aliases || []).forEach(alias => speciesByAlias.set(normalize(alias), sp));
  });

  data.occurrences.forEach(occ => {
    if (!occurrencesByBirdId.has(occ.birdId)) occurrencesByBirdId.set(occ.birdId, []);
    occurrencesByBirdId.get(occ.birdId).push(occ);
  });

  (taxonomy.orders || []).forEach(o => taxonomySortMap.set(o.zh, o.sortOrder));
  (taxonomy.families || []).forEach(f => taxonomySortMap.set(f.zh, f.sortOrder));
  flattenLocations(data.locations).forEach(loc => locationsByCode.set(loc.code, loc));

  return { ...data, species, taxonomy, speciesById, speciesByChineseName, speciesByAlias, speciesByScientificName, speciesByEnglishName, occurrencesByBirdId, taxonomySortMap, locationsByCode };
}

function flattenLocations(locations, parent = null) {
  return locations.flatMap(loc => [{ ...loc, parent }, ...flattenLocations(loc.children || [], loc)]);
}

const StorageService = {
  getLists() {
    const lists = safeParse(localStorage.getItem(STORAGE_KEYS.lists), []);
    return Array.isArray(lists) ? lists : [];
  },
  saveList(list) {
    try {
      const lists = this.getLists().filter(item => item.listId !== list.listId);
      lists.unshift(list);
      localStorage.setItem(STORAGE_KEYS.lists, JSON.stringify(lists));
    } catch (err) {
      showModal({
        title: "保存失败",
        message: "存储空间不足，请清理一些旧清单后重试。",
        buttons: [{ label: "确定" }]
      });
    }
  },
  getList(listId) { return this.getLists().find(list => list.listId === listId); },
  deleteList(listId) {
    const lists = this.getLists().filter(item => item.listId !== listId);
    localStorage.setItem(STORAGE_KEYS.lists, JSON.stringify(lists));
    localStorage.removeItem(STORAGE_KEYS.checks(listId));
    localStorage.removeItem(STORAGE_KEYS.notes(listId));
  },
  updateList(list) {
    const lists = this.getLists().map(item => item.listId === list.listId ? { ...item, ...list, updatedAt: nowISO() } : item);
    localStorage.setItem(STORAGE_KEYS.lists, JSON.stringify(lists));
  },
  addBirdToList(listId, birdId) {
    const list = this.getList(listId);
    if (!list || list.birdIds.includes(birdId)) return false;
    list.birdIds = [...list.birdIds, birdId];
    list.updatedAt = nowISO();
    this.updateList(list);
    return true;
  },
  removeBirdFromList(listId, birdId) {
    const list = this.getList(listId);
    if (!list || !list.birdIds.includes(birdId)) return false;
    list.birdIds = list.birdIds.filter(id => id !== birdId);
    this.updateList(list);

    const checks = this.getChecks(listId);
    if (checks.checkedBirdIds.includes(birdId)) {
      checks.checkedBirdIds = checks.checkedBirdIds.filter(id => id !== birdId);
      checks.updatedAt = nowISO();
      localStorage.setItem(STORAGE_KEYS.checks(listId), JSON.stringify(checks));
    }

    const notes = this.getNotes(listId);
    if (Object.hasOwn(notes, birdId)) {
      delete notes[birdId];
      localStorage.setItem(STORAGE_KEYS.notes(listId), JSON.stringify(notes));
    }
    return true;
  },
  getChecks(listId) {
    const checks = safeParse(localStorage.getItem(STORAGE_KEYS.checks(listId)), null);
    if (!checks || !Array.isArray(checks.checkedBirdIds)) return { listId, checkedBirdIds: [], updatedAt: nowISO() };
    return checks;
  },
  isChecked(listId, birdId) { return this.getChecks(listId).checkedBirdIds.includes(birdId); },
  toggleCheck(listId, birdId) {
    const checks = this.getChecks(listId);
    checks.checkedBirdIds = checks.checkedBirdIds.includes(birdId)
      ? checks.checkedBirdIds.filter(id => id !== birdId)
      : [...checks.checkedBirdIds, birdId];
    checks.updatedAt = nowISO();
    localStorage.setItem(STORAGE_KEYS.checks(listId), JSON.stringify(checks));
  },
  getNotes(listId) {
    const notes = safeParse(localStorage.getItem(STORAGE_KEYS.notes(listId)), {});
    return notes && typeof notes === "object" && !Array.isArray(notes) ? notes : {};
  },
  saveNote(listId, birdId, text) {
    const notes = this.getNotes(listId);
    const value = text.trim();
    if (value) notes[birdId] = value;
    else delete notes[birdId];
    localStorage.setItem(STORAGE_KEYS.notes(listId), JSON.stringify(notes));
  },
  getLocationHistory() {
    return safeParse(localStorage.getItem("birdPreviewBook:locationHistory"), []);
  },
  addLocationHistory({ name, match }) {
    if (!name) return;
    const history = this.getLocationHistory().filter(h => h.name !== name);
    history.unshift({ name, match });
    localStorage.setItem("birdPreviewBook:locationHistory", JSON.stringify(history.slice(0, 3)));
  }
};

function navigate(hash) { location.hash = hash; }

function dismissTransientPanels() {
  document.querySelectorAll(".note-panel, .modal-overlay").forEach(node => node.remove());
}

function getRoute() {
  const raw = location.hash.slice(1);
  if (!raw) return { name: "home" };
  if (raw.startsWith("share=")) return { name: "share", encoded: raw.slice(6) };
  const [name, queryString] = raw.split("?");
  const params = Object.fromEntries(new URLSearchParams(queryString || ""));
  return { name, params };
}

function render() {
  dismissTransientPanels();
  const route = getRoute();
  state.imageIndex = 0;
  window.scrollTo(0, 0);
  if (route.name === "book" && route.params?.id && _lastRouteName !== "bird") {
    sessionStorage.removeItem(`search:${route.params.id}`);
    sessionStorage.removeItem(`filter:${route.params.id}`);
    sessionStorage.removeItem(`sort:${route.params.id}`);
  }
  _lastRouteName = route.name;
  if (route.name === "new-book") return renderNewBook();
  if (route.name === "import-list") return renderImportList();
  if (route.name === "book") return renderBookDetail(route.params?.id);
  if (route.name === "bird") return renderBirdDetail(route.params?.list, route.params?.bird, route.params?.share === "1");
  if (route.name === "share") return renderShare(route.encoded);
  renderHome();
}

function renderHome() {
  const lists = StorageService.getLists();
  const savedLists = lists.filter(l => l.saved === true);
  app.innerHTML = $html`
    <h1 class="home-title">观鸟预习本</h1>
    <p class="home-subtitle">可能会看到什么鸟？</p>
    <div class="stack">
      <button onclick="navigate('new-book')">推荐清单</button>
      <button class="secondary" onclick="navigate('import-list')">录入清单</button>
    </div>
    <h2 class="section-title">最近清单</h2>
    ${savedLists.length ? savedLists.map(list => `
      <div class="swipe-container">
        <div class="swipe-delete" onclick="deleteRecentList(event, '${esc(list.listId)}')"><span class="swipe-delete-icon" aria-hidden="true"></span></div>
        <div class="card list-card swipe-card" data-listid="${esc(list.listId)}" onclick="navigate('book?id=${esc(list.listId)}')">
          <div style="flex:1;">
            <strong>${esc(list.title)}</strong>
            <div class="muted small">${formatMonths(list.months) ? `${esc(formatMonths(list.months))} · ` : ''}${list.birdIds.length} 种</div>
          </div>
        </div>
      </div>
    `).join("") : `<div class="card muted">还没有本地清单</div>`}
  `;
  setupSwipeCards();
}

function deleteRecentList(event, listId) {
  event.stopPropagation();
  showModal({
    title: "确认删除",
    message: "确定删除这个清单？已观察和笔记也会一并删除。",
    buttons: [
      { label: "取消", action: () => resetAllSwipes() },
      { label: "删除", cls: "danger", action: () => { StorageService.deleteList(listId); render(); } }
    ]
  });
}

function resetAllSwipes(exceptCard = null) {
  document.querySelectorAll(".swipe-card").forEach(el => {
    if (el !== exceptCard) el.style.transform = "translateX(0)";
  });
}

function setupSwipeCards() {
  document.querySelectorAll(".swipe-container").forEach(container => {
    const card = container.querySelector(".swipe-card");
    const deleteAction = container.querySelector(".swipe-delete");
    const swipeWidth = Math.max(48, Math.round(deleteAction?.getBoundingClientRect().width || 52));
    const dragThreshold = 10;
    const axisLockOffset = 6;
    let startX = 0;
    let startY = 0;
    let startSwipeX = 0;
    let lastDx = 0;
    let moved = false;
    let suppressClick = false;
    let mouseDragging = false;
    let swipeAxis = "";

    function reset() { card.style.transform = "translateX(0)"; }
    function currentSwipeX() { return parseInt(card.style.transform.replace(/[^-\d]/g, "")) || 0; }
    function setSwipeX(nextX) { card.style.transform = `translateX(${Math.min(0, Math.max(nextX, -swipeWidth))}px)`; }
    function detectSwipeAxis(dx, dy) {
      if (swipeAxis) return swipeAxis;
      const absX = Math.abs(dx);
      const absY = Math.abs(dy);
      if (absX < dragThreshold && absY < dragThreshold) return "";
      if (absY > absX + axisLockOffset) {
        swipeAxis = "vertical";
        return swipeAxis;
      }
      if (absX > absY + axisLockOffset) {
        swipeAxis = "horizontal";
        return swipeAxis;
      }
      return "";
    }
    function finalizeSwipe() {
      if (!moved) return;
      if (lastDx > dragThreshold) reset();
      else if (currentSwipeX() < -(swipeWidth / 2)) card.style.transform = `translateX(-${swipeWidth}px)`;
      else reset();
      suppressClick = true;
      setTimeout(() => { suppressClick = false; }, 0);
    }

    card.addEventListener("touchstart", e => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      startSwipeX = currentSwipeX();
      lastDx = 0;
      moved = false;
      swipeAxis = "";
      resetAllSwipes(card);
    }, { passive: true });

    card.addEventListener("touchmove", e => {
      const dx = e.touches[0].clientX - startX;
      const dy = e.touches[0].clientY - startY;
      const axis = detectSwipeAxis(dx, dy);
      if (axis !== "horizontal") return;
      moved = true;
      lastDx = dx;
      if (dx > 0) {
        reset();
        return;
      }
      const nextX = startSwipeX + dx;
      if (nextX <= 0) {
        setSwipeX(nextX);
      }
    }, { passive: true });

    card.addEventListener("touchend", () => {
      finalizeSwipe();
    });

    card.addEventListener("pointerdown", e => {
      if (e.pointerType !== "mouse" || e.button !== 0) return;
      startX = e.clientX;
      startY = e.clientY;
      startSwipeX = currentSwipeX();
      lastDx = 0;
      moved = false;
      mouseDragging = true;
      suppressClick = false;
      swipeAxis = "";
      resetAllSwipes(card);
      card.setPointerCapture(e.pointerId);
    });

    card.addEventListener("pointermove", e => {
      if (!mouseDragging || e.pointerType !== "mouse") return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      const axis = detectSwipeAxis(dx, dy);
      if (axis !== "horizontal") return;
      moved = true;
      lastDx = dx;
      card.classList.add("swiping");
      if (dx > 0) {
        reset();
        return;
      }
      const nextX = startSwipeX + dx;
      if (nextX <= 0) {
        setSwipeX(nextX);
      }
    });

    function finishMouseSwipe(e) {
      if (!mouseDragging || e.pointerType !== "mouse") return;
      mouseDragging = false;
      card.classList.remove("swiping");
      if (card.hasPointerCapture(e.pointerId)) card.releasePointerCapture(e.pointerId);
      finalizeSwipe();
    }

    card.addEventListener("pointerup", finishMouseSwipe);
    card.addEventListener("pointercancel", finishMouseSwipe);
    card.addEventListener("dragstart", e => e.preventDefault());

    card.addEventListener("click", e => {
      if (suppressClick) {
        e.stopPropagation();
        e.preventDefault();
        return;
      }
      const currentX = currentSwipeX();
      if (currentX < -40) { e.stopPropagation(); e.preventDefault(); resetAllSwipes(); }
    });
  });
}

let _locationMatch = null;
let _currentAudio = null;

function renderNewBook() {
  const orderCheckboxesHtml = (appData.taxonomy.orders || []).map(o => `<label class="dropdown-item"><input type="checkbox" class="order-check" value="${esc(o.zh)}" checked> ${esc(o.zh)}</label>`).join("");
  _locationMatch = null;
  window._unsavedPreview = null;

  app.innerHTML = $html`
    ${header("新增预习本")}
    <div class="card stack">
      <div class="field"><label>地点</label>
        <input id="locInput" placeholder="输入省、市、区县或具体观鸟地点" autocomplete="off">
        <div id="locHistory" class="loc-history" style="display:none;"></div>
        <div id="locSuggest" class="search-results" style="max-height:200px;"></div>
      </div>

      <div class="field"><label>分类</label>
        <div id="orderDropdown" class="dropdown-trigger">
          <span id="orderDropdownLabel">全部目</span>
          <span class="dropdown-arrow">▾</span>
        </div>
        <div id="orderDropdownPanel" class="dropdown-panel" style="display:none;">
          <label class="dropdown-item"><input type="checkbox" id="orderAllCheck" checked> 全部目</label>
          <div class="dropdown-divider"></div>
          ${orderCheckboxesHtml}
        </div>
      </div>
      <div class="field"><label>预习本名称</label><input id="title" value=""></div>
      <button id="generate">生成预习本</button>
      <div id="newBookMsg" class="small"></div>
    </div>
  `;

  const backBtn = document.querySelector(".page-header .ghost");
  backBtn.setAttribute("onclick", "handleNewBookBack()");

  const locInput = document.querySelector("#locInput");
  const locHistory = document.querySelector("#locHistory");
  const locSuggest = document.querySelector("#locSuggest");
  const title = document.querySelector("#title");

  locInput.onfocus = () => {
    const history = StorageService.getLocationHistory();
    if (history.length) {
      locHistory.style.display = "block";
      locHistory.innerHTML = history.map(h =>
        `<div class="add-bird-item" data-name="${esc(h.name)}" data-match="${esc(h.match)}"><span>📍 ${esc(h.name)}</span></div>`
      ).join("");
      locHistory.querySelectorAll(".add-bird-item").forEach(item => {
        item.onclick = () => {
          _locationMatch = safeParse(item.dataset.match, null);
          locInput.value = item.dataset.name;
          locHistory.style.display = "none";
          locSuggest.innerHTML = "";
          syncTitle();
        };
      });
    }
  };
  locInput.onblur = () => { setTimeout(() => { locHistory.style.display = "none"; }, 200); };

  const orderDropdown = document.querySelector("#orderDropdown");
  const orderDropdownPanel = document.querySelector("#orderDropdownPanel");
  const orderAllCheck = document.querySelector("#orderAllCheck");
  const orderChecks = document.querySelectorAll(".order-check");

  function updateOrderDropdownLabel() {
    const selected = [...orderChecks].filter(c => c.checked);
    const total = orderChecks.length;
    document.querySelector("#orderDropdownLabel").textContent =
      (selected.length === total || selected.length === 0) ? "全部目" : `已选${selected.length}个目`;
  }

  function syncTitle() {
    const locName = _locationMatch ? _locationMatch.name : (locInput.value.trim() || "全国");
    const allChecked = [...orderChecks].every(c => c.checked);
    if (allChecked) {
      title.value = locName;
    } else {
      const selected = [...orderChecks].filter(c => c.checked).map(c => c.value);
      title.value = `${locName} · ${selected.join("、")}`;
    }
  }

  function buildFilters() {
    const allChecked = [...orderChecks].every(c => c.checked);
    return { orders: allChecked ? [] : [...orderChecks].filter(c => c.checked).map(c => c.value), families: [], habitats: [] };
  }

  orderDropdown.onclick = (e) => {
    const isOpening = orderDropdownPanel.style.display === "none";
    orderDropdownPanel.style.display = isOpening ? "block" : "none";
    if (isOpening) {
      setTimeout(() => {
        document.addEventListener("click", function closeOrderDropdown(ev) {
          if (!orderDropdownPanel.contains(ev.target) && !orderDropdown.contains(ev.target)) {
            orderDropdownPanel.style.display = "none";
            document.removeEventListener("click", closeOrderDropdown);
          }
        });
      }, 0);
    }
    e.stopPropagation();
  };

  orderAllCheck.onchange = () => {
    orderChecks.forEach(c => c.checked = orderAllCheck.checked);
    updateOrderDropdownLabel();
    syncTitle();
  };

  orderChecks.forEach(c => {
    c.onchange = () => {
      const allChecked = [...orderChecks].every(ch => ch.checked);
      const noneChecked = [...orderChecks].every(ch => !ch.checked);
      orderAllCheck.checked = allChecked || noneChecked;
      if (noneChecked) { orderChecks.forEach(ch => ch.checked = true); orderAllCheck.checked = true; }
      updateOrderDropdownLabel();
      syncTitle();
    };
  });

  syncTitle();

  locInput.oninput = () => {
    _locationMatch = null;
    const q = normalize(locInput.value);
    if (!q) { locSuggest.innerHTML = ""; syncTitle(); return; }
    const allLocs = flattenLocations(appData.locations);
    const matches = allLocs.filter(loc => normalize(loc.name).includes(q) || normalize(loc.parent?.name || "").includes(q)).slice(0, 8);
    locSuggest.innerHTML = matches.map(loc => `<div class="add-bird-item" data-code="${esc(loc.code)}" data-name="${esc(loc.name)}" data-parent="${esc(loc.parent?.name || "")}"><strong>${esc(loc.name)}</strong> <span class="muted">${esc(loc.parent?.name || "")}</span></div>`).join("");
    syncTitle();
  };

  locSuggest.onclick = e => {
    const item = e.target.closest(".add-bird-item");
    if (!item) return;
    const code = item.dataset.code;
    const name = item.dataset.name;
    const parent = item.dataset.parent;
    const loc = appData.locationsByCode.get(code);
    _locationMatch = { code, name, parentName: parent, loc };
    locInput.value = parent ? `${parent} ${name}` : name;
    locSuggest.innerHTML = "";
    syncTitle();
  };

  document.querySelector("#generate").onclick = () => {
    const location = buildLocationFromMatch(locInput.value.trim());
    const months = ALL_MONTHS;
    const filters = buildFilters();
    const birdIds = generateRecommendedList({ location, months, filters });
    if (!birdIds.length) {
      document.querySelector("#newBookMsg").innerHTML = `<span class="error">暂无符合条件且有可靠记录的鸟种。</span>`;
      return;
    }
    document.querySelector("#newBookMsg").innerHTML = "";
    StorageService.addLocationHistory({ name: locInput.value.trim(), match: JSON.stringify(_locationMatch) });
    saveGeneratedList({ location, months, filters, birdIds, title: title.value.trim() });
  };
}

function handleNewBookBack() {
  navigate("home");
}

function saveGeneratedList(p) {
  if (!p) return;
  const createdAt = nowISO();
  const list = {
    listId: `list_${hashString(JSON.stringify({ location: p.location, months: p.months, filters: p.filters, birdIds: p.birdIds, createdAt }))}`,
    title: p.title || `${p.location?.provinceName || "全国"}${formatMonths(p.months) ? ` · ${formatMonths(p.months)}` : ''}`,
    mode: "recommended",
    location: p.location,
    months: p.months,
    filters: p.filters,
    birdIds: p.birdIds,
    createdAt,
    updatedAt: createdAt,
    saved: false,
    dataVersion: appData.metadata.dataVersion
  };
  StorageService.saveList(list);
  window._unsavedPreview = null;
  navigate(`book?id=${list.listId}`);
}

function buildLocationFromMatch(freeText) {
  if (_locationMatch) {
    const lm = _locationMatch.loc;
    if (lm.level === "province") return { provinceCode: lm.code, provinceName: lm.name, cityCode: "", cityName: "", districtCode: "", districtName: "" };
    if (lm.level === "city") return { provinceCode: lm.parent?.code || "", provinceName: lm.parent?.name || "", cityCode: lm.code, cityName: lm.name, districtCode: "", districtName: "" };
    if (lm.level === "district") return { provinceCode: lm.parent?.parent?.code || "", provinceName: lm.parent?.parent?.name || "", cityCode: lm.parent?.code || "", cityName: lm.parent?.name || "", districtCode: lm.code, districtName: lm.name };
  }
  return { provinceCode: "", provinceName: freeText || "", cityCode: "", cityName: "", districtCode: "", districtName: "" };
}

function generateRecommendedList({ location, months, filters }) {
  const best = new Map();
  const hasLocation = location?.provinceCode || location?.cityCode || location?.districtCode;

  // Phase 1: match species via occurrence records
  appData.occurrences.forEach(occ => {
    const sp = appData.speciesById.get(occ.birdId);
    if (!sp) return;
    if (!occ.sourceRefs?.length) return;
    if (!["high", "medium"].includes(occ.reliability)) return;
    if (!occ.months?.some(m => months.includes(m))) return;
    if (!matchLocation(occ, location)) return;
    if (filters.orders.length && !filters.orders.includes(sp.order?.zh)) return;
    if (filters.families.length && !filters.families.includes(sp.family?.zh)) return;
    if (filters.habitats.length && !filters.habitats.some(h => occ.habitats?.includes(h))) return;
    const prev = best.get(occ.birdId);
    if (!prev || occurrenceRank(occ) > occurrenceRank(prev)) best.set(occ.birdId, occ);
  });

  // Phase 2: fill gaps with province distribution for species without occurrence records
  appData.speciesById.forEach((sp, birdId) => {
    if (best.has(birdId)) return;
    if (filters.orders.length && !filters.orders.includes(sp.order?.zh)) return;
    if (filters.families.length && !filters.families.includes(sp.family?.zh)) return;
    if (hasLocation) {
      const prov = normalizeProvince(appData.locationsByCode.get(location.provinceCode)?.name);
      if (!prov) return;
      if (!sp.provinceDistribution?.some(p => normalizeProvince(p) === prov)) return;
    }
    best.set(birdId, null);
  });

  return [...best.keys()].sort((a, b) => sortBirdIds(a, b, best));
}

function normalizeProvince(name) {
  if (!name) return "";
  let normalized = name.trim();
  while (normalized) {
    const next = normalized.replace(/(?:特别行政区|自治区|维吾尔|壮族|回族|省|市)$/, "").trim();
    if (next === normalized) break;
    normalized = next;
  }
  return normalized;
}

function matchLocation(occ, location) {
  if (!occ.locationCode || occ.locationLevel === "national") return true;
  if (!location.provinceCode && !location.cityCode && !location.districtCode) return true;
  if (location.districtCode && occ.locationCode === location.districtCode) return true;
  if (location.cityCode && occ.locationCode === location.cityCode) return true;
  if (location.provinceCode && occ.locationCode === location.provinceCode) return true;
  return false;
}

function occurrenceRank(occ) {
  const levelRank = { district: 3, city: 2, province: 1 }[occ.locationLevel] || 0;
  const reliabilityRank = occ.reliability === "high" ? 2 : 1;
  return levelRank * 100 + reliabilityRank * 10;
}

function sortBirdIds(a, b, occurrenceMap = null) {
  const sa = appData.speciesById.get(a);
  const sb = appData.speciesById.get(b);
  const ta = appData.taxonomySortMap.get(sa?.order?.zh) || 999;
  const tb = appData.taxonomySortMap.get(sb?.order?.zh) || 999;
  if (ta !== tb) return ta - tb;
  const fa = appData.taxonomySortMap.get(sa?.family?.zh) || 999;
  const fb = appData.taxonomySortMap.get(sb?.family?.zh) || 999;
  if (fa !== fb) return fa - fb;
  return (sa?.chineseName || "").localeCompare(sb?.chineseName || "", "zh-Hans-CN");
}

function renderImportList() {
  app.innerHTML = $html`
    ${header("录入清单")}
    <div class="card stack">
      <p class="muted">支持手动输入或批量导入</p>
      <div class="small muted">批量导入格式要求：可每行输入一种鸟；也可用逗号或顿号分隔多个鸟名；支持中文名、别名、学名或英文名；可直接从表格复制一列鸟名。</div>
      <textarea id="importText" placeholder="红嘴蓝鹊、白头鹎、普通翠鸟"></textarea>
      <div class="row">
        <button class="secondary" id="demo">使用示例</button>
        <button class="danger" id="clear">清空</button>
      </div>
      <button id="match">开始匹配</button>
      <div id="matchResults"></div>
      <div class="field"><label>预习本名称</label><input id="importTitle" value="自定义预习本 · 0种"></div>
      <button id="createImport">生成预习本</button>
      <div id="importMsg" class="small"></div>
    </div>
  `;
  document.querySelector("#demo").onclick = () => document.querySelector("#importText").value = "红嘴蓝鹊、白头鹎、普通翠鸟";
  document.querySelector("#clear").onclick = () => { document.querySelector("#importText").value = ""; document.querySelector("#matchResults").innerHTML = ""; };
  document.querySelector("#match").onclick = runImportMatch;
  document.querySelector("#createImport").onclick = createImportList;
}

function parseImportText(text) {
  return [...new Set(text.split(/[\n,，、]/).map(item => item.trim()).filter(Boolean))];
}

function matchInputName(input) {
  const key = normalize(input);
  const exact = appData.speciesByChineseName.get(key) || appData.speciesByAlias.get(key) || appData.speciesByScientificName.get(key) || appData.speciesByEnglishName.get(key);
  if (exact) return { input, status: "matched", species: exact };
  const candidates = appData.species.filter(sp => {
    const cn = normalize(sp.chineseName);
    if (cn.includes(key) || key.includes(cn)) return true;
    const keySet = new Set([...key]);
    const cnSet = new Set([...cn]);
    const overlap = [...keySet].filter(c => cnSet.has(c)).length;
    const minLen = Math.min(key.length, cn.length);
    return overlap >= Math.max(2, Math.ceil(minLen * 0.5));
  }).slice(0, 5);
  if (candidates.length) return { input, status: "candidate", candidates, selected: null };
  return { input, status: "unmatched" };
}

function runImportMatch() {
  state.matchResults = parseImportText(document.querySelector("#importText").value).map(matchInputName);
  renderMatchResults();
}

function renderMatchResults() {
  const box = document.querySelector("#matchResults");
  const matchedCount = getImportBirdIds().length;
  document.querySelector("#importTitle").value = `自定义预习本 · ${matchedCount}种`;
  box.innerHTML = state.matchResults.map((result, idx) => {
    if (result.status === "matched") return `<div class="match-item success">✓ ${esc(result.input)} → ${esc(result.species.chineseName)}</div>`;
    if (result.status === "candidate") return `<div class="match-item">? ${esc(result.input)}<br>${result.candidates.map(sp => `<button class="secondary pill" onclick="selectCandidate(${idx}, '${sp.birdId}')">${esc(sp.chineseName)}</button>`).join("")}</div>`;
    return `<div class="match-item error">× ${esc(result.input)} → 未在本地鸟种库中找到</div>`;
  }).join("");
}

function selectCandidate(index, birdId) {
  const species = appData.speciesById.get(birdId);
  state.matchResults[index] = { input: state.matchResults[index].input, status: "matched", species };
  renderMatchResults();
}

function getImportBirdIds() {
  return [...new Set(state.matchResults.filter(r => r.status === "matched").map(r => r.species.birdId))];
}

function createImportList() {
  const birdIds = getImportBirdIds();
  if (!birdIds.length) {
    document.querySelector("#importMsg").innerHTML = `<span class="error">还没有可加入预习本的鸟种，请先输入并匹配鸟名。</span>`;
    return;
  }
  const createdAt = nowISO();
  const list = { listId: `import_${hashString(JSON.stringify({ birdIds, createdAt }))}`, title: document.querySelector("#importTitle").value.trim() || `自定义预习本 · ${birdIds.length}种`, mode: "import", location: null, months: ALL_MONTHS, filters: { orders: [], families: [], habitats: [] }, birdIds, createdAt, updatedAt: createdAt, saved: false, dataVersion: appData.metadata.dataVersion };
  StorageService.saveList(list);
  navigate(`book?id=${list.listId}`);
}

function getListViewState(listId) {
  return {
    filter: sessionStorage.getItem(`filter:${listId}`) || "all",
    sort: sessionStorage.getItem(`sort:${listId}`) || "taxonomy",
    search: sessionStorage.getItem(`search:${listId}`) || ""
  };
}

function cacheVisibleBirds(listId, birdIds) {
  sessionStorage.setItem(`visibleBirds:${listId}`, JSON.stringify(birdIds || []));
}

function getCachedVisibleBirds(list) {
  const cached = safeParse(sessionStorage.getItem(`visibleBirds:${list.listId}`), []);
  if (!Array.isArray(cached) || !cached.length) return [];
  const available = new Set(list.birdIds || []);
  return cached.filter(id => available.has(id));
}

function renderBookDetail(listId, sharePayload = null) {
  const list = sharePayload || StorageService.getList(listId);
  if (!list) return renderError("当前清单不存在。", "返回首页");
  const isShare = listId?.startsWith("share_");
  const checks = StorageService.getChecks(list.listId);
  const { filter, sort, search } = getListViewState(list.listId);
  const birds = filterSortBirds(list.birdIds, list.listId, { filter, sort, search }, list);
  cacheVisibleBirds(list.listId, birds);
  const sortOptions = [
    { value: "taxonomy", label: "按分类" },
    { value: "name", label: "按中文名" }
  ];
  const sortHTML = sortOptions.map(o =>
    `<option value="${o.value}">${esc(o.label)}</option>`
  ).join("");
  const wasSearchFocused = document.activeElement?.id === "search";
  app.innerHTML = $html`
    <div class="page-header">
      <button class="ghost" onclick="handleBookBack('${esc(list.listId)}')">返回</button>
      <div style="display:flex;align-items:center;gap:6px;">
        <h1 class="page-title" style="margin:0;">${esc(list.title)}</h1>
        ${isShare ? `` : `<button class="ghost small" onclick="renameList('${esc(list.listId)}')" title="重命名">✎</button>`}
      </div>
      ${isShare ? `<span></span>` : `<div style="display:flex;align-items:center;gap:6px;">${list.saved ? `` : `<button class="ghost" onclick="saveBookList('${esc(list.listId)}')">保存预习本</button>`}<button class="ghost" onclick="shareList('${esc(list.listId)}')">分享</button></div>`}
    </div>
    <div class="card">
      <strong>已观察 ${checks.checkedBirdIds.length} / 共 ${list.birdIds.length} 种</strong>
      <div style="display:flex;gap:8px;margin-top:12px;margin-bottom:12px;">
        <input id="search" placeholder="搜索鸟名（支持拼音首字母）" value="${esc(search)}" style="flex:1;min-width:0;">
        <select id="filter" style="flex-shrink:0;width:70px;"><option value="all">全部</option><option value="unchecked">未观察</option><option value="checked">已观察</option></select>
        <select id="sort" style="flex-shrink:0;width:80px;">${sortHTML}</select>
      </div>
      ${birds.length ? birds.map((id, index) => birdRow(list, id, isShare, index === birds.length - 1)).join("") : `<p class="muted">没有符合条件的鸟种。</p>`}
    </div>
    ${isShare ? `<button class="secondary" style="width:100%;" onclick="cloneShareList('${esc(list.listId)}')">复制为我的清单（可编辑）</button>` : ``}
    ${isShare ? `` : `<button class="fab" onclick="showAddBirdModal('${esc(list.listId)}')" title="添加鸟种">+</button>`}
  `;
  if (!isShare) setupSwipeCards();
  document.querySelector("#filter").value = filter;
  document.querySelector("#sort").value = sort;
  document.querySelector("#search").oninput = e => { sessionStorage.setItem(`search:${list.listId}`, e.target.value); renderBookDetail(list.listId, isShare ? list : null); };
  document.querySelector("#filter").onchange = e => { sessionStorage.setItem(`filter:${list.listId}`, e.target.value); renderBookDetail(list.listId, isShare ? list : null); };
  document.querySelector("#sort").onchange = e => { sessionStorage.setItem(`sort:${list.listId}`, e.target.value); renderBookDetail(list.listId, isShare ? list : null); };
  if (wasSearchFocused) {
    const searchInput = document.querySelector("#search");
    if (searchInput) {
      searchInput.focus();
      searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
    }
  }
}

function handleBookBack(listId) {
  const list = StorageService.getList(listId);
  if (!list || list.saved === true) {
    navigate("home");
    return;
  }
  showModal({
    title: "确认返回",
    message: "你还没有保存这个预习本",
    buttons: [
      { label: "取消" },
      { label: "不保存", cls: "danger", action: () => { StorageService.deleteList(listId); navigate("home"); } },
      { label: "保存", action: () => { saveBookList(listId); navigate("home"); } }
    ]
  });
}

function saveBookList(listId) {
  const list = StorageService.getList(listId);
  if (!list) return;
  StorageService.updateList({ ...list, saved: true });
  render();
}

function birdRow(list, birdId, isShare, isLast = false) {
  const sp = appData.speciesById.get(birdId);
  if (!sp) return "";
  const media = appData.media[birdId] || { images: [] };
  const imgIndex = getWorkingImageIndex(media.images || [], 0, getFailedImages(birdId));
  const img = imgIndex === -1 ? "" : media.images?.[imgIndex]?.url;
  const checked = StorageService.isChecked(list.listId, birdId);
  const shareParam = isShare ? "&share=1" : "";
  const navTarget = `bird?list=${esc(list.listId)}&bird=${esc(birdId)}${shareParam}`;
  const rowHtml = `<div class="bird-row ${checked ? "checked-row" : ""} ${isLast ? "bird-row-last" : ""}" onclick="navigate('${navTarget}')">
    ${img ? `<img class="thumb" src="${esc(img)}" alt="${esc(sp.chineseName)}" data-image-index="${imgIndex}" onerror="handleThumbImageError(this, '${esc(birdId)}')">` : `<div class="thumb">🐦</div>`}
    <div class="bird-main">
      <div class="bird-name">${esc(sp.chineseName)}</div>
      <div class="bird-taxonomy">${esc(formatTaxonomy(sp))}</div>
    </div>
    <div class="check-zone" onclick="event.stopPropagation(); toggleAndRefresh('${esc(list.listId)}','${esc(birdId)}')">${birdCheckIcon(checked)}</div>
  </div>`;
  if (isShare) return rowHtml;
  return `<div class="swipe-container bird-swipe-container">
    <div class="swipe-delete bird-swipe-delete" onclick="deleteBirdFromList(event, '${esc(list.listId)}', '${esc(birdId)}')"><span class="swipe-delete-icon" aria-hidden="true"></span></div>
    <div class="swipe-card bird-swipe-card">${rowHtml}</div>
  </div>`;
}

function filterSortBirds(birdIds, listId, { filter, sort, search }, list) {
  const query = normalize(search);
  return birdIds.filter(id => {
    const checked = StorageService.isChecked(listId, id);
    if (filter === "checked" && !checked) return false;
    if (filter === "unchecked" && checked) return false;
    if (!query) return true;
    const sp = appData.speciesById.get(id);
    const pinyinQuery = query.toLowerCase().replace(/\s/g, "");
    if (pinyinQuery && matchesAnyPinyinInitials([sp?.chineseName, ...(sp?.aliases || [])], pinyinQuery)) return true;
    const hay = [sp?.chineseName, sp?.scientificName, sp?.englishName, ...(sp?.aliases || [])].map(normalize).join(" ");
    return hay.includes(query);
  }).sort((a, b) => {
    if (sort === "name") return (appData.speciesById.get(a)?.chineseName || "").localeCompare(appData.speciesById.get(b)?.chineseName || "", "zh-Hans-CN");
    return sortBirdIds(a, b);
  });
}

function toggleAndRefresh(listId, birdId) {
  StorageService.toggleCheck(listId, birdId);
  render();
}

function deleteBirdFromList(event, listId, birdId) {
  event.stopPropagation();
  const sp = appData.speciesById.get(birdId);
  showModal({
    title: "确认移除",
    message: `确定从当前清单移除“${sp?.chineseName || "该鸟种"}”？已观察状态和笔记也会一并删除。`,
    buttons: [
      { label: "取消", action: () => resetAllSwipes() },
      {
        label: "删除",
        cls: "danger",
        action: () => {
          StorageService.removeBirdFromList(listId, birdId);
          render();
        }
      }
    ]
  });
}

const IUCN_BADGES = {
  critically_endangered: { text: "CR", label: "极危", cls: "iucn-badge-cr" },
  endangered:           { text: "EN", label: "濒危", cls: "iucn-badge-en" },
  vulnerable:           { text: "VU", label: "易危", cls: "iucn-badge-vu" },
  near_threatened:      { text: "NT", label: "近危", cls: "iucn-badge-nt" },
};

const DETAIL_TAG_LABELS = {
  endemic: "中国特有种",
  breeding_endemic: "仅在中国繁育",
  near_endemic: "近乎中国特有",
  rare: "稀见/偶见",
  introduced: "外来物种",
  extirpated: "消失",
  exotic: "非本土宠物种",
};

function renderIucnBadge(sp) {
  const badge = IUCN_BADGES[sp.iucnStatus];
  if (!badge) return "";
  return `<span class="iucn-badge ${badge.cls}" title="IUCN ${esc(badge.label)}" aria-label="IUCN ${esc(badge.label)}">${badge.text}</span>`;
}

function renderDetailTags(sp) {
  const tags = [];
  if (sp.endemism && DETAIL_TAG_LABELS[sp.endemism]) {
    tags.push(DETAIL_TAG_LABELS[sp.endemism]);
  }
  if (sp.occurrenceType && DETAIL_TAG_LABELS[sp.occurrenceType]) {
    tags.push(DETAIL_TAG_LABELS[sp.occurrenceType]);
  }
  if (!tags.length) return "";
  return `<p class="detail-line detail-tags">${tags.map(esc).join("、")}</p>`;
}

function renderDetailHeroImage(sp, image, listId, birdId, isShare) {
  return image
    ? `<img src="${esc(image.url)}" alt="${esc(sp.chineseName)}" onerror="handleBirdImageError('${esc(listId)}', '${esc(birdId)}', ${isShare})">`
    : `<div><div style="font-size:58px;text-align:center;">🐦</div><div class="muted">暂无可靠图片</div></div>`;
}

function renderDetailImageCounter(images = [], imageIndex) {
  if (!images.length) return "0/0";
  if (imageIndex === -1) return `0/${images.length}`;
  return `${imageIndex + 1}/${images.length}`;
}

function updateBirdDetailImage(listId, birdId, isShare) {
  const sp = appData.speciesById.get(birdId);
  const media = appData.media[birdId] || { images: [] };
  const failedImages = state.imageFailures[birdId] || new Set();
  const workingImageIndex = getWorkingImageIndex(media.images || [], state.imageIndex, failedImages);
  if (workingImageIndex !== -1 && workingImageIndex !== state.imageIndex) state.imageIndex = workingImageIndex;
  const image = workingImageIndex === -1 ? null : media.images?.[workingImageIndex];
  const heroImage = document.querySelector(".hero-image");
  const imageCounter = document.querySelector('[data-role="image-counter"]');

  if (!heroImage || !imageCounter || !sp) {
    renderBirdDetail(listId, birdId, isShare);
    return;
  }

  heroImage.innerHTML = renderDetailHeroImage(sp, image, listId, birdId, isShare);
  imageCounter.textContent = renderDetailImageCounter(media.images || [], workingImageIndex);
}

function renderBirdDetail(listId, birdId, isShare) {
  const list = isShare ? getShareListFromSession(listId) : StorageService.getList(listId);
  const sp = appData.speciesById.get(birdId);
  if (!list || !sp) return renderError("当前鸟种资料不存在。", "返回首页");
  const viewState = getListViewState(list.listId);
  const visibleBirds = getCachedVisibleBirds(list);
  const sortedBirds = filterSortBirds(list.birdIds, list.listId, { ...viewState, filter: "all", search: "" }, list);
  const detailBirds = visibleBirds.includes(birdId) ? visibleBirds : sortedBirds;
  const media = appData.media[birdId] || { images: [], sounds: [] };
  const identification = appData.identification[birdId] || {};
  const similar = appData.similar[birdId] || [];
  const checked = StorageService.isChecked(list.listId, birdId);
  const notes = StorageService.getNotes(list.listId);
  const index = Math.max(0, detailBirds.indexOf(birdId));
  const failedImages = state.imageFailures[birdId] || new Set();
  const workingImageIndex = getWorkingImageIndex(media.images || [], state.imageIndex, failedImages);
  if (workingImageIndex !== -1 && workingImageIndex !== state.imageIndex) state.imageIndex = workingImageIndex;
  const image = workingImageIndex === -1 ? null : media.images?.[workingImageIndex];
  const hasDist = !!(sp?.distribution || identification?.wikipediaDistribution || (identification?.wikipediaSummary && extractDistFromWiki(toSimplified(identification.wikipediaSummary))) || (sp?.description && extractDistFromWiki(toSimplified(sp.description))));

  app.innerHTML = $html`
    <div class="page-header">
      <button class="ghost" onclick="${isShare ? `renderBookDetail('${esc(list.listId)}', getShareListFromSession('${esc(list.listId)}'))` : `navigate('book?id=${esc(list.listId)}')`}">返回清单</button>
      <strong>${index + 1}/${detailBirds.length}</strong>
      <button class="ghost" onclick="openNotePanel('${esc(list.listId)}','${esc(birdId)}')">笔记${notes[birdId] ? "•" : ""}</button>
      <button class="ghost check-zone" onclick="toggleAndRefresh('${esc(list.listId)}','${esc(birdId)}')">${birdCheckIcon(checked)}</button>
    </div>
    <div class="detail-name">
      <h1>${esc(sp.chineseName)}${renderIucnBadge(sp)}</h1>
      <div class="taxonomy-left">${esc(formatTaxonomy(sp))}</div>
      <div class="name-right">${esc(sp.englishName || "暂无可靠数据")}</div>
    </div>
    <div class="hero-image">${renderDetailHeroImage(sp, image, listId, birdId, isShare)}</div>
    <div class="image-nav">${media.images?.length > 1 ? `<button class="ghost" onclick="changeImage(-1, '${esc(listId)}', '${esc(birdId)}', ${isShare})">◀</button>` : `<span></span>`}<span data-role="image-counter">${renderDetailImageCounter(media.images || [], workingImageIndex)}</span>${media.images?.length > 1 ? `<button class="ghost" onclick="changeImage(1, '${esc(listId)}', '${esc(birdId)}', ${isShare})">▶</button>` : `<span></span>`}</div>
    <details open><summary>鸣声</summary>${renderSounds(media.sounds)}</details>
    <details open><summary>基本信息</summary>${renderDescription(sp, identification)}</details>
    <details${hasDist ? " open" : ""}><summary>分布信息</summary>${renderDistribution(media.rangeMap, sp, identification)}</details>
    <details><summary>资料来源</summary>${renderSources(sp, media, identification)}</details>
    <div class="bottom-nav">
      <button class="secondary" ${index <= 0 ? "disabled" : ""} onclick="goBird('${esc(list.listId)}', '${esc(detailBirds[index - 1])}', ${isShare})">上一种</button>
      <button ${index >= detailBirds.length - 1 ? "disabled" : ""} onclick="goBird('${esc(list.listId)}', '${esc(detailBirds[index + 1])}', ${isShare})">下一种</button>
    </div>
  `;
  document.querySelectorAll("audio").forEach(audio => {
    audio.addEventListener("play", function() {
      if (_currentAudio && _currentAudio !== this) _currentAudio.pause();
      _currentAudio = this;
    });
    audio.addEventListener("ended", function() {
      if (_currentAudio === this) _currentAudio = null;
    });
  });
}

function renderSounds(sounds = []) {
  if (!sounds.length) return `<p class="muted">暂无可靠鸣声</p>`;
  const audios = sounds.map((s, i) =>
    `<audio controls controlsList="nodownload noplaybackrate" src="${esc(s.url)}"${i > 0 ? ' style="margin-top:8px"' : ''}></audio>`
  ).join("");
  const links = sounds.map((s, i) =>
    s.sourceUrl ? `<a href="${esc(s.sourceUrl)}" target="_blank">鸣声${i + 1}</a>` : `鸣声${i + 1}`
  ).join(" · ");
  const sources = new Set(sounds.map(s => s.source).filter(Boolean));
  const sourceText = [...sources].join(" / ") || "Macaulay Library / eBird";
  return `<div class="audio-card">${audios}</div><p class="small muted" style="margin-top:4px">来源：${esc(sourceText)}（${links}）</p>`;
}

function renderDistribution(rangeMap, sp, identification) {
  const wikiSource = toSimplified(identification?.wikipediaSummary || sp?.description || "");
  const wikiDist = extractDistFromWiki(stripWikiIntro(wikiSource));
  const preDist = toSimplified(identification?.wikipediaDistribution || sp?.distribution || "");
  const combined = wikiDist || preDist;
  const body = combined ? `<p>${esc(cleanText(combined))}</p>` : `<p class="muted">暂无该地区月份的可靠记录</p>`;
  const map = rangeMap?.sourceUrl ? `<p><a href="${esc(rangeMap.sourceUrl)}" target="_blank">查看权威分布图</a></p>` : "";
  return `${map}${body}`;
}

function cleanText(text) {
  return text.replace(/。。+/g, "。").replace(/））+/g, "）").replace(/，，+/g, "，").replace(/：：+/g, "：").replace(/；；+/g, "；").replace(/。；/g, "；").replace(/；。+/g, "。").replace(/^[；，]/, "");
}

function stripWikiIntro(text) {
  return text.replace(/^[^（(]+[（(](?:学名|學名)[：:].+?[）)]\s*/, "");
}

const DIST_RE = /[^。\n]*(?:分布[于在]|模式产地|分布於|分布在|常见[於于].{1,40}(?:地区|區域|大陆|國家)|广布[於于]|繁殖[於于在]|越冬[於于在]|南迁地区|南遷地區|冬候鸟|冬候鳥|从.{1,60}(?:经|到).{2,60}(?:到|一直).{2,60}|留鸟.{0,40}从.{2,60}到.{2,60}|造访.{0,30}(?:日本|韩国|朝鲜|台湾))[^。\n]*[。\n]/g;

function extractDistFromWiki(text) {
  const matches = (text || "").match(DIST_RE);
  if (!matches) return "";
  return matches.map(s => s.trim()).filter(Boolean).join("");
}

function stripDistSentences(text) {
  return text.replace(DIST_RE, "").replace(/^[。\s]+|[。\s]+$/g, "").replace(/\n{2,}/g, "\n");
}

function renderDescription(sp, identification) {
  const wiki = toSimplified(identification?.wikipediaSummary || sp?.description || "");
  const cleanWiki = stripDistSentences(stripWikiIntro(wiki));
  const fallback = identification?.morphology || identification?.habitat || identification?.behavior;
  const parts = [];
  parts.push(`<p class="detail-line latin">学名：${esc(sp.scientificName || "暂无可靠数据")}</p>`);
  if (sp?.aliases?.length) {
    parts.push(`<p class="detail-line">别名：${esc(sp.aliases.join("、"))}</p>`);
  }
  const detailTags = renderDetailTags(sp);
  if (detailTags) parts.push(detailTags);
  if (cleanWiki) {
    parts.push(`<p class="detail-line detail-text">${esc(cleanText(cleanWiki))}</p>`);
    if (identification?.wikipediaUrl) {
      parts.push(`<p class="small muted">来源：<a href="${esc(identification.wikipediaUrl)}" target="_blank" rel="noopener">维基百科</a>（CC BY-SA）</p>`);
    }
  } else if (fallback) {
    parts.push(`<p class="detail-line detail-text">${esc(cleanText(toSimplified(fallback)))}</p>`);
  }
  return parts.join("");
}

function renderSources(sp, media, identification) {
  const refs = [...(sp.sourceRefs || []), ...(identification.sourceRefs || [])];
  const mediaSources = [...(media.images || []).map(i => i.source), ...(media.sounds || []).map(s => s.source)].filter(Boolean);
  const all = [...new Set([...refs, ...mediaSources])];
  return all.length ? all.map(renderSourcePill).join("") : `<p class="muted">暂无可靠来源</p>`;
}

function renderSourcePill(source) {
  const text = String(source || "");
  const match = text.match(/(https?:\/\/\S+)/);
  if (!match) return `<span class="pill">${esc(text)}</span>`;
  const url = match[1];
  const label = text.replace(url, "").replace(/[：:|｜\s-]+$/, "").trim() || "来源";
  return `<a class="pill" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a>`;
}

function changeImage(offset, listId, birdId, isShare) {
  const images = appData.media[birdId]?.images || [];
  state.imageIndex = (state.imageIndex + offset + images.length) % images.length;
  updateBirdDetailImage(listId, birdId, isShare);
}

function handleBirdImageError(listId, birdId, isShare) {
  const images = appData.media[birdId]?.images || [];
  if (!images.length) return;
  const failedImages = markImageFailure(birdId, state.imageIndex);
  const nextIndex = getWorkingImageIndex(images, state.imageIndex + 1, failedImages);
  state.imageIndex = nextIndex === -1 ? 0 : nextIndex;
  updateBirdDetailImage(listId, birdId, isShare);
}

function handleThumbImageError(imgEl, birdId) {
  const images = appData.media[birdId]?.images || [];
  if (!images.length) return;
  const currentIndex = Number(imgEl?.dataset?.imageIndex || 0);
  const failedImages = markImageFailure(birdId, currentIndex);
  const nextIndex = getWorkingImageIndex(images, currentIndex + 1, failedImages);
  if (nextIndex === -1) {
    const fallback = document.createElement("div");
    fallback.className = "thumb";
    fallback.textContent = "🐦";
    const onclick = imgEl.getAttribute("onclick");
    if (onclick) fallback.setAttribute("onclick", onclick);
    imgEl.replaceWith(fallback);
    return;
  }
  imgEl.dataset.imageIndex = String(nextIndex);
  imgEl.src = images[nextIndex].url;
}

function goBird(listId, birdId, isShare) {
  state.imageIndex = 0;
  navigate(`bird?list=${listId}&bird=${birdId}${isShare ? "&share=1" : ""}`);
}

function openNotePanel(listId, birdId) {
  dismissTransientPanels();
  const notes = StorageService.getNotes(listId);
  const panel = document.createElement("div");
  panel.className = "note-panel";
  panel.innerHTML = `<h3>笔记</h3><textarea id="noteText" placeholder="补充说明">${esc(notes[birdId] || "")}</textarea><div class="row"><button id="saveNote">保存</button><button class="secondary" id="closeNote">关闭</button></div>`;
  document.body.appendChild(panel);
  panel.querySelector("#closeNote").onclick = () => panel.remove();
  panel.querySelector("#saveNote").onclick = () => {
    StorageService.saveNote(listId, birdId, panel.querySelector("#noteText").value);
    panel.remove();
    render();
  };
}

function renameList(listId) {
  const list = StorageService.getList(listId);
  if (!list) return;
  const newTitle = prompt("请输入新的预习本名称：", list.title);
  if (newTitle && newTitle.trim()) {
    StorageService.updateList({ ...list, title: newTitle.trim() });
    render();
  }
}

function showAddBirdModal(listId) {
  const list = StorageService.getList(listId);
  if (!list) return;
  dismissTransientPanels();
  const panel = document.createElement("div");
  panel.className = "note-panel";
  panel.innerHTML = `<h3>添加鸟种</h3>
    <input id="addBirdSearch" placeholder="输入鸟名、别名、学名或英文名" autocomplete="off" style="width:100%;">
    <div id="addBirdResults" class="search-results"></div>
    <div class="row" style="margin-top:12px;"><button class="secondary" id="closeAddBird">关闭</button></div>`;
  document.body.appendChild(panel);
  panel.querySelector("#closeAddBird").onclick = () => panel.remove();
  panel.querySelector("#addBirdSearch").oninput = function() {
    const query = normalize(this.value);
    const resultsNode = panel.querySelector("#addBirdResults");
    if (!query) {
      resultsNode.innerHTML = "";
      return;
    }
    const pinyinQuery = query.toLowerCase().replace(/\s/g, "");
    const results = appData.species.filter(sp => {
      const match = normalize(sp.chineseName).includes(query) ||
        normalize(sp.scientificName).includes(query) ||
        normalize(sp.englishName).includes(query) ||
        (sp.aliases || []).some(a => normalize(a).includes(query)) ||
        (pinyinQuery && matchesAnyPinyinInitials([sp.chineseName, ...(sp.aliases || [])], pinyinQuery));
      return match && !list.birdIds.includes(sp.birdId);
    }).slice(0, 10);
    resultsNode.innerHTML = results.length
      ? results.map(sp => `<div class="add-bird-item" onclick="addBirdToList('${esc(sp.birdId)}','${esc(listId)}','${esc(list.listId)}')"><strong>${esc(sp.chineseName)}</strong> <span class="muted">${esc(sp.englishName || sp.scientificName)}</span></div>`).join("")
      : `<p class="muted">未找到可添加的鸟种（可能已存在或未收录）。</p>`;
  };
}

function addBirdToList(targetBirdId, listId, rerenderListId) {
  const ok = StorageService.addBirdToList(rerenderListId, targetBirdId);
  if (ok) {
    document.querySelector(".note-panel")?.remove();
    render();
  } else {
    alert("无法添加该鸟种（可能已存在）。");
  }
}

function createSharePayload(list) {
  return { type: "birdPreviewBookShare", app: "观鸟预习本", version: 1, title: list.title, mode: list.mode, location: list.location, months: null, filters: list.filters, birdIds: list.birdIds, dataVersion: list.dataVersion };
}

function shareList(listId) {
  const list = StorageService.getList(listId);
  if (!list) return;
  const url = `${location.origin}${location.pathname}#share=${base64urlEncode(createSharePayload(list))}`;
  navigator.clipboard?.writeText(url).then(() => alert("分享链接已复制"), () => prompt("复制分享链接", url));
}

function renderShare(encoded) {
  try {
    const payload = base64urlDecode(encoded);
    if (payload.type !== "birdPreviewBookShare" || !Array.isArray(payload.birdIds)) throw new Error("bad payload");
    const listId = `share_${hashString(JSON.stringify(payload))}`;
    const list = { ...payload, listId, createdAt: nowISO(), updatedAt: nowISO() };
    sessionStorage.setItem(`share:${listId}`, JSON.stringify(list));
    renderBookDetail(listId, list);
  } catch {
    renderError("分享链接无法识别。", "返回首页");
  }
}

function getShareListFromSession(listId) {
  return safeParse(sessionStorage.getItem(`share:${listId}`), null);
}

function cloneShareList(shareListId) {
  const list = getShareListFromSession(shareListId);
  if (!list) return alert("无法读取分享清单。");
  const createdAt = nowISO();
  const copy = {
    listId: `list_${hashString(JSON.stringify({ birdIds: list.birdIds, createdAt }))}`,
    title: list.title + "（副本）",
    mode: "import",
    location: list.location || null,
    months: list.months || ALL_MONTHS,
    filters: list.filters || { orders: [], families: [], habitats: [] },
    birdIds: [...list.birdIds],
    createdAt,
    updatedAt: createdAt,
    dataVersion: appData.metadata.dataVersion
  };
  StorageService.saveList(copy);
  navigate(`book?id=${copy.listId}`);
}

function header(title) {
  return `<div class="page-header"><button class="ghost" onclick="navigate('home')">返回</button><h1 class="page-title">${esc(title)}</h1><span></span></div>`;
}

function renderError(message, buttonText) {
  app.innerHTML = `<div class="card"><p class="error">${esc(message)}</p><button onclick="navigate('home')">${esc(buttonText)}</button></div>`;
}

async function init() {
  try {
    appData = await loadData();
    window.addEventListener("hashchange", render);
    render();
  } catch (err) {
    console.error(err);
    app.innerHTML = `<div class="card error">启动失败：${esc(err.message)}</div>`;
  }
}

init();
