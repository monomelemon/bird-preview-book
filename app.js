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

const DATA_CACHE_VERSION = "v1-tangshan-2026-05-07p6";

const STORAGE_KEYS = {
  lists: "birdPreviewBook:lists",
  checks: (listId) => `birdPreviewBook:checks:${listId}`,
  notes: (listId) => `birdPreviewBook:notes:${listId}`
};

const ALL_MONTHS = [1,2,3,4,5,6,7,8,9,10,11,12];
const app = document.querySelector("#app");
let appData = null;
let state = { imageIndex: 0, matchResults: [] };

const $html = (strings, ...values) => strings.reduce((out, str, i) => out + str + (values[i] ?? ""), "");
const esc = (value) => String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
const nowISO = () => new Date().toISOString();
const safeParse = (text, fallback) => { try { return JSON.parse(text); } catch { return fallback; } };
const normalize = (text) => String(text || "").trim().toLowerCase();

const PINYIN_INITIALS = String.raw`
a:阿啊
b:白百斑半宝北背本币碧扁冰波伯薄布
c:仓草叉茶长朝潮彻匙翅崇丑出楚川锤雌赐粗簇翠村
d:达大代带丹淡岛道地滇典点雕顶东冬董豆独渡短断对多
e:俄峨额厄鄂鹗耳洱二
f:发番翻凡反饭范方飞非绯斐粉丰风冯凤佛夫弗浮福斧附复
g:盖干甘刚高鸽歌格各庚工公狗古谷骨瓜关冠鹳灌光广龟贵桂郭
h:哈海邯寒汉旱杭毫禾合河貉褐鹤黑恒横衡红虹鸿喉厚狐胡湖虎花华滑画槐环鹮黄蝗灰辉徽火
j:叽鸡姬基极急棘几计纪季济加佳家甲尖间肩剪碱剑涧暗健箭江将交角脚教接揭节洁捷靛金锦近经颈九酒旧居菊巨鹃卷绢
k:卡开堪坎看康科壳可克肯空口苦库矿阔
l:拉蓝朗浪老勒雷类黎篱李里理力历丽栗笠连帘镰脸链良两根亮辽猎鬣林临鳞灵岭另琉硫鹨六龙隆娄卢芦鸬鹭绿峦轮罗裸
m:麻马毛矛茅铆煤美门蒙猛梦迷米密绵冕面苗民闽名明鸣摸末漠墨牡木牧
n:南瑙内尼泥拟鸟宁牛农浓弄努女暖诺
p:爬帕牌攀盘胖刨炮佩盆蓬皮片漂拼品平瓶普
q:七齐奇旗企启千迁前潜浅茜强墙悄翘鞘亲秦青清庆琼丘秋鸲曲全拳雀群
s:萨鳃三散沙沙山珊陕善上勺少蛇社深神升生声圣尸十石食史始鹬寿书舒疏鼠曙树数双水睡丝四松苏宿虽穗隼蓑缩索
t:台苔太泰滩檀唐塘陶特提天田铁通同铜童头秃图土团屯驼椭
w:瓦弯玩晚万王网苇尾位魏文问翁乌无吴五鹉雾
x:西吸希昔溪锡蟋习喜细瞎峡狭下先仙咸显线乡香湘想项小楔蝎斜谢心新星兴行杏胸熊修绣须旭悬雪血
y:鸦鸭崖亚烟岩沿眼艳燕秧杨洋仰腰摇冶野叶夜一伊衣遗疑以异翼阴银隐印莺鹰迎影映硬勇尤有幼渝鱼羽雨玉鸢元园原圆缘远约月岳越云陨鹦
z:杂在赞灶泽贼增扎窄展占张章爪找赵赭浙针珍真枕震镇正郑枝织直志雉中肿重帚朱珠猪竹主煮住注柱砖妆壮追锥缀准卓资子紫棕纵走嘴最遵座
`.trim().split("\n").reduce((map, line) => {
  const [initial, chars] = line.split(":");
  for (const c of chars) map[c] = initial;
  return map;
}, {});

