# V2 数据修复与 UI 回归

## TL;DR

> **Quick Summary**: 修复 V2 数据重建脚本导致的10个回归问题：occurrence 全部全国级导致筛选失效、V1 手工数据被覆盖、科名/鸟名为英文繁体、Wikipedia 数据丢失、保存按钮失效、生成流程变化。
> 
> **Deliverables**:
> - GBIF 重建省级+月份 occurrence 数据（合并 V1 手工数据）
> - 104 科名英→中映射、全部鸟名繁→简转换
> - Wikipedia 数据重新获取并写入 species.json
> - 恢复 V1 生成流程、修复保存按钮、简化鸣声播放器
> - Macaulay 图片优先（过滤图画）、locations.json 按实际数据清理
> 
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 → Task 2 → Task 4 → Task 6 → Wave 3 (UI) → Task 10

---

## Context

### 问题诊断
V2 `clean_and_rebuild.py` 采用「完整替换」而非「增量合并」策略：
- occurrence 全部重建为全国级（816条 `locationLevel:national, months:[1..12]`）
- species birdId 从 V1 的学名格式改为 eBird speciesCode
- identification.json 重新生成，覆盖 Wikipedia 数据
- family.zh 未应用 FAMILY_MAP

### 10 个回归问题
1. 选任何地点/月份都返回 816 种 — occurrence 全是全国级全年
2. 保存按钮无反应 — localStorage 可能超限且无错误处理
3. V2 丢 27 种 V1 鸟 — eBird 中文名与 V1 不同且繁简不一
4. 816 个科名全英文 — FAMILY_MAP 未执行
5. 鸟名繁体 — eBird zh locale 返回繁体，toSimplified 只做运行时转换
6. 图片混入图画 — Wikimedia Commons 含插图
7. Wikipedia 数据丢失 — 写入 identification.json 后被覆盖
8. 鸣声多余信息 — 显示标题和完整控制条
9. 生成流程多了预览步骤 — 用户要 V1 直接生成
10. locations.json 骨架数据无实际匹配 — 全部全国级无省市区

### 核心修复策略：重建 + 合并
- **不完整替换**，保留 V1 手工数据
- GBIF 提供省+月份粒度
- 科名/鸟名在数据层修复（非运行时）
- V1 birdId 保留为别名确保导入匹配

### Metis Review
**关键建议**（已纳入）：
- 合并优先级：manual > gbif > ebird
- GBIF 需过滤 captive/introduced/uncertain 记录
- V1 birdId 保留为 aliases
- 繁体中文名保留为 aliases
- GBIF 省份名标准化（Nei Mongol → 内蒙古）
- localStorage 不可用/无痕模式需处理
- 脚本必须 deterministic 且可复现

---

## Work Objectives

### Core Objective
修复 V2 全部数据与 UI 回归，恢复 V1 筛选功能和手工数据，同时保留 V2 的 816 种覆盖面。

### Concrete Deliverables
- `data/occurrences.json`：省级+月份记录（含23条唐山手工数据）
- `data/species.json`：科名中文、鸟名简体、V1 别名保留、Wikipedia description/distribution
- `data/media.json`：Macaulay 照片优先、过滤图示
- `data/taxonomy.json`：104科中文名、按实际数据更新
- `data/locations.json`：只保留有 occurrence 的省份
- `app.js`：恢复 V1 生成流程、修复保存、简化鸣声
- `style.css`：如有鸣声样式调整

### Definition of Done
- [ ] 选「河北 + 5月」返回河北5月有记录的鸟种（≠816）
- [ ] 选「唐山」（手工数据）返回23种（5月7种/9月23种）
- [ ] 清单页科名显示中文（鸦科 而非 Crows, Jays）
- [ ] 鸟种名显示简体（红嘴蓝鹊 而非 紅嘴藍鵲）
- [ ] 导入「普通翠鸟」「白头鹎」「红嘴蓝鹊」能匹配
- [ ] 保存按钮正常跳转清单页
- [ ] 鸣声无标题文字、无下载/调速按钮
- [ ] 生成直接进入清单页（无预览步骤）
- [ ] 数据一致性脚本通过

### Must Have
- GBIF 省级+月份 occurrence（可靠性 medium+）
- 23条 V1 唐山手工数据保留
- 全部科名中文
- 全部鸟名简体
- V1 鸟种可匹配（鸟名/别名保留）
- 保存功能正常
- Wikipedia 数据写入 species.json

### Must NOT Have
- 市级 occurrence（GBIF 无结构化市级数据）
- 假数据（全年/全国级占位）
- 新功能（仅修复回归）
- 完整替换（必须合并 V1 数据）
- 英文/繁体展示（中文名、科名、别名）

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO
- **Automated tests**: None
- **QA**: Agent-executed via Bash (data scripts), Playwright (UI flows), Node (syntax check)