function getPinyinInitials(chineseText) {
  let result = "";
  for (const c of chineseText || "") {
    result += PINYIN_INITIALS[c] || "";
  }
  return result;
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
  if (!months || months.length === 0 || months.length === 12) return "全年";
  return months.map(m => `${m}月`).join("、");
}

function formatTaxonomy(species) {
  return `${species?.order?.zh || "暂无可靠数据"} > ${species?.family?.zh || "暂无可靠数据"}`;
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
  const speciesById = new Map();
  const speciesByChineseName = new Map();
  const speciesByAlias = new Map();
  const speciesByScientificName = new Map();
  const speciesByEnglishName = new Map();
  const occurrencesByBirdId = new Map();
  const taxonomySortMap = new Map();
  const locationsByCode = new Map();

  data.species.forEach(sp => {
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

  (data.taxonomy.orders || []).forEach(o => taxonomySortMap.set(o.zh, o.sortOrder));
  (data.taxonomy.families || []).forEach(f => taxonomySortMap.set(f.zh, f.sortOrder));
  flattenLocations(data.locations).forEach(loc => locationsByCode.set(loc.code, loc));

  return { ...data, speciesById, speciesByChineseName, speciesByAlias, speciesByScientificName, speciesByEnglishName, occurrencesByBirdId, taxonomySortMap, locationsByCode };
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
    const lists = this.getLists().filter(item => item.listId !== list.listId);
    lists.unshift(list);
    localStorage.setItem(STORAGE_KEYS.lists, JSON.stringify(lists));
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
  }
};

function navigate(hash) { location.hash = hash; }

function getRoute() {
  const raw = location.hash.slice(1);
  if (!raw) return { name: "home" };
  if (raw.startsWith("share=")) return { name: "share", encoded: raw.slice(6) };
  const [name, queryString] = raw.split("?");
  const params = Object.fromEntries(new URLSearchParams(queryString || ""));
  return { name, params };
}

function render() {
  const route = getRoute();
  state.imageIndex = 0;
  if (route.name === "new-book") return renderNewBook();
  if (route.name === "import-list") return renderImportList();
  if (route.name === "book") return renderBookDetail(route.params?.id);
  if (route.name === "bird") return renderBirdDetail(route.params?.list, route.params?.bird, route.params?.share === "1");
  if (route.name === "share") return renderShare(route.encoded);
  renderHome();
}

function renderHome() {
  const lists = StorageService.getLists();
  app.innerHTML = $html`
    <h1 class="home-title">观鸟预习本</h1>
    <p class="home-subtitle">可能会看到什么鸟？</p>
    <div class="stack">
      <button onclick="navigate('new-book')">推荐清单</button>
      <button class="secondary" onclick="navigate('import-list')">录入清单</button>
    </div>
    <h2 class="section-title">最近清单</h2>
    ${lists.length ? lists.map(list => `
      <div class="swipe-container">
        <div class="swipe-delete" onclick="deleteRecentList(event, '${esc(list.listId)}')">🗑</div>
        <div class="card list-card swipe-card" data-listid="${esc(list.listId)}">
          <div onclick="navigate('book?id=${esc(list.listId)}')" style="flex:1;">
            <strong>${esc(list.title)}</strong>
            <div class="muted small">${esc(formatMonths(list.months))} · ${list.birdIds.length} 种</div>
          </div>
        </div>
      </div>
    `).join("") : `<div class="card muted">还没有本地清单</div>`}
  `;
  setupSwipeCards();
}

function deleteRecentList(event, listId) {
  event.stopPropagation();
  if (confirm("确定删除这个清单？已观察和笔记也会一并删除。")) {
    StorageService.deleteList(listId);
    render();
  } else {
    resetAllSwipes();
  }
}

function resetAllSwipes() {
  document.querySelectorAll(".swipe-card").forEach(el => el.style.transform = "translateX(0)");
}

function setupSwipeCards() {
  document.querySelectorAll(".swipe-container").forEach(container => {
    const card = container.querySelector(".swipe-card");
    let startX = 0, moved = false;

    function reset() { card.style.transform = "translateX(0)"; }

    card.addEventListener("touchstart", e => {
      startX = e.touches[0].clientX;
      moved = false;
      resetAllSwipes();
    }, { passive: true });

    card.addEventListener("touchmove", e => {
      const dx = e.touches[0].clientX - startX;
      if (dx < 0) { card.style.transform = `translateX(${Math.max(dx, -80)}px)`; moved = true; }
    }, { passive: true });

    card.addEventListener("touchend", () => {
      if (!moved) return;
      const currentX = parseInt(card.style.transform.replace(/[^-\d]/g, "")) || 0;
      if (currentX < -40) card.style.transform = "translateX(-80px)";
      else reset();
    });

    card.addEventListener("click", e => {
      const currentX = parseInt(card.style.transform.replace(/[^-\d]/g, "")) || 0;
      if (currentX < -40) { e.stopPropagation(); e.preventDefault(); resetAllSwipes(); }
    });
  });
}

let _locationMatch = null;

function renderNewBook() {
  const orderOptions = (appData.taxonomy.orders || []).map(o => `<option value="order:${esc(o.zh)}">${esc(o.zh)}</option>`).join("");
  const familyOptions = (appData.taxonomy.families || []).map(f => `<option value="family:${esc(f.zh)}">${esc(f.zh)}</option>`).join("");
  const habitatOptions = (appData.taxonomy.habitats || []).map(h => `<option value="habitat:${esc(h)}">${esc(h)}</option>`).join("");
  _locationMatch = null;
  app.innerHTML = $html`
    ${header("新增预习本")}
    <div class="card stack">
      <div class="field"><label>地点</label>
        <input id="locInput" placeholder="输入省、市、区县或具体观鸟地点" autocomplete="off">
        <div id="locSuggest" class="search-results" style="max-height:200px;"></div>
      </div>
      <div class="field"><label>时间</label>
        <div id="monthGrid" class="month-grid">
          <button class="secondary pill active" data-m="all" id="monthAllBtn">全年</button>
          ${ALL_MONTHS.map(m => `<button class="secondary pill" data-m="${m}">${m}月</button>`).join("")}
        </div>
      </div>
      <div class="field"><label>想重点看哪类鸟？</label><select id="category"><option value="all">全部</option>${orderOptions}${familyOptions}${habitatOptions}</select></div>
      <div class="field"><label>预习本名称</label><input id="title" value=""></div>
      <button id="generate">生成预习本</button>
      <div id="newBookMsg" class="small"></div>
    </div>
  `;

  const locInput = document.querySelector("#locInput");
  const locSuggest = document.querySelector("#locSuggest");
  const category = document.querySelector("#category");
  const title = document.querySelector("#title");

  const allMonthBtns = [...document.querySelectorAll("#monthGrid .pill")];
  const monthAllBtn = document.querySelector("#monthAllBtn");

  function getSelectedMonths() {
    if (monthAllBtn?.classList.contains("active")) return ALL_MONTHS;
    return allMonthBtns.filter(b => b !== monthAllBtn && b.classList.contains("active")).map(b => Number(b.dataset.m));
  }

  function monthLabel() {
    const m = getSelectedMonths();
    if (m.length === 0 || m.length === 12) return "全年";
    return m.map(x => `${x}月`).join("、");
  }

  function syncTitle() {
    const locName = _locationMatch ? _locationMatch.name : (locInput.value.trim() || "全国");
    const catName = category.value === "all" ? "全部" : category.selectedOptions[0]?.textContent;
    title.value = `${locName} · ${monthLabel()} · ${catName}`;
  }

  function setMonthActive() {
    const m = getSelectedMonths();
    monthAllBtn.classList.toggle("active", m.length === 12 || m.length === 0);
    allMonthBtns.forEach(b => {
      if (b === monthAllBtn) return;
      b.classList.toggle("active", m.includes(Number(b.dataset.m)));
    });
    syncTitle();
  }

  monthAllBtn.onclick = () => {
    allMonthBtns.forEach(b => b.classList.remove("active"));
    monthAllBtn.classList.add("active");
    syncTitle();
  };

  allMonthBtns.forEach(b => {
    if (b === monthAllBtn) return;
    b.onclick = () => {
      monthAllBtn.classList.remove("active");
      b.classList.toggle("active");
      syncTitle();
    };
  });

  category.onchange = syncTitle;
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
    const months = getSelectedMonths();
    if (!months.length) { document.querySelector("#newBookMsg").innerHTML = `<span class="error">请至少选择一个月份。</span>`; return; }
    const filters = parseCategory(category.value);
    const birdIds = generateRecommendedList({ location, months, filters });
    if (!birdIds.length) {
      document.querySelector("#newBookMsg").innerHTML = `<span class="error">暂无符合条件且有可靠记录的鸟种。${!location?.provinceCode ? " 可尝试从地点建议中选择一个已知地点。" : ""}</span>`;
      return;
    }
    const createdAt = nowISO();
    const list = { listId: `list_${hashString(JSON.stringify({ location, months, filters, birdIds, createdAt }))}`, title: title.value.trim(), mode: "recommended", location, months, filters, birdIds, createdAt, updatedAt: createdAt, dataVersion: appData.metadata.dataVersion };
    StorageService.saveList(list);
    navigate(`book?id=${list.listId}`);
  };
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

function getSelectedLocation(province, city, district) {
  return {
    provinceCode: province.value,
    provinceName: province.selectedOptions[0]?.textContent || "",
    cityCode: city.value,
    cityName: city.selectedOptions[0]?.textContent || "",
    districtCode: district.value,
    districtName: district.selectedOptions[0]?.textContent || ""
  };
}

function getSelectedLocation(province, city, district) {
  return {
    provinceCode: province.value,
    provinceName: province.selectedOptions[0]?.textContent || "",
    cityCode: city.value,
    cityName: city.selectedOptions[0]?.textContent || "",
    districtCode: district.value,
    districtName: district.selectedOptions[0]?.textContent || ""
  };
}

function parseCategory(value) {
  const filters = { orders: [], families: [], habitats: [] };
  if (value.startsWith("order:")) filters.orders = [value.slice(6)];
  if (value.startsWith("family:")) filters.families = [value.slice(7)];
  if (value.startsWith("habitat:")) filters.habitats = [value.slice(8)];
  return filters;
}

function generateRecommendedList({ location, months, filters }) {
  const best = new Map();
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
  return [...best.keys()].sort((a, b) => sortBirdIds(a, b, best));
}

function matchLocation(occ, location) {
  if (location.districtCode && occ.locationCode === location.districtCode) return true;
  if (location.cityCode && occ.locationCode === location.cityCode) return true;
  if (location.provinceCode && occ.locationCode === location.provinceCode) return true;
  return false;
}

function occurrenceRank(occ) {
  const levelRank = { district: 3, city: 2, province: 1 }[occ.locationLevel] || 0;
  const reliabilityRank = occ.reliability === "high" ? 2 : 1;
  return levelRank * 100 + reliabilityRank * 10 + (occ.probabilityScore || 0);
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
  const pa = occurrenceMap?.get(a)?.probabilityScore || 0;
  const pb = occurrenceMap?.get(b)?.probabilityScore || 0;
  if (pa !== pb) return pb - pa;
  return (sa?.chineseName || "").localeCompare(sb?.chineseName || "", "zh-Hans-CN");
}

function renderImportList() {
  app.innerHTML = $html`
    ${header("录入清单")}
    <div class="card stack">
      <p class="muted">支持手动输入或批量导入</p>
      <div class="small muted">批量导入格式要求：可每行输入一种鸟；也可用逗号分隔多个鸟名；支持中文名、别名、学名或英文名；可直接从表格复制一列鸟名。</div>
      <textarea id="importText" placeholder="红嘴蓝鹊，白头鹎，普通翠鸟"></textarea>
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
  document.querySelector("#demo").onclick = () => document.querySelector("#importText").value = "红嘴蓝鹊，白头鹎，普通翠鸟";
  document.querySelector("#clear").onclick = () => { document.querySelector("#importText").value = ""; document.querySelector("#matchResults").innerHTML = ""; };
  document.querySelector("#match").onclick = runImportMatch;
  document.querySelector("#createImport").onclick = createImportList;
}

function parseImportText(text) {
  return [...new Set(text.split(/[\n,，]/).map(item => item.trim()).filter(Boolean))];
}

function matchInputName(input) {
  const key = normalize(input);
  const exact = appData.speciesByChineseName.get(key) || appData.speciesByAlias.get(key) || appData.speciesByScientificName.get(key) || appData.speciesByEnglishName.get(key);
  if (exact) return { input, status: "matched", species: exact };
  const candidates = appData.species.filter(sp => normalize(sp.chineseName).includes(key) || key.includes(normalize(sp.chineseName))).slice(0, 5);
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
  const list = { listId: `import_${hashString(JSON.stringify({ birdIds, createdAt }))}`, title: document.querySelector("#importTitle").value.trim() || `自定义预习本 · ${birdIds.length}种`, mode: "import", location: null, months: ALL_MONTHS, filters: { orders: [], families: [], habitats: [] }, birdIds, createdAt, updatedAt: createdAt, dataVersion: appData.metadata.dataVersion };
  StorageService.saveList(list);
  navigate(`book?id=${list.listId}`);
}

function renderBookDetail(listId, sharePayload = null) {
  const list = sharePayload || StorageService.getList(listId);
  if (!list) return renderError("当前清单不存在。", "返回首页");
  const isShare = listId?.startsWith("share_");
  const checks = StorageService.getChecks(list.listId);
  const filter = sessionStorage.getItem(`filter:${list.listId}`) || "all";
  const sort = sessionStorage.getItem(`sort:${list.listId}`) || "taxonomy";
  const search = sessionStorage.getItem(`search:${list.listId}`) || "";
  const birds = filterSortBirds(list.birdIds, list.listId, { filter, sort, search }, list);
  const hasProb = hasProbabilityData(list);
  const sortOptions = [
    { value: "taxonomy", label: "按分类地位" },
    { value: "check", label: "按观察状态" },
    { value: "name", label: "按中文名" },
    { value: "probability", label: "按出现概率", disabled: !hasProb }
  ];
  const sortHTML = sortOptions.map(o =>
    `<option value="${o.value}"${o.disabled ? " disabled" : ""}>${esc(o.label)}${o.disabled ? "（暂无数据）" : ""}</option>`
  ).join("");
  app.innerHTML = $html`
    <div class="page-header">
      <button class="ghost" onclick="navigate('home')">返回</button>
      <div style="display:flex;align-items:center;gap:6px;">
        <h1 class="page-title" style="margin:0;">${esc(list.title)}</h1>
        ${isShare ? `` : `<button class="ghost small" onclick="renameList('${esc(list.listId)}')" title="重命名">✎</button>`}
      </div>
      ${isShare ? `<span></span>` : `<button class="ghost" onclick="shareList('${esc(list.listId)}')">分享</button>`}
    </div>
    <div class="card">
      <strong>已观察 ${checks.checkedBirdIds.length} / 共 ${list.birdIds.length} 种</strong>
      <div class="toolbar" style="margin-top:12px;">
        <input id="search" placeholder="搜索鸟名、别名、学名、英文名（支持拼音首字母）" value="${esc(search)}">
        <div class="toolbar-grid">
          <select id="filter"><option value="all">全部</option><option value="unchecked">未观察</option><option value="checked">已观察</option></select>
          <select id="sort">${sortHTML}</select>
        </div>
      </div>
      ${birds.length ? birds.map(id => birdRow(list, id, isShare)).join("") : `<p class="muted">没有符合条件的鸟种。</p>`}
    </div>
    ${isShare ? `<button class="secondary" style="width:100%;" onclick="cloneShareList('${esc(list.listId)}')">复制为我的清单（可编辑）</button>` : ``}
    ${isShare ? `` : `<button class="fab" onclick="showAddBirdModal('${esc(list.listId)}')" title="添加鸟种">+</button>`}
  `;
  document.querySelector("#filter").value = filter;
  document.querySelector("#sort").value = sort;
  document.querySelector("#search").oninput = e => { sessionStorage.setItem(`search:${list.listId}`, e.target.value); renderBookDetail(list.listId, isShare ? list : null); };
  document.querySelector("#filter").onchange = e => { sessionStorage.setItem(`filter:${list.listId}`, e.target.value); renderBookDetail(list.listId, isShare ? list : null); };
  document.querySelector("#sort").onchange = e => { sessionStorage.setItem(`sort:${list.listId}`, e.target.value); renderBookDetail(list.listId, isShare ? list : null); };
}

function birdRow(list, birdId, isShare) {
  const sp = appData.speciesById.get(birdId);
  if (!sp) return "";
  const media = appData.media[birdId];
  const img = media?.images?.[0]?.url;
  const checked = StorageService.isChecked(list.listId, birdId);
  const shareParam = isShare ? "&share=1" : "";
  return `<div class="bird-row ${checked ? "checked-row" : ""}">
    ${img ? `<img class="thumb" src="${esc(img)}" alt="${esc(sp.chineseName)}">` : `<div class="thumb">🐦</div>`}
    <div class="bird-main" onclick="navigate('bird?list=${esc(list.listId)}&bird=${esc(birdId)}${shareParam}')">
      <div class="bird-name">${esc(sp.chineseName)}</div>
      <div class="bird-taxonomy">${esc(formatTaxonomy(sp))}</div>
    </div>
    <div class="check-zone" onclick="toggleAndRefresh('${esc(list.listId)}','${esc(birdId)}')">${checked ? "✓" : ""}</div>
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
    const pinyinInitials = getPinyinInitials(sp?.chineseName || "");
    if (pinyinQuery && pinyinInitials.toLowerCase().startsWith(pinyinQuery)) return true;
    const hay = [sp?.chineseName, sp?.scientificName, sp?.englishName, ...(sp?.aliases || [])].map(normalize).join(" ");
    return hay.includes(query);
  }).sort((a, b) => {
    if (sort === "name") return (appData.speciesById.get(a)?.chineseName || "").localeCompare(appData.speciesById.get(b)?.chineseName || "", "zh-Hans-CN");
    if (sort === "check") return Number(StorageService.isChecked(listId, a)) - Number(StorageService.isChecked(listId, b));
    if (sort === "probability") return ((locationProbability(b, list) || 0) - (locationProbability(a, list) || 0));
    return sortBirdIds(a, b);
  });
}

function bestProbability(birdId) {
  return Math.max(0, ...(appData.occurrencesByBirdId.get(birdId) || []).map(o => o.probabilityScore || 0));
}

function locationProbability(birdId, list) {
  if (!list?.location || !list?.months?.length) return 0;
  const occs = appData.occurrencesByBirdId.get(birdId) || [];
  const scores = occs.filter(o =>
    matchLocation(o, list.location) && o.months?.some(m => list.months.includes(m))
  ).map(o => o.probabilityScore || 0);
  return scores.length ? Math.max(...scores) : 0;
}

function hasProbabilityData(list) {
  if (!list?.location || !list?.months?.length) return false;
  return list.birdIds.some(birdId => {
    const occs = appData.occurrencesByBirdId.get(birdId) || [];
    return occs.some(o =>
      o.probabilityScore != null && o.probabilityScore > 0 &&
      matchLocation(o, list.location) &&
      o.months?.some(m => list.months.includes(m))
    );
  });
}

function toggleAndRefresh(listId, birdId) {
  StorageService.toggleCheck(listId, birdId);
  render();
}

function renderBirdDetail(listId, birdId, isShare) {
  const list = isShare ? getShareListFromSession(listId) : StorageService.getList(listId);
  const sp = appData.speciesById.get(birdId);
  if (!list || !sp) return renderError("当前鸟种资料不存在。", "返回首页");
  const media = appData.media[birdId] || { images: [], sounds: [] };
  const identification = appData.identification[birdId] || {};
  const similar = appData.similar[birdId] || [];
  const checked = StorageService.isChecked(list.listId, birdId);
  const notes = StorageService.getNotes(list.listId);
  const index = list.birdIds.indexOf(birdId);
  const image = media.images?.[state.imageIndex];
  app.innerHTML = $html`
    <div class="page-header">
      <button class="ghost" onclick="${isShare ? `renderBookDetail('${esc(list.listId)}', getShareListFromSession('${esc(list.listId)}'))` : `navigate('book?id=${esc(list.listId)}')`}">返回清单</button>
      <strong>${index + 1}/${list.birdIds.length}</strong>
      <button class="ghost" onclick="openNotePanel('${esc(list.listId)}','${esc(birdId)}')">笔记${notes[birdId] ? "•" : ""}</button>
      <button class="ghost check-zone" onclick="toggleAndRefresh('${esc(list.listId)}','${esc(birdId)}')">${checked ? "✓" : ""}</button>
    </div>
    <div class="detail-name">
      <h1>${esc(sp.chineseName)}</h1>
      <div class="muted">${esc(sp.englishName || "暂无可靠数据")}</div>
      <div class="latin">${esc(sp.scientificName || "暂无可靠数据")}</div>
      <div class="bird-taxonomy">${esc(formatTaxonomy(sp))}</div>
    </div>
    <div class="hero-image">${image ? `<img src="${esc(image.url)}" alt="${esc(sp.chineseName)}">` : `<div><div style="font-size:58px;text-align:center;">🐦</div><div class="muted">暂无可靠图片</div></div>`}</div>
    <div class="image-counter">${media.images?.length ? `${state.imageIndex + 1}/${media.images.length}` : "0/0"}</div>
    ${media.images?.length > 1 ? `<div class="row"><button class="secondary" onclick="changeImage(-1, '${esc(listId)}', '${esc(birdId)}', ${isShare})">上一张</button><button class="secondary" onclick="changeImage(1, '${esc(listId)}', '${esc(birdId)}', ${isShare})">下一张</button></div>` : ""}
    <details open><summary>识别要点</summary>${renderKeyPoints(identification.keyPoints)}</details>
    <details open><summary>鸣声</summary>${renderSounds(media.sounds)}</details>
    <details><summary>相似种对比</summary>${renderSimilar(similar)}</details>
    <details><summary>分布信息</summary>${renderDistribution(media.rangeMap, birdId)}</details>
    <details><summary>详细信息</summary>${esc(identification.morphology || identification.habitat || identification.behavior || "暂无可靠数据")}</details>
    <details><summary>资料来源</summary>${renderSources(sp, media, identification)}</details>
    <div class="bottom-nav">
      <button class="secondary" ${index <= 0 ? "disabled" : ""} onclick="goBird('${esc(list.listId)}', '${esc(list.birdIds[index - 1])}', ${isShare})">上一种</button>
      <button ${index >= list.birdIds.length - 1 ? "disabled" : ""} onclick="goBird('${esc(list.listId)}', '${esc(list.birdIds[index + 1])}', ${isShare})">下一种</button>
    </div>
  `;
}