### QA Policy
- **Data scripts**: Bash 运行 Python 脚本 + 数据一致性检查
- **UI flows**: Playwright 验证生成→保存→清单页流程
- **Regression**: 导入匹配三种演示鸟 + 唐山5月/9月数量验证

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (数据准备 — 脚本并行):
├── Task 1: GBIF 省级+月份数据获取脚本
├── Task 2: 合并 V1 手工数据 + 重建 occurrences.json
└── Task 3: 科名中文化 + 鸟名繁转简 + Wikipedia 合并脚本

Wave 2 (UI 代码 — 全部并行):
├── Task 4: 恢复 V1 生成流程（生成→清单页→保存）
├── Task 5: 修复保存按钮（try-catch + 超限提示）
├── Task 6: 简化鸣声播放器（去标题 + controlsList）
├── Task 7: 图片类型标记（Macaulay 优先）
├── Task 8: locations.json 按 occurrence 重建
└── Task 9: 其他数据/展示修复（V1 别名、taxonomy 更新、详情页科名等）

Wave 3 (验证+部署):
├── Task 10: 本地全量验证（数据一致性 + JS 语法 + Playwright 流程）
└── Task 11: 部署 + 线上回归验证
```

**Critical Path**: Task 1 → Task 2 → Task 4 → Task 6 → Task 10  
**Parallel Speedup**: ~60% faster than sequential (Wave 1 scripts parallel, Wave 2 all UI parallel)

### Agent Dispatch Summary
- **Task 1**: `quick` — GBIF 数据脚本
- **Task 2**: `quick` — 数据合并脚本
- **Task 3**: `quick` — 数据清洗脚本
- **Task 4**: `deep` — UI 流程重构
- **Task 5**: `quick` — 保存按钮修复
- **Task 6**: `quick` — 鸣声 UI
- **Task 7**: `quick` — 图片过滤
- **Task 8**: `quick` — locations 重建
- **Task 9**: `unspecified-high` — 综合数据/展示修复
- **Task 10**: `unspecified-high` — 本地验证
- **Task 11**: `quick` — 部署

---

## TODOs

- [x] 1. GBIF 省级+月份数据获取脚本

  **What to do**:
  - 编写 `scripts/fetch_gbif.py`
  - 读取 `data/species.json` 获取全部 scientificName
  - 对每个鸟种调用 GBIF API `occurrence/search?country=CN&scientificName=...&facet=stateProvince&facet=month&limit=0`
  - 过滤：`basisOfRecord` 排除 `FOSSIL_SPECIMEN`、`LIVING_SPECIMEN`；排除 `establishmentMeans=MANAGED/INTRODUCED`
  - 聚合每个 (birdId, province, month) 的记录数
  - 省份名标准化映射：`Beijing`→`北京`、`Hebei`→`河北`、`Nei Mongol`→`内蒙古`、`Xinjiang Uygur`/`Sinkiang`→`新疆`、`Xizang`→`西藏`、`YunNan`→`云南` 等
  - 输出中间文件 `data/gbif_raw.json`（供 Task 2 使用）
  - 记录执行统计：多少种有GBIF数据、省份覆盖数

  **Must NOT do**:
  - 不写入最终 `occurrences.json`（由 Task 2 合并）
  - 不做市级数据（GBIF无结构化字段）
  - 不覆盖任何现有文件

  **References**:
  - `data/species.json` — scientificName 用于 GBIF 查询
  - GBIF API: `https://api.gbif.org/v1/occurrence/search?country=CN&scientificName=...&facet=stateProvince&facet=month&limit=0`

  **Acceptance Criteria**:
  - [ ] `scripts/fetch_gbif.py` 可独立运行（`python3 scripts/fetch_gbif.py`）
  - [ ] `data/gbif_raw.json` 生成，包含 birdId→省份→月份的聚合记录
  - [ ] 省份名全部为中文（无 English 拼音）

  **QA Scenarios**:
  ```
  Scenario: 脚本正常完成
    Tool: Bash
    Preconditions: 网络可访问 api.gbif.org
    Steps:
      1. 运行: python3 scripts/fetch_gbif.py
      2. 检查退出码: echo $? → 0
      3. 检查输出文件存在: ls data/gbif_raw.json
    Expected Result: 退出码0，gbif_raw.json 存在且为合法 JSON
    Evidence: .sisyphus/evidence/task-1-gbif-output.txt

  Scenario: 省份名标准化
    Tool: Bash
    Preconditions: gbif_raw.json 已生成
    Steps:
      1. python3 -c "import json; d=json.load(open('data/gbif_raw.json')); provinces=set(); [provinces.update(p.keys()) for p in d.values()]; print('\n'.join(sorted(provinces)))"
      2. 检查输出无 Beijing/Hebei/Nei Mongol/Xinjiang Uygur 等英文名
    Expected Result: 所有省份名为中文
    Evidence: .sisyphus/evidence/task-1-provinces.txt
  ```

  **Commit**: NO (中间文件，由 Task 2 统一提交)

- [x] 2. 合并 V1 手工数据 + 重建 occurrences.json

  **What to do**:
  - 编写 `scripts/rebuild_occurrences.py`
  - 从 git 恢复 V1 数据：`git show 08cba9d:data/occurrences.json` → 筛选 `locationLevel=city` 的23条
  - 从 `data/gbif_raw.json` 读取 GBIF 聚合数据
  - 合并规则：
    - 手工记录保留不动（`sourceRefs` 含 `manual`，`locationLevel=city`，保持原有 months）
    - GBIF 记录生成：`locationLevel=province`，`locationCode` 用 province code，`months` 取 GBIF 有记录的月份且记录数≥3
    - 月度记录数<3 的不纳入（避免噪声）
    - 同鸟种同省多条 GBIF month 合并为一条 occurrence
    - `reliability`：手工=high，GBIF=medium
    - `sourceRefs`：GBIF 标记 `GBIF.org (date)`，手工标记 `manual: Wild Beijing Nanpu 2011` 等
  - 更新 `metadata.json` dataVersion
  - 统计数据：手工条数、GBIF 条数、总条数、省份覆盖、有月份数据的鸟种数

  **Must NOT do**:
  - 不生成 `locationLevel=national` 记录
  - 不覆盖手工数据的 months
  - 不生成 months=[1..12] 全部月份（除非 GBIF 确实所有月都有≥3条记录）

  **References**:
  - `08cba9d:data/occurrences.json` — V1 手工唐山数据
  - `data/gbif_raw.json` — Task 1 输出
  - `data/species.json` — birdId 验证

  **Acceptance Criteria**:
  - [ ] `data/occurrences.json` 包含23条 V1 手工记录
  - [ ] 手工记录 `locationLevel=city`, `sourceRefs` 含 `manual`
  - [ ] 无 `locationLevel=national` 记录
  - [ ] 无 `months=[1,2,...,12]` 全部月份（除非真实数据支持）
  - [ ] 至少覆盖12个省份
  - [ ] dataVersion 已更新

  **QA Scenarios**:
  ```
  Scenario: 手工数据保留
    Tool: Bash
    Steps:
      1. python3 -c "import json; o=json.load(open('data/occurrences.json')); manual=[x for x in o if 'manual' in str(x.get('sourceRefs',''))]; print(f'Manual: {len(manual)}'); assert len(manual)>=23"
    Expected Result: 手工记录 ≥ 23条
    Failure Indicators: 手工记录 < 23条
    Evidence: .sisyphus/evidence/task-2-manual-count.txt

  Scenario: 无全国级虚假记录
    Tool: Bash
    Steps:
      1. python3 -c "import json; o=json.load(open('data/occurrences.json')); nat=[x for x in o if x['locationLevel']=='national']; print(f'National: {len(nat)}'); assert len(nat)==0"
    Expected Result: National 记录 = 0
    Evidence: .sisyphus/evidence/task-2-no-national.txt

  Scenario: 无全月份占位
    Tool: Bash
    Steps:
      1. python3 -c "import json; o=json.load(open('data/occurrences.json')); full=[x for x in o if x['months']==[1,2,3,4,5,6,7,8,9,10,11,12]]; print(f'Full-year: {len(full)}'); print(f'Total: {len(o)}')"
    Expected Result: 全月份记录应极少（仅GBIF确实全年有大量数据的鸟种），输出具体数字供人工判断
    Evidence: .sisyphus/evidence/task-2-full-year.txt
  ```

  **Commit**: YES
  - Message: `fix(data): rebuild occurrences with GBIF province+month data and V1 manual records`
  - Files: `data/occurrences.json`, `data/metadata.json`, `scripts/rebuild_occurrences.py`