function renderKeyPoints(points = []) {
  if (!points.length) return `<p class="muted">暂无可靠辨识资料</p>`;
  return `<ol>${points.map(p => `<li>${esc(p)}</li>`).join("")}</ol>`;
}

function renderSounds(sounds = []) {
  if (!sounds.length) return `<p class="muted">暂无可靠鸣声</p>`;
  return sounds.map(s => `<div class="card"><strong>${esc(s.caption || s.type || "鸣声")}</strong><br><audio controls src="${esc(s.url)}"></audio><div class="small muted">${esc(s.source || "")} ${s.sourceUrl ? `<a href="${esc(s.sourceUrl)}" target="_blank">来源</a>` : ""}</div></div>`).join("");
}

function renderSimilar(items = []) {
  if (!items.length) return `<p class="muted">暂无相似种资料</p>`;
  return items.map(item => `<div><strong>${esc(item.similarName)}</strong><ul>${(item.differences || []).map(d => `<li>${esc(d.field)}：${esc(d.thisSpecies)} / ${esc(d.similarSpecies)}</li>`).join("")}</ul></div>`).join("");
}

function renderDistribution(rangeMap, birdId) {
  const occs = appData.occurrencesByBirdId.get(birdId) || [];
  const lines = occs.map(o => `${o.locationName}：${formatMonths(o.months)}（${o.reliability}）`).join("<br>");
  const map = rangeMap?.sourceUrl ? `<p><a href="${esc(rangeMap.sourceUrl)}" target="_blank">查看权威分布图</a></p>` : `<p class="muted">暂无可靠分布图</p>`;
  const occRefs = [...new Set(occs.flatMap(o => o.sourceRefs || []))];
  const refs = occRefs.length ? `<div class="small muted">出现记录来源：${occRefs.map(renderSourcePill).join("")}</div>` : "";
  return `${map}<p>${lines || "暂无该地区月份的可靠记录"}</p>${refs}`;
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
  renderBirdDetail(listId, birdId, isShare);
}