- [x] 3. 科名中文化 + 鸟名繁转简 + Wikipedia 合并脚本

  **What to do**:
  - 编写 `scripts/clean_species_data.py`
  - 科名映射：104个英文 family.zh → 中文（对照 taxonomy.json 的科列表）
  - 鸟名繁转简：`chineseName` 全部简转繁（用 TRAD_TO_SIMP 表）
  - 繁体原名保留为 `aliases`（用于搜索）
  - V1 birdId 保留为 `aliases`（确保「普通翠鸟→alcedo_atthis→comkin1」能匹配）
  - Wikipedia 数据：重新运行 `scripts/fetch_wikipedia_v2.py`（输出改写到 species.json 的 `description`/`distribution` 字段，不再写 identification.json）
  - `identification.json` 不在此任务修改（保留现有手工数据）
  - 更新 `taxonomy.json` 的 families 列表（从 species 唯一 family 生成）
  - 更新 `metadata.json` 版本号

  **Must NOT do**:
  - 不修改 scientificName/englishName
  - 不覆盖 `identification.json` 手工辨识数据
  - 不影响 V2 的 eBird speciesCode（birdId）

  **References**:
  - `scripts/fetch_wikipedia_v2.py` — 需修改输出目标
  - `data/species.json` — 当前数据
  - `data/taxonomy.json` — 科列表
  - `app.js:29` — TRAD_TO_SIMP 表

  **Acceptance Criteria**:
  - [ ] 全部 816 种 `family.zh` 为中文
  - [ ] 全部 `chineseName` 为简体中文
  - [ ] 繁体原名在 `aliases` 中
  - [ ] V1 birdId 在 `aliases` 中（至少三种演示鸟）
  - [ ] taxonomy.json families 从 species 重建
  - [ ] Wikipedia description/distribution 有数据的鸟种 > 0

  **QA Scenarios**:
  ```
  Scenario: 科名全中文
    Tool: Bash
    Steps:
      1. python3 -c "import json; s=json.load(open('data/species.json')); en_fam=[x for x in s if any(c.isascii() and c.isalpha() for c in x['family']['zh'] if c not in ' ·、')]; print(f'English family.zh: {len(en_fam)}'); assert len(en_fam)==0, f'{en_fam[:5]}'"
    Expected Result: English family.zh = 0
    Evidence: .sisyphus/evidence/task-3-family-cn.txt

  Scenario: 鸟名全简体
    Tool: Bash
    Steps:
      1. python3 -c "import json; s=json.load(open('data/species.json')); trad=sum(1 for x in s if any(c in '鵲鵰鷹鷺雞鶴鷗鷸鵐鶲鵯鶇鴉鷂鷲鶚鶻' for c in x['chineseName'])); print(f'Traditional names: {trad}'); assert trad==0"
    Expected Result: 繁体名 = 0
    Evidence: .sisyphus/evidence/task-3-simplified.txt

  Scenario: 三种演示鸟可匹配
    Tool: Bash
    Steps:
      1. python3 -c "
      import json; s=json.load(open('data/species.json'))
      targets=['普通翠鸟','白头鹎','红嘴蓝鹊']
      for t in targets:
          found=[x for x in s if x['chineseName']==t or t in x.get('aliases',[])]
          print(f'{t}: {\"FOUND\" if found else \"MISSING\"}')"
    Expected Result: 三种全部 FOUND
    Evidence: .sisyphus/evidence/task-3-demo-match.txt
  ```

  **Commit**: YES
  - Message: `fix(data): Chinese family names, simplified species names, Wikipedia data merge`
  - Files: `data/species.json`, `data/taxonomy.json`, `data/metadata.json`, `scripts/clean_species_data.py`, `scripts/fetch_wikipedia_v2.py`

- [x] 4. 恢复 V1 生成流程

  **What to do**:
  - 修改 `app.js` `renderNewBook()`：
    - 按钮文字从「生成预览」改回「生成预习本」
    - 移除预览区（`#previewSection`）及相关 JS
    - 点击「生成预习本」直接调用 `savePreviewToStorage()` 逻辑 → 保存到 localStorage → 跳转清单页
    - 移除 `handleNewBookBack()` 的未保存检测（生成即保存）
  - 在清单页 `renderBookDetail()` 增加：
    - 本地清单（非分享）显示「保存预习本」按钮（如果 `list.saved !== true`）
    - 已保存的清单不显示保存按钮
    - 返回按钮检测：如果清单未保存，弹自定义对话框：「确认返回 / 你还没有保存这个预习本」→ 取消/不保存/保存
  - 在 `StorageService` 中增加 `isSaved` 标记或利用 `list.saved` 字段

  **Must NOT do**:
  - 不改变分享页行为
  - 不影响已保存清单的查看流程

  **References**:
  - `app.js:332-601` — renderNewBook 及相关函数
  - `app.js:626+` — renderBookDetail
  - `app.js:566-580` — handleNewBookBack（待简化）
  - `app.js:582-601` — savePreviewToStorage（保留核心逻辑）

  **Acceptance Criteria**:
  - [ ] 按钮显示「生成预习本」
  - [ ] 点击后直接跳转清单页（无预览步骤）
  - [ ] 清单页有保存按钮（仅未保存时显示）
  - [ ] 已保存清单返回时不弹对话框
  - [ ] 未保存清单返回时弹确认对话框

  **QA Scenarios**:
  ```
  Scenario: 生成直接进入清单页
    Tool: Playwright
    Preconditions: 打开 #new-book，地点输入「唐山」，选5月
    Steps:
      1. page.goto('{BASE}/#new-book')
      2. 输入地点: page.fill('#locInput', '唐山')
      3. 点击5月按钮: page.click('[data-m="5"]'); page.click('#monthAllBtn') 两下切换
      4. 点击「生成预习本」: page.click('#generate')
      5. 等待跳转: page.waitForSelector('.bird-item', {timeout:5000})
    Expected Result: 页面跳转到清单页，URL 包含 #book?id=list_，显示鸟种列表
    Failure Indicators: 停留在新增页面，或显示预览区
    Evidence: .sisyphus/evidence/task-4-generate-flow.png

  Scenario: 未保存清单返回弹对话框
    Tool: Playwright
    Preconditions: 通过推荐生成了一个清单，未点保存
    Steps:
      1. 在清单页点击返回按钮
      2. page.waitForSelector('.modal-overlay', {timeout:3000})
    Expected Result: 显示确认对话框「确认返回 / 你还没有保存这个预习本」
    Evidence: .sisyphus/evidence/task-4-unsaved-dialog.png

  Scenario: 保存后不再弹对话框
    Tool: Playwright
    Preconditions: 清单页，点击了「保存预习本」
    Steps:
      1. page.click('text=保存预习本')
      2. 再次点击返回按钮: page.click('.page-header .ghost')
      3. page.waitForSelector('h1', {timeout:3000})  # 回到首页
    Expected Result: 直接返回首页，无弹窗
    Evidence: .sisyphus/evidence/task-4-saved-return.png
  ```

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 Task 5-9)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 10 (验证)
  - **Blocked By**: Task 2 (需要 occurrence 数据测试)

  **Commit**: YES
  - Message: `fix(ui): restore V1 generate flow, add save button on list page`
  - Files: `app.js`

- [x] 5. 修复保存按钮（localStorage 保护）

  **What to do**:
  - 在 `StorageService.saveList()` 加 try-catch
  - catch 到 `QuotaExceededError` 或一般错误时调用 `showModal()` 显示错误提示
  - 对存储的数据做体积预估：如果 `JSON.stringify(list).length > 500000`（约500KB），先警告
  - `getLists()` 也加 try-catch（防止损坏数据导致整个页面崩溃）
  - `getChecks()`/`getNotes()` 同理

  **Must NOT do**:
  - 不改变 localStorage key 结构
  - 不引入 IndexedDB（保持 V1 兼容）

  **References**:
  - `app.js:170-233` — StorageService
  - `app.js:582-601` — savePreviewToStorage
  - `app.js:566-580` — handleNewBookBack 中的保存按钮

  **Acceptance Criteria**:
  - [ ] localStorage 写入失败时显示错误提示（不是静默失败）
  - [ ] localStorage 读取失败时降级为空数组/空对象
  - [ ] 正常保存功能不受影响

  **QA Scenarios**:
  ```
  Scenario: 正常保存成功
    Tool: Playwright
    Preconditions: 生成一个清单
    Steps:
      1. 点击「保存预习本」
      2. page.waitForSelector('.bird-item', {timeout:5000})
      3. 检查 URL: page.url() 包含 #book?id=list_
    Expected Result: 页面为清单页，显示鸟种列表，无错误弹窗
    Evidence: .sisyphus/evidence/task-5-save-success.png

  Scenario: 损坏数据不崩溃
    Tool: Bash (Playwright setup)
    Preconditions: localStorage 中 birdPreviewBook:lists 设为非法 JSON
    Steps:
      1. page.evaluate(() => localStorage.setItem('birdPreviewBook:lists', 'NOT JSON'))
      2. page.goto('{BASE}/')
      3. page.waitForSelector('h1', {timeout:5000})
    Expected Result: 首页正常加载（最近清单为空），无白屏/报错
    Evidence: .sisyphus/evidence/task-5-corrupt-data.png
  ```

  **Parallelization**:
  - **Can Run In Parallel**: YES (与 Task 4,6-9)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 10
  - **Blocked By**: Task 4 (共用清单页逻辑)

  **Commit**: YES (与 Task 4 一起提交)
  - Files: `app.js`