function goBird(listId, birdId, isShare) {
  state.imageIndex = 0;
  navigate(`bird?list=${listId}&bird=${birdId}${isShare ? "&share=1" : ""}`);
}

function openNotePanel(listId, birdId) {
  const notes = StorageService.getNotes(listId);
  const panel = document.createElement("div");
  panel.className = "note-panel";
  panel.innerHTML = `<h3>笔记</h3><textarea id="noteText" placeholder="补充说明">${esc(notes[birdId] || "")}</textarea><div class="row"><button id="saveNote">保存</button><button class="secondary" id="closeNote">关闭</button></div>`;
  document.body.appendChild(panel);
  document.querySelector("#closeNote").onclick = () => panel.remove();
  document.querySelector("#saveNote").onclick = () => { StorageService.saveNote(listId, birdId, document.querySelector("#noteText").value); panel.remove(); render(); };
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
  const panel = document.createElement("div");
  panel.className = "note-panel";
  panel.innerHTML = `<h3>添加鸟种</h3>
    <input id="addBirdSearch" placeholder="输入鸟名、别名、学名或英文名" autocomplete="off" style="width:100%;">
    <div id="addBirdResults" class="search-results"></div>
    <div class="row" style="margin-top:12px;"><button class="secondary" id="closeAddBird">关闭</button></div>`;
  document.body.appendChild(panel);
  document.querySelector("#closeAddBird").onclick = () => panel.remove();
  document.querySelector("#addBirdSearch").oninput = function() {
    const query = normalize(this.value);
    if (!query) { document.querySelector("#addBirdResults").innerHTML = ""; return; }
    const results = appData.species.filter(sp => {
      const match = normalize(sp.chineseName).includes(query) ||
        normalize(sp.scientificName).includes(query) ||
        normalize(sp.englishName).includes(query) ||
        (sp.aliases || []).some(a => normalize(a).includes(query));
      return match && !list.birdIds.includes(sp.birdId);
    }).slice(0, 10);
    document.querySelector("#addBirdResults").innerHTML = results.length
      ? results.map(sp => `<div class="add-bird-item" onclick="addBirdToList('${esc(listId)}','${esc(sp.birdId)}','${esc(list.listId)}')"><strong>${esc(sp.chineseName)}</strong> <span class="muted">${esc(sp.englishName || sp.scientificName)}</span></div>`).join("")
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
  return { type: "birdPreviewBookShare", app: "观鸟预习本", version: 1, title: list.title, mode: list.mode, location: list.location, months: list.months, filters: list.filters, birdIds: list.birdIds, dataVersion: list.dataVersion };
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