- [x] 6. 简化鸣声播放器

  **What to do**:
  - 修改 `app.js` `renderSounds()`：
    - 去掉 `<strong>${esc(s.caption || s.type || "鸣声")}</strong>` 标题行
    - `<audio>` 加 `controlsList="nodownload noplaybackrate"`
    - 保留来源信息行（`<div class="small muted">`）
  - 如需要，`style.css` 调整 audio 元素样式确保移动端简洁

  **Must NOT do**:
  - 不删除来源出处（保留底部署名）
  - 不影响图片展示

  **References**:
  - `app.js:866-868` — renderSounds
  - `app.js:850` — 鸣声区域的 HTML

  **Acceptance Criteria**:
  - [ ] 鸣声区域无标题文字（不显示「鸣声」「叫声」等）
  - [ ] audio 元素含 `controlsList="nodownload noplaybackrate"`
  - [ ] 来源信息保留

  **QA Scenarios**:
  ```
  Scenario: 鸣声无标题和多余控件
    Tool: Playwright
    Preconditions: 打开一个有鸣声的鸟种详情页
    Steps:
      1. page.goto('{BASE}/#bird?list=...&bird=comkin1')
      2. 检查鸣声区域的 strong 标签: page.$$eval('details[open] summary', els => els.filter(e=>e.textContent.includes('鸣声')).length)
      3. 检查 audio 的 controlsList 属性: page.$eval('audio', el => el.getAttribute('controlsList'))
    Expected Result: 鸣声区域内无 strong 标签显示鸣声类型；controlsList 含 nodownload noplaybackrate
    Evidence: .sisyphus/evidence/task-6-audio.png
  ```

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 10
  - **Blocked By**: None

  **Commit**: YES (与 Task 4-5 一起)
  - Files: `app.js`, `style.css`(如有)

- [x] 7. 图片类型过滤 + Macaulay 优先

  **What to do**:
  - 编写 `scripts/filter_media.py`：
    - 读取 `data/media.json`
    - 标记 `source` 含 `Macaulay` 的为优先（照片来源）
    - Wikimedia 图片：检查 `type` 字段，无 type 或 type 不为 `photo` 的标记低优先级
    - 对每个鸟种，保留最多 3 张图片（Macaulay 优先，Wikimedia 补充）
    - 如果全部图片都疑似非照片，保留但标记 `note: "待确认是否为实物照片"`
  - 更新 `media.json`

  **Must NOT do**:
  - 不删除旧图片 URL（可能已在上一个版本中使用，只通过 type 降级）
  - 不引入图片下载/重新托管

  **References**:
  - `data/media.json` — 当前媒体数据
  - Macaulay API response 字段：`source: "ebird"`→标记为 Macaulay/照片

  **Acceptance Criteria**:
  - [ ] Macaulay 来源图片排前
  - [ ] 每鸟种最多 3 张
  - [ ] 可疑非照片图片标记 note

  **QA Scenarios**:
  ```
  Scenario: Macaulay 图片在前
    Tool: Bash
    Steps:
      1. python3 -c "
      import json; m=json.load(open('data/media.json'))
      for bid, data in list(m.items())[:10]:
          imgs=data.get('images',[])
          mac_first = all('Macaulay' in (img.get('source','')) for img in imgs[:min(2,len(imgs))]) if imgs else True
          if not mac_first: print(f'{bid}: Macaulay not first')"
    Expected Result: 无输出（所有鸟种 Macaulay 图片在前）
    Evidence: .sisyphus/evidence/task-7-image-order.txt
  ```

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 10
  - **Blocked By**: Task 3 (需要科名/鸟名修复后的 species)

  **Commit**: YES
  - Message: `fix(data): prioritize Macaulay photos, filter potential illustrations`
  - Files: `data/media.json`, `scripts/filter_media.py`

- [x] 8. locations.json 按 occurrence 重建

  **What to do**:
  - 编写 `scripts/rebuild_locations.py`
  - 从 `data/occurrences.json` 提取所有 `locationCode`
  - 与 `data/locations.json` 交叉：保留有 occurrence 的省/市
  - 原23条唐山手工数据：保留 河北省→唐山市 及其区县
  - 省级 occurrence：只保留省名+code，不生成无数据的城市
  - 移除所有无 occurrence 匹配的骨架数据

  **Must NOT do**:
  - 不删除 occurrence 中引用的地点

  **References**:
  - `data/occurrences.json` — locationCode 来源
  - `data/locations.json` — 现骨架数据

  **Acceptance Criteria**:
  - [ ] locations.json 中的省份均有对应 occurrence
  - [ ] 唐山市及区县保留
  - [ ] 无冗余区县（如北京只有东城海淀）

  **QA Scenarios**:
  ```
  Scenario: 地点与 occurrence 一致
    Tool: Bash
    Steps:
      1. python3 -c "
      import json
      occ=json.load(open('data/occurrences.json'))
      loc=json.load(open('data/locations.json'))
      occ_codes=set(o['locationCode'] for o in occ if o['locationCode'])
      # Flatten locations to get all codes
      def get_codes(items):
          codes=set()
          for i in items:
              codes.add(i['code'])
              if 'children' in i: codes.update(get_codes(i['children']))
          return codes
      loc_codes=get_codes(loc)
      orphan=occ_codes-loc_codes
      print(f'Orphan occurrence codes: {orphan}')"
    Expected Result: 无孤立的 occurrence code
    Evidence: .sisyphus/evidence/task-8-location-consistency.txt
  ```

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 10
  - **Blocked By**: Task 2 (需要 occurrence)

  **Commit**: YES
  - Message: `fix(data): rebuild locations.json from actual occurrences`
  - Files: `data/locations.json`, `scripts/rebuild_locations.py`

- [x] 9. 综合数据/展示修复

  **What to do**:
  - `data/taxonomy.json`：更新 orders 列表（按 species 实际目重建），更新 families 列表（中文科名）
  - `data/metadata.json`：更新 dataVersion 为 `v2-fix-2026-05-08`，更新 sources 列表
  - `data/similar.json`：确认无占位假数据（如 `"similarBirdId": "暂无可靠数据"`）
  - `app.js`：确认详情页 `formatTaxonomy()` 显示中文科名
  - `app.js`：`renderNewBook()` 中的 orderOptions 从 taxonomy.orders 生成，移除旧的 familyOptions/habitatOptions 残留
  - 清理 `app.js` 中不再使用的函数（如 `parseCategory()`、重复的 `getSelectedLocation()`）
  - `style.css`：如有繁体相关样式残留清理

  **Must NOT do**:
  - 不改变对外 API（分享 payload 格式等）

  **References**:
  - `data/taxonomy.json` — 需更新
  - `data/metadata.json` — 需更新版本
  - `app.js:332-500` — renderNewBook 清理
  - `app.js:698+` — formatTaxonomy

  **Acceptance Criteria**:
  - [ ] taxonomy.json orders 和 families 与实际 species 一致
  - [ ] dataVersion 已更新
  - [ ] 详情页科名显示中文
  - [ ] 无残留 dead code

  **QA Scenarios**:
  ```
  Scenario: taxonomy 与 species 一致
    Tool: Bash
    Steps:
      1. python3 -c "
      import json; s=json.load(open('data/species.json')); t=json.load(open('data/taxonomy.json'))
      sp_orders=set(x['order']['zh'] for x in s)
      tax_orders=set(o['zh'] for o in t.get('orders',[]))
      missing=sp_orders-tax_orders; print(f'Orders in species but not taxonomy: {missing}')"
    Expected Result: 无缺失
    Evidence: .sisyphus/evidence/task-9-taxonomy-consistency.txt

  Scenario: 详情页科名中文
    Tool: Playwright
    Steps:
      1. 打开鸟种详情页: page.goto('{BASE}/#bird?list=...&bird=rbbmag')
      2. 检查分类文字: page.textContent('.bird-classification')
    Expected Result: 含「鸦科」而非「Crows, Jays」
    Evidence: .sisyphus/evidence/task-9-family-zh-ui.png
  ```

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 10
  - **Blocked By**: Task 2, Task 3

  **Commit**: YES (与 Task 4-8 一起或单独)
  - Message: `fix: update taxonomy, metadata, clean dead code`
  - Files: `data/taxonomy.json`, `data/metadata.json`, `app.js`

- [x] 10. 本地全量验证

  **What to do**:
  - 运行数据一致性脚本：所有 JSON 合法；occurrence birdId 存在于 species；species family.zh 全中文；无繁体中文名
  - `node --check app.js` 语法检查
  - 启动本地 `python3 -m http.server 8000`
  - Playwright 回归验证：
    - 首页加载 → 推荐清单 → 输入「唐山」→ 5月 → 鸻形目 → 生成 → 应返回 7 种（V1 手工数据）
    - 录入清单 → 使用示例 → 匹配 → 三种演示鸟全部匹配
    - 清单页科名中文、保存按钮可用、点击保存跳转
    - 鸟种详情页鸣声简洁、科名中文
    - 返回未保存弹窗正确
  - 截图保存为证据

  **Must NOT do**:
  - 不修改任何代码（仅验证）

  **Acceptance Criteria**:
  - [ ] `node --check app.js` 通过
  - [ ] 全部 `data/*.json` 合法
  - [ ] 数据一致性脚本通过
  - [ ] Playwright 全流程通过（唐山5月7种、演示3种匹配）

  **QA Scenarios**:
  ```
  Scenario: JS 语法检查
    Tool: Bash
    Steps: node --check app.js
    Expected Result: 无输出（通过）
    Evidence: .sisyphus/evidence/task-10-syntax.txt

  Scenario: JSON 合法性
    Tool: Bash
    Steps: for f in data/*.json; do python3 -m json.tool "$f" > /dev/null && echo "$f OK" || echo "$f FAIL"; done
    Expected Result: 全部 OK
    Evidence: .sisyphus/evidence/task-10-json-valid.txt

  Scenario: 唐山 5月 鸻形目 = 7种
    Tool: Playwright
    Steps:
      1. page.goto('{BASE}/#new-book')
      2. page.fill('#locInput', '唐山'); page.click('.add-bird-item')  # 选建议
      3. 选5月、鸻形目
      4. page.click('#generate')
      5. page.waitForSelector('.bird-item')
      6. 检查数量: page.textContent('已观察 0 / 共')
    Expected Result: 显示「已观察 0 / 共 7 种」
    Evidence: .sisyphus/evidence/task-10-tangshan-may.png

  Scenario: 演示三鸟全匹配
    Tool: Playwright
    Steps:
      1. page.goto('{BASE}/#import-list')
      2. page.click('#demo'); page.click('#match')
      3. page.waitForSelector('#matchResults .match-item')
      4. 检查匹配结果数量
    Expected Result: 3种全部匹配（红嘴蓝鹊、白头鹎、普通翠鸟）
    Evidence: .sisyphus/evidence/task-10-demo-match.png
  ```

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 11 (必须通过才能部署)
  - **Blocked By**: Task 1-9

  **Commit**: NO (仅验证)

- [x] 11. 部署 + 线上回归验证

  **What to do**:
  - `git add` 所有修改文件
  - `git commit` 提交（见下方 Commit Strategy）
  - `git push origin main`
  - 等待 GitHub Pages build 完成
  - 线上 Playwright 验证：
    - `https://monomelemon.github.io/bird-preview-book/` 首页正常
    - 生成流程、录入匹配、唐山筛选 与本地一致
  - 确认无 console 错误

  **Must NOT do**:
  - 不部署 scripts/（仅本地用）
  - 不修改 GitHub Pages 配置

  **Acceptance Criteria**:
  - [ ] GitHub Pages build status: built
  - [ ] 线上页面可正常访问
  - [ ] 线上唐山5月=7种、演示3种匹配

  **QA Scenarios**:
  ```
  Scenario: 线上可访问
    Tool: Playwright
    Steps:
      1. page.goto('https://monomelemon.github.io/bird-preview-book/', {waitUntil:'domcontentloaded',timeout:30000})
      2. page.waitForSelector('h1', {timeout:15000})
      3. 检查标题: page.textContent('h1')
    Expected Result: 显示「观鸟预习本」
    Evidence: .sisyphus/evidence/task-11-live-home.png

  Scenario: 线上生成流程
    Tool: Playwright
    Steps: 同 Task 10，但 BASE=https://monomelemon.github.io/bird-preview-book
    Expected Result: 与本地一致
    Evidence: .sisyphus/evidence/task-11-live-generate.png
  ```

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: None (最后一步)
  - **Blocked By**: Task 10

  **Commit**: YES
  - Message: `release: V2 data and UI fixes - GBIF province+month, Chinese names, restore V1 flow`
  - Files: 全部修改文件

---

## Final Verification Wave

- [x] F1. **数据一致性审计** — `unspecified-high`
  运行 `python3 scripts/verify_data.py` 检查：
  occurrence 无全数组 national；23条唐山手工记录存在；family.zh 全中文；species 名全简体；V1 鸟种可匹配。
  Output: `checks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **UI 回归测试** — `unspecified-high` (+ Playwright)
  验证：生成→清单页→保存→详情页 完整流程；三种演示鸟导入匹配；唐山5月7种/9月23种；保存按钮正常；鸣声简化。
  Output: `scenarios [N/N pass] | VERDICT`

- [x] F3. **代码质量检查** — `quick`
  `node --check app.js`、JSON 合法性、CSS 无语法错误。
  Output: `Build [PASS/FAIL] | JSON [N valid/N] | VERDICT`

---

## Commit Strategy
- **Wave 1**: `fix(data): rebuild occurrences with GBIF province+month data`
- **Wave 2**: `fix(ui): restore V1 generate flow, fix save button, simplify audio`
- **Wave 3**: `chore: verify and deploy V2 fixes`

---

## Success Criteria

### 数据验证
```bash
python3 -c "import json; o=json.load(open('data/occurrences.json')); assert not all(x['locationLevel']=='national' for x in o)"
python3 -c "import json; s=json.load(open('data/species.json')); assert all(any('\u4e00'<=c<='\u9fff' for c in x['family']['zh']) for x in s)"
node --check app.js
```

### UI 验证 (Playwright)
- 生成「唐山·5月·鸻形目」→ 清单页显示 7 种
- 导入「普通翠鸟, 白头鹎, 红嘴蓝鹊」→ 3 种全部匹配
- 清单页科名显示中文
- 鸣声区域无标题文字、无下载按钮
- 保存按钮点击后跳转清单页
