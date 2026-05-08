# 观鸟预习本 V2：数据真实化与 UI 优化

## TL;DR

> **Quick Summary**: 对观鸟预习本进行 V2 升级：清洗假数据（出现概率、假分布信息），补全真实数据（Wikipedia 介绍/分布、Macaulay 鸣声/精选图片），优化 UI（分类多选下拉、保存-预览逻辑、删除确认、地点历史），并将鸟种库从河北 200 种扩展到全中国级（预计 1100-1500 种）。

> **Deliverables**:
> - 全中国鸟种基础名录（scripts 合并 eBird 各省 checklist）
> - Macaulay 鸣声（199+ 种有鸣声）
> - Macaulay 图片质量过滤（rating ≥4，成鸟优先，≥400px）
> - Wikipedia 中文描述 + 分布信息（繁转简）
> - 移除假数据：出现概率排序、假 distribution text
> - 分类多选下拉面板
> - 生成→预览→保存 三步逻辑
> - 删除图标/确认弹窗重设计
> - 地点历史最近 3 个
> - 目排序按图鉴惯例

> **Estimated Effort**: Large (~40-50min script + UI changes)
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Wave 1（脚本）→ Wave 2（UI）→ Wave 3（验证部署）

---

## Context

### Original Request
用户要求将《观鸟预习本》从 V1 河北演示版升级为全中国级观鸟预习工具，同时修复假数据、改进 UI 体验、补全多媒体和文字资料。

### Interview Summary

**Key Discussions**（18 项已确认任务）:
- UI 优化：移除出现概率排序、移除相似种对比、隐藏生境筛选、分类多选下拉、目排序调整、预览-保存逻辑、默认命名优化、删除图标/弹窗重设计、地点历史
- 数据真实化：Wikipedia 分布信息替换假 occurrence 数据、Wikipedia 详细信息繁转简、识别要点继续按现有方式补充
- 媒体扩充：Macaulay 鸣声、Macaulay 图片质量过滤（rating≥4/adult/≥400px）
- 鸟种扩展：eBird 多省 checklist 合并到全中国级（预估 1100-1500 种）

**Metis Review**（已纳入）:
- 定义“全中国”范围：大陆 eBird CN 子区域（CN-01 至 CN-34），不含台湾/香港/澳门独立区域
- 分波交付：数据脚本 → UI 变更 → 验证部署
- 所有生成数据需保留来源元数据（source name、URL、retrieval date）
- 静态 JSON 规模需验证移动端性能
- V1 localStorage 兼容：新增字段向后兼容，不变更现有结构
- 全部物种首次默认 `dataLevel: C`（基础名录），已有资料自动升为 B/A
- eBird checklist 中 subspecies/hybrid/spuh/domestic 类目自动排除
- Macaulay media 缺失 rating/age/dimensions 时使用安全默认值（不排除该条目）
- 空结果/过滤后无结果状态显示友好提示
- 分类全选时与全部相同效果（过滤逻辑使用空数组表示不过滤）

---

## Work Objectives

### Core Objective
将观鸟预习本从河北 200 种演示版升级为全中国级真实数据版本，同时优化 UI 和用户体验。

### Concrete Deliverables
- `data/species.json`：200 → ~1100-1500 种（全中国基线）
- `data/occurrences.json`：重写为 China-wide 记录，移除假 probabilityScore
- `data/media.json`：Macaulay 图片（质量过滤）+ Macaulay 鸣声 + Wikipedia 分布图外链
- `data/identification.json`：Wikipedia 介绍摘要（繁转简）
- `app.js`：UI 变更（分类下拉、保存预览、删除弹窗、地点历史）
- `style.css`：删除图标、下拉面板样式

### Definition of Done
- [ ] 全中国级推荐清单可生成（省级或全国查询均可得到有记录的结果）
- [ ] 出现概率排序选项已移除，来源文本改为 Wikipedia 分布描述
- [ ] Macaulay 鸣声可在详情页播放
- [ ] 分类多选下拉面板可正常使用
- [ ] 预览→保存→返回对话框逻辑正确
- [ ] 删除确认使用自定义弹窗
- [ ] 地点历史保留最近 3 个
- [ ] 详情页不显示假数据、无相似种区域、有 Wikipedia 详细介绍

### Must Have
- 所有数据来源可追溯（sourceRefs/sourceUrl/license/retrievedAt）
- eBird API key 不进入前端代码
- V1 localStorage 数据兼容
- 缺失资料显示“暂无可靠数据”

### Must NOT Have（Guardrails）
- 不编造鸟类资料
- 不部署 API key 到前端
- 不做用户账号/云同步
- 不做离线缓存 / PWA
- 不添加概率建模 / 分布图绘制
- 不对 1100+ 种全部手写识别要点
- 不使用浏览器原生 `confirm()` / `alert()`
- 不引入框架/构建工具

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: YES（node --check, python3 -m json.tool, Python 数据一致性脚本）
- **Automated tests**: NO（V1 前端无测试框架）
- **Framework**: 无

### QA Policy
每项任务通过以下方式验证：
- **数据质量**：Python 脚本校验 JSON 合法性、引用完整性、字段非空
- **功能行为**：Playwright 浏览器模拟用户操作，验证 UI 状态
- **前端语法**：`node --check app.js`
- **数据规模**：物种数、图片数、鸣声数统计

---

## Execution Strategy

### Parallel Execution Waves

> 数据脚本(不可以并行于自身，但数据清洗可与 UI 并行) → UI 代码 → 验证部署

```
Wave 1（数据脚本 - 可并行准备，顺序执行写入）:
├── Task 1: eBird China checklist 合并脚本 [deep]
├── Task 2: Macaulay 图片质量过滤脚本 [quick]
├── Task 3: Macaulay 鸣声批量获取脚本 [deep]
├── Task 4: Wikipedia 中文摘要获取脚本 [deep]
└── Task 5: 数据清洗：移除假数据 + 重建 occurrences [quick]

Wave 2（代码 - MAX PARALLEL）:
├── Task 6: 分类多选下拉面板 [visual-engineering]
├── Task 7: 预览-保存-返回对话框逻辑 [unspecified-high]
├── Task 8: 删除图标 + 自定义确认弹窗 [visual-engineering]
├── Task 9: 地点历史最近 3 个 [quick]
├── Task 10: 移除出现概率排序 [quick]
├── Task 11: 移除相似种对比区域 [quick]
├── Task 12: 隐藏生境筛选 [quick]
├── Task 13: 目排序调整 + 默认命名优化 [quick]
├── Task 14: 全国搜索 bug 修复 [quick]
└── Task 15: Wikipedia 分布信息 + 详情渲染 [unspecified-high]

Wave 3（部署）:
├── Task 16: 本地全量验证 [unspecified-high]
└── Task 17: 提交推送 + 线上验证 [quick]
```

### Critical Path
Task 1（合并全国名录）→ Task 2-5 依赖 species 列表 → Task 4/5 → Task 15 依赖 Wikipedia 数据 → Wave 3

### Parallel Speedup
Wave 2 中 10 个 task 全部可并行（不互依赖）。

---

## TODOs

- [ ] 1. **eBird China 全国鸟种合并脚本**

  **What to do**:
  - 读取 `data/species.json` 现有 200 种，记录已有 birdId/speciesCode
  - 通过 eBird API v2 `/ref/taxonomy/ebird` 获取全分类树
  - 用 eBird API `/product/spplist/{subRegionCode}` 拉取各省 checklist（覆盖 CN-01 至 CN-34 所有省/自治区/直辖市，不含 CN-40 台湾/CN-80 香港/CN-90 澳门）
  - 合并所有省级 speciesCode，去重
  - 对每个新 speciesCode，从 taxonomy 树中取出 `sciName`、`comName`（英文名）、`familyComName`、`familySciName`、`order`
  - 对每个新 species，通过 eBird taxonomy `zh` locale 回退获取中文名（调用 `https://api.ebird.org/v2/ref/taxonomy/ebird?fmt=json&locale=zh`）
  - 排除：subspecies（sciName 含 3+ 词且非 hybrid）、hybrid（category=hybrid）、spuh（category=spuh）、domestic（category=domestic）、slash（category=slash）
  - 生成 birdId：`speciesCode` 清理后的小写标识符
  - 写入 `data/species.json`：合并原有 200 种 + 新增物种，保留已有字段（dataLevel、aliases、sourceRefs），新物种默认 `dataLevel: "C"`、`aliases: []`、`sourceRefs: ["eBird API v2 taxonomy"]`
  - 同时写入 `speciesCode` 字段到每个 species 对象中
  - 更新 `data/metadata.json`：`dataVersion → "v2-china-2026-05-07"`，`sources` 追加 `"eBird API v2 (China provincial checklists)"`，`updatedAt` 更新
  - 脚本位置：`scripts/merge_china_species.py`，通过环境变量 `EBIRD_API_KEY` 读取 key

  **Must NOT do**:
  - 不要把 API key 写入前端文件
  - 不要对港澳台单独拉取
  - 不要丢弃已有的 200 种数据

  **Recommended Agent Profile**:
  - **Category**: `deep` — 需要正确处理 eBird API 多省查询、去重、taxonomy 映射
  - **Skills**: `[]` — Python standard library 足够

  **Parallelization**:
  - **Can Run In Parallel**: NO（必须先完成，后续所有任务依赖 species 列表）
  - **Parallel Group**: Wave 1 sequential
  - **Blocks**: Tasks 2, 3, 4, 5, 15
  - **Blocked By**: None

  **References**:
  - `data/species.json` — 现有 200 种结构模板
  - `scripts/update_media_and_names.py:lines 108-120` — eBird taxonomy API 调用模式
  - eBird API docs: `https://documenter.getpostman.com/view/664302/S1ENwy59` — `/product/spplist` 端点
  - `data/metadata.json` — 版本号更新目标

  **Acceptance Criteria**:
  - [ ] 脚本执行完成无报错
  - [ ] `data/species.json` 物种数从 200 增长到 1000-1500 区间
  - [ ] 无重复 birdId
  - [ ] 所有 species 有 `speciesCode` 字段
  - [ ] 无 subspecies/hybrid/spuh/domestic 类目
  - [ ] 原有 200 种数据完整保留
  - [ ] `python3 -m json.tool data/species.json` 通过

  **QA Scenarios**:

  ```
  Scenario: 全国 species.json 合法且完整
    Tool: Bash (python3)
    Steps:
      1. python3 -c "import json; s=json.load(open('data/species.json')); print(len(s))"
      2. python3 -c "import json; s=json.load(open('data/species.json')); ids=[x['birdId'] for x in s]; assert len(ids)==len(set(ids)); print('no dupes')"
      3. python3 -c "import json; s=json.load(open('data/species.json')); codes=[x.get('speciesCode') for x in s]; print(f'{sum(1 for c in codes if c)}/{len(s)} have speciesCode')"
    Expected Result: 物种数在 1000-1500，无重复 birdId，95%+ 有 speciesCode
    Evidence: .sisyphus/evidence/task-1-species-count.json

  Scenario: 无 subspecies/hybrid/spuh
    Tool: Bash (python3)
    Steps:
      1. python3 -c "import json,re; s=json.load(open('data/species.json')); bad=[(x['birdId'],x['scientificName']) for x in s if len(x['scientificName'].split())>=4]; print(bad[:20], len(bad))"
    Expected Result: 无 4 词及以上学名（表明无 subspecies）
    Evidence: .sisyphus/evidence/task-1-no-subspecies.txt
  ```

  **Commit**: YES
  - Message: `feat(data): expand to China-wide species via eBird provincial checklists`
  - Files: `data/species.json`, `data/metadata.json`, `scripts/merge_china_species.py`

- [ ] 2. **Macaulay 图片质量过滤脚本**

  **What to do**:
  - 读取 `data/media.json` 现有数据
  - 对每个有 Macaulay 图片的 species：检查每张图的 metadata
  - 使用 Macaulay search API 返回字段过滤：`rating`（数字）≥ 4.0、`age`（可选）= "Adult"、`width`（可选）≥ 400
  - 如果 rating/age/width 字段缺失：使用安全默认值（不因缺失而排除该图）——仅在有明确低质量标志时移除
  - 过滤后，若某 species 图片少于 1 张，保留原有图片（不过滤）
  - 对过滤后仍少于 3 张的 species，重新调用 Macaulay API 补齐（使用过滤条件）
  - 图片限制每种最多 3 张
  - 脚本位置：`scripts/filter_macaulay_photos.py`

  **Must NOT do**:
  - 不要把仅有 1-2 张图的物种变成 0 图
  - 不要修改非 Macaulay 来源的图片（Wikimedia/Wild Beijing 保留）

  **Recommended Agent Profile**:
  - **Category**: `quick` — 逻辑明确的过滤+补全循环
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES（Task 1 完成后可与 Task 3/4 并行）
  - **Parallel Group**: Wave 1（with Tasks 3, 4, 5）
  - **Blocks**: Task 16
  - **Blocked By**: Task 1

  **References**:
  - `data/media.json` — 当前 576 Macaulay 图片结构
  - `scripts/update_media_and_names.py:lines 180-210` — Macaulay API 调用模式
  - Macaulay API response fields: `rating`, `age`, `width` on each content item

  **Acceptance Criteria**:
  - [ ] 过滤后 90%+ 物种有至少 1 张图
  - [ ] 无物种从有图变为 0 图
  - [ ] 每物种最多 3 张
  - [ ] 图片 source 字段仍标记为 "Macaulay Library / eBird"

  **QA Scenarios**:

  ```
  Scenario: 图片质量统计
    Tool: Bash (python3)
    Steps:
      1. python3 -c "import json; m=json.load(open('data/media.json')); imgs=sum(len(v.get('images',[])) for v in m.values()); count=sum(1 for v in m.values() if v.get('images')); print(f'{count} species with images, {imgs} total')"
      2. python3 -c "import json; m=json.load(open('data/media.json')); zero=[k for k,v in m.items() if not v.get('images')]; print(f'{len(zero)} species with 0 images')"
    Expected Result: 90%+ 有图，0 图物种在可接受范围
    Evidence: .sisyphus/evidence/task-2-image-stats.json
  ```

  **Commit**: YES
  - Message: `feat(data): filter Macaulay photos by quality rating`
  - Files: `data/media.json`, `scripts/filter_macaulay_photos.py`

- [ ] 3. **Macaulay 鸣声批量获取脚本**

  **What to do**:
  - 读取 `data/species.json` 获取最新 speciesCode 列表
  - 读取 `data/media.json` 现有 sounds 数据
  - 对没有 sounds 的 species，调用 Macaulay search API：`mediaType=audio&taxonCode={code}&pageSize=3`
  - 每条录音保存字段：`url`（`largeUrl` 或 `mediaUrl`）、`type: "audio"`、`caption: {chineseName}`、`source: "Macaulay Library / eBird"`、`sourceUrl`（specimenUrl）、`author`（userDisplayName）、`license`（licenseType）
  - 每种最多 2 条录音
  - 对已有 1 条的补齐到 2 条
  - 并发获取（10 线程），打印进度
  - 脚本位置：`scripts/fetch_macaulay_audio.py`

  **Must NOT do**:
  - 不删除已有 sounds
  - 不覆盖非 Macaulay 来源的鸣声

  **Recommended Agent Profile**:
  - **Category**: `deep` — 需要处理大量并发 API 请求和错误重试
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES（Task 1 完成后可与 Task 2/4/5 并行）
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 16
  - **Blocked By**: Task 1

  **References**:
  - `scripts/update_media_and_names.py:lines 170-220` — Macaulay API 并发模式
  - Macaulay API: `https://search.macaulaylibrary.org/api/v1/search?mediaType=audio&taxonCode=...`

  **Acceptance Criteria**:
  - [ ] 70%+ 物种有至少 1 条鸣声
  - [ ] 每种最多 2 条
  - [ ] sounds 每条有完整字段

  **QA Scenarios**:

  ```
  Scenario: 鸣声数量统计
    Tool: Bash (python3)
    Steps:
      1. python3 -c "import json; m=json.load(open('data/media.json')); snd=sum(len(v.get('sounds',[])) for v in m.values()); count=sum(1 for v in m.values() if v.get('sounds')); print(f'{count} species with sounds, {snd} total')"
    Expected Result: 物种的 70%+ 有鸣声
    Evidence: .sisyphus/evidence/task-3-audio-stats.json
  ```

  **Commit**: YES
  - Message: `feat(data): add Macaulay audio sounds for all species`
  - Files: `data/media.json`, `scripts/fetch_macaulay_audio.py`

- [ ] 4. **Wikipedia 中文摘要获取脚本**

  **What to do**:
  - 读取 `data/species.json` 获取所有 speciesCode 和 chineseName
  - 对每个 species，使用 Wikipedia API `action=query&prop=extracts&exintro&explaintext&titles={chineseName}` 获取中文摘要
  - 若中文名无结果，降级尝试学名（scientificName），再降级尝试英文名
  - 摘要内容繁转简（使用脚本内置映射，同 `update_media_and_names.py`）
  - 限制摘要长度：保留前 500 字
  - 写入 `data/identification.json`：对尚未有识别要点的 species，设置 `keyPoints: []`（待后续补充），`morphology: ""`，`habitat: ""`，`behavior: ""`，`sourceRefs: ["Wikipedia - {pageTitle}"]`，`updatedAt: "2026-05-07"`
  - 将 Wikipedia 摘要存入 `data/species.json` 的扩展字段 `description`（每个 species 对象新增可选字段 `description: {text, source, sourceUrl, license, retrievedAt}`）
  - 同时提取分布相关 sentence：在摘要中搜索含"分布"/"见于"/"栖息"的句子，写入 `data/species.json` 的 `distributionText` 字段
  - 脚本位置：`scripts/fetch_wikipedia_descriptions.py`

  **Must NOT do**:
  - 不覆盖已有的 identification keyPoints（保留人工编写的 13 种识别要点）
  - 不对没有 Wikipedia 页面的物种编造描述
  - 摘要必须标注 CC BY-SA 许可

  **Recommended Agent Profile**:
  - **Category**: `deep` — 需要处理 Wikipedia API 和大量数据
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES（Task 1 完成后可与 Task 2/3/5 并行）
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 15
  - **Blocked By**: Task 1

  **References**:
  - `scripts/update_media_and_names.py:lines 23-39` — 繁简字符映射表
  - Wikipedia API: `https://zh.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles=...&format=json&origin=*`
  - `data/species.json` — 需要新增 `description` 和 `distributionText` 字段

  **Acceptance Criteria**:
  - [ ] 50%+ 物种有 Wikipedia 摘要
  - [ ] 所有摘要已繁转简
  - [ ] 最大 500 字
  - [ ] 每条有 sourceUrl 和 license 字段

  **QA Scenarios**:

  ```
  Scenario: Wikipedia 覆盖统计
    Tool: Bash (python3)
    Steps:
      1. python3 -c "import json; s=json.load(open('data/species.json')); d=[x for x in s if x.get('description',{}).get('text')]; print(f'{len(d)} species with description')"
      2. python3 -c "import json; s=json.load(open('data/species.json')); d=[x for x in s if x.get('distributionText')]; print(f'{len(d)} species with distribution text')"
    Expected Result: 50%+ 有描述和分布文本
    Evidence: .sisyphus/evidence/task-4-wikipedia-stats.json
  ```

  **Commit**: YES
  - Message: `feat(data): add Wikipedia Chinese summaries and distribution text`
  - Files: `data/species.json`, `data/identification.json`, `scripts/fetch_wikipedia_descriptions.py`

- [ ] 5. **数据清洗：移除假数据 + 重建 occurrences**

  **What to do**:
  - 从 `data/occurrences.json` 移除所有 `probabilityScore` 字段（或设为 null）
  - 为所有 occurrence 条目标记 `retrievedAt: "2026-05-07"`
  - 保持所有 occurrence 的 `sourceRefs` 链接完整
  - 在 `data/species.json` 中添加 `distributionText` 字段（已有者保留，无者留空字符串）
  - 为 `data/species.json` 所有条目统一更新 `updatedAt: "2026-05-07"`
  - 更新 `data/taxonomy.json`：调整 orders 的 `sortOrder` 为新顺序（雁形目=10、䴙䴘目=20、鹤形目=30、鸻形目=40、鹈形目=50、鹰形目=60、佛法僧目=70、雀形目=80）
  - 更新 `data/taxonomy.json` 的 `version` 为 `"v2-china-2026-05-07"`
  - 分类全选"全部"时默认生成空数组 filters（不用遍历判断全选），保持现有过滤逻辑不变
  - 脚本位置：`scripts/clean_legacy_data.py`

  **Must NOT do**:
  - 不删除 occurrence 条目
  - 不修改 species 中的 `dataLevel`、`sourceRefs`、`aliases`（保持从 Task 1 来的状态）

  **Recommended Agent Profile**:
  - **Category**: `quick` — 数据清理，逻辑简单
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES（Task 1 完成后可与 Task 2/3/4 并行）
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 15, 16
  - **Blocked By**: Task 1

  **References**:
  - `data/occurrences.json` — 当前 198 条记录
  - `data/taxonomy.json` — orders 列表需重排
  - `data/species.json` — 需要 `distributionText` 字段

  **Acceptance Criteria**:
  - [ ] occurrences 中无 `probabilityScore` 字段
  - [ ] taxonomy orders sortOrder 为新顺序
  - [ ] species 所有条目有 `distributionText` 字段（允许空字符串）

  **QA Scenarios**:

  ```
  Scenario: 无假 probability 数据
    Tool: Bash (python3)
    Steps:
      1. python3 -c "import json; o=json.load(open('data/occurrences.json')); bad=[x for x in o if x.get('probabilityScore') is not None]; print(f'{len(bad)} bad entries')"
    Expected Result: 0 bad entries
    Evidence: .sisyphus/evidence/task-5-no-prob.txt

  Scenario: 目顺序正确
    Tool: Bash (python3)
    Steps:
      1. python3 -c "import json; t=json.load(open('data/taxonomy.json')); [print(o['zh'],o['sortOrder']) for o in t['orders']]"
    Expected Result: 雁形目=10, 䴙䴘目=20, 鹤形目=30, 鸻形目=40, 鹈形目=50, 鹰形目=60, 佛法僧目=70, 雀形目=80
    Evidence: .sisyphus/evidence/task-5-order-sort.txt
  ```

  **Commit**: YES
  - Message: `fix(data): remove fake probability data and reorder taxonomy`
  - Files: `data/occurrences.json`, `data/taxonomy.json`, `data/species.json`, `scripts/clean_legacy_data.py`

---

- [ ] 6. **分类多选下拉面板**

  **What to do**:
  - 替换 `renderNewBook()` 中当前的 `.filter-grid` 按钮网格
  - 新增一个自定义下拉多选组件：
    - 点击触发按钮显示 "N 项已选"（或 "全部目"）
    - 弹出面板显示所有 orders（从 `taxonomy.orders` 读取），每个前面有 checkbox
    - 选中的项目带有 `.active` 样式
    - "全部目" 选项全选/反选所有
    - 点击面板外部关闭面板
    - 面板可视区域不足时自动上移
  - 生境面板同逻辑但默认隐藏（`style="display:none"`）
  - 保留现有的 `buildFilters()` 逻辑
  - 修改 `syncTitle()`：全选时不追加 "全部分类" 后缀
  - CSS：新增 `.multi-select-dropdown`、`.multi-select-panel`、`.multi-select-item` 样式；复用 `.pill` 的 active 色

  **Must NOT do**:
  - 不使用原生 `<select multiple>`（样式不可控）
  - 不改变 filters 生成逻辑（空数组 = 全选 = 不过滤）

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering` — UI 交互密集型
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES（所有 Wave 2 tasks 可并行）
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16
  - **Blocked By**: None

  **References**:
  - `app.js:lines 291-354` — 当前 `renderNewBook()` 分类 UI
  - `app.js:lines 440-480` — `buildFilters()` / `setupMultiSelectGrid()`
  - `style.css:lines 301-310` — 当前 `.month-grid` / `.filter-grid` 样式

  **Acceptance Criteria**:
  - [ ] 分类按目显示，可多选
  - [ ] "全部目" 选项一键全选/取消
  - [ ] 点击面板外关闭
  - [ ] 选中项数显示在触发按钮上
  - [ ] 生境面板不可见（display:none）
  - [ ] 全选时标题不追加分类后缀

  **QA Scenarios**:

  ```
  Scenario: 分类多选面板操作
    Tool: Playwright
    Steps:
      1. 打开 http://localhost:8000/#new-book
      2. 点击分类触发按钮
      3. 确认面板弹出，显示所有目 + "全部目"
      4. 点击 鸻形目，确认只选中该目，按钮文字为 "鸻形目"
      5. 点击 "全部目"，确认所有目被选中
      6. 点击面板外部，面板关闭
      7. 检查标题中是否不含 "全部分类"
    Expected Result: 按钮文字正确反映选中项数；全选时标题简化
    Evidence: .sisyphus/evidence/task-6-category-dropdown.png

  Scenario: 生境筛选不可见
    Tool: Playwright
    Steps:
      1. 检查 #habitatGrid 是否 display:none
    Expected Result: 生境筛选不可见
    Evidence: .sisyphus/evidence/task-6-habitat-hidden.png
  ```

  **Commit**: YES
  - Message: `feat(ui): multi-select dropdown category filter, hide habitat`
  - Files: `app.js`, `style.css`

- [ ] 7. **预览-保存-返回对话框逻辑**

  **What to do**:
  - 修改 `generateRecommendedList()` / 生成按钮逻辑：
    - 点击"生成预习本" → 生成 birdIds 并跳转到预览模式（新 route `preview?id=...` 或临时渲染）
    - 预览模式下清单不保存到 localStorage，页面顶部显示"预览中"标识
    - 预览页底部有"保存预习本"按钮和"放弃"按钮
    - 点击"保存" → 写入 localStorage → 跳转到清单详情页
    - 点击"放弃" → 返回新增预习本页
    - 若用户在预览模式下点击返回按钮或浏览器后退 → 弹出自定义对话框："是否保存？ 保存 / 不保存 / 取消"
  - 自定义对话框组件：覆盖全屏半透明背景 + 居中白色卡片 + 标题 + 文字 + 三个按钮
  - CSS 类 `.modal-overlay`、`.modal-box`
  - 预览页清单数据暂存到 `state.previewList`（不写入 localStorage 直到显式保存）

  **Must NOT do**:
  - 不使用浏览器原生 `confirm()`
  - 不在生成时自动保存（必须用户显式确认）
  - 不影响现有分享和导入清单的保存逻辑

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` — 涉及路由和 localStorage 交互
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16
  - **Blocked By**: None

  **References**:
  - `app.js:lines 392-407` — 当前生成按钮逻辑
  - `app.js:lines 140-193` — StorageService API

  **Acceptance Criteria**:
  - [ ] 生成后进入预览模式（无本地保存）
  - [ ] 预览页有"保存"和"放弃"按钮
  - [ ] 保存后跳转清单详情
  - [ ] 放弃后返回新增预习本页
  - [ ] 返回时弹出自定义对话框
  - [ ] 对话框三种选项均正确响应

  **QA Scenarios**:

  ```
  Scenario: 生成-预览-保存流程
    Tool: Playwright
    Steps:
      1. 打开 #new-book，选择唐山市、5月、鸻形目，点击生成
      2. 确认进入预览页，显示鸟种列表，顶部有"预览中"
      3. 检查 localStorage 是否无新清单（预览未保存）
      4. 点击"保存预习本"
      5. 确认跳转到清单详情页，localStorage 有新清单
    Expected Result: localStorage 仅在点击保存后才写入
    Evidence: .sisyphus/evidence/task-7-save-flow.png

  Scenario: 返回-对话框-放弃
    Tool: Playwright
    Steps:
      1. 生成预览后点击浏览器返回
      2. 自定义对话框出现
      3. 点击"不保存"
      4. 确认返回新增预习本页，localStorage 无新清单
    Expected Result: 无原生 confirm()，自定义对话框正确
    Evidence: .sisyphus/evidence/task-7-discard-dialog.png
  ```

  **Commit**: YES
  - Message: `feat(ui): preview-save-return dialog flow`
  - Files: `app.js`, `style.css`

- [ ] 8. **删除图标 + 自定义确认弹窗**

  **What to do**:
  - 替换 `renderHome()` 中最近清单的删除图标：
    - 从 `🗑` emoji 改为 CSS 绘制的简约垃圾箱图标
    - 白色底 + 红色线条（2px 笔画）
    - 使用 CSS 或 inline SVG
  - 替换 `deleteRecentList()` 中的 `confirm()` 为自定义弹窗
    - 复用 Task 7 的 `.modal-overlay` / `.modal-box` 样式
    - 弹窗文案："确定删除「{清单名}」？已观察和笔记也会一并删除。"
    - 按钮："删除（红色）"、"取消"
  - 同时修改清单详情页中可能的重命名/删除逻辑（若有 `confirm()` 调用）

  **Must NOT do**:
  - 不使用 emoji
  - 不使用浏览器 `confirm()`

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering` — 图标 + 弹窗 UI
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16
  - **Blocked By**: None

  **References**:
  - `app.js:lines 218-241` — `renderHome()` 删除图标
  - `app.js:lines 243-251` — `deleteRecentList()` 当前使用 `confirm()`
  - `style.css:lines 324-338` — `.swipe-delete` 样式

  **Acceptance Criteria**:
  - [ ] 删除图标为 CSS/SVG 简约风格（白底+红线）
  - [ ] 删除确认弹窗为自定义组件
  - [ ] "删除"按钮为红色，"取消"按钮为次要样式
  - [ ] 删除后清单从列表消失

  **QA Scenarios**:

  ```
  Scenario: 删除确认自定义弹窗
    Tool: Playwright
    Steps:
      1. 打开首页，确认有最近清单
      2. 左滑露出删除图标，点击
      3. 确认自定义弹窗显示（白色卡片 + 清单名 + 两个按钮）
      4. 点击"取消"，清单仍存在
      5. 再次左滑删除，点击"删除"
      6. 确认清单已删除
    Expected Result: 全程无原生 confirm() 弹窗
    Evidence: .sisyphus/evidence/task-8-delete-dialog.png
  ```

  **Commit**: YES
  - Message: `feat(ui): red-line delete icon and custom confirmation dialog`
  - Files: `app.js`, `style.css`

- [ ] 9. **地点历史最近 3 个**

  **What to do**:
  - 在 `StorageService` 中新增方法 `getLocationHistory()` / `addLocationHistory(locationText)`
  - 每次成功生成清单时，将地点文本（`locInput.value` 或 `_locationMatch.name`）保存到 `birdPreviewBook:locationHistory`（localStorage key）
  - 历史保留最近 3 个，去重（同一地点不重复），最新的排前面
  - 在 `renderNewBook()` 中：`#locInput` 获得焦点时，如果输入为空，显示最近 3 个地点建议
  - 展示方式：`#locSuggest` 区域，历史地点带一个"历史"小标签
  - 点击历史地点自动填充并选中

  **Must NOT do**:
  - 不覆盖现有地点搜索建议
  - 不保存包含敏感信息的地点文本

  **Recommended Agent Profile**:
  - **Category**: `quick` — 逻辑简单清晰
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16
  - **Blocked By**: None

  **References**:
  - `app.js:lines 140-193` — StorageService
  - `app.js:lines 369-390` — 地点输入/建议逻辑
  - `app.js:lines 392-407` — 生成按钮（在此处写入历史）

  **Acceptance Criteria**:
  - [ ] 生成清单后保存地点
  - [ ] 历史不超过 3 个
  - [ ] 点击输入框显示历史
  - [ ] 重复地点不重复显示

  **QA Scenarios**:

  ```
  Scenario: 地点历史显示和点击
    Tool: Playwright
    Steps:
      1. 生成 3 个不同地点的清单（唐山、北京、全国）
      2. 回到 #new-book，点击地点输入框
      3. 确认最近 3 个地点显示在下拉建议中
      4. 点击"唐山市"，确认输入框自动填充
      5. 用相同地点再生成一次
      6. 确认历史列表中唐山仍在第一位（去重，移至最新）
    Expected Result: 最近 3 个地点建议正确
    Evidence: .sisyphus/evidence/task-9-location-history.png
  ```

  **Commit**: YES
  - Message: `feat(ui): location history (last 3)`
  - Files: `app.js`

---

- [ ] 10. **移除出现概率排序选项**

  **What to do**:
  - 从 `renderBookDetail()` 的 `sortOptions` 中删除 `{ value: "probability", label: "按出现概率" }` 条目
  - 删除 `hasProbabilityData()` 函数及相关调用
  - 排序 `<select>` 只剩：按分类地位、按观察状态、按中文名

  **Must NOT do**:
  - 不删除 occurrence 数据（保留但不用概率排序）

  **Recommended Agent Profile**:
  - **Category**: `quick` — 单行删除
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16
  - **Blocked By**: None

  **References**:
  - `app.js:lines 579-586` — `sortOptions` 定义

  **QA Scenarios**:

  ```
  Scenario: 排序选项无 按出现概率
    Tool: Playwright
    Steps:
      1. 打开清单详情页
      2. 点击排序下拉
      3. 确认选项仅有 按分类地位、按观察状态、按中文名
    Expected Result: 无"按出现概率"选项
    Evidence: .sisyphus/evidence/task-10-no-prob-sort.png
  ```

  **Commit**: NO（合并到 Task 13 一起提交）

- [ ] 11. **移除相似种对比区域**

  **What to do**:
  - 从 `renderBirdDetail()` 中删除相似种对比的 `<details>` 区块
  - 搜索 `similar` 相关代码，确保详情页不再渲染相似种
  - 保留 `data/similar.json`（可留空数组，不删除文件）

  **Must NOT do**:
  - 不删除 `data/similar.json` 文件

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16
  - **Blocked By**: None

  **References**:
  - `app.js:lines 800-850` 区间 — 鸟种详情页渲染（搜索 `similar` 相关代码段）

  **QA Scenarios**:

  ```
  Scenario: 详情页无相似种区域
    Tool: Playwright
    Steps:
      1. 打开鸟种详情页
      2. 确认页面中不包含"相似种"文字
    Expected Result: 无相似种对比区域
    Evidence: .sisyphus/evidence/task-11-no-similar.png
  ```

  **Commit**: NO（合并到 Task 13）

- [ ] 12. **隐藏生境筛选**

  **What to do**:
  - 在 `renderNewBook()` 中，设置生境区域 `#habitatGrid` 为 `style="display:none"`
  - 确保 `buildFilters()` 中 habitats 始终输出空数组
  - 确保 `syncTitle()` 中不出现 "全部生境" 文字

  **Must NOT do**:
  - 不删除 habitats 数据
  - 不删除 HTML 结构（只隐藏），便于未来恢复

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16
  - **Blocked By**: None（但 Task 6 可能同时修改此区域；若 Task 6 已合并隐藏到分类下拉中，此 task 可跳过）

  **QA Scenarios**:

  ```
  Scenario: 生境筛选不可见
    Tool: Playwright
    Steps:
      1. 打开 #new-book
      2. 检查 #habitatGrid 是否不可见
    Expected Result: 生境筛选区域不可见
    Evidence: .sisyphus/evidence/task-12-habitat-hidden.png
  ```

  **Commit**: NO（合并到 Task 6）

- [ ] 13. **目排序调整 + 默认命名优化**

  **What to do**:
  - 确认 `data/taxonomy.json` 的 `sortOrder` 为：雁形目=10、䴙䴘目=20、鹤形目=30、鸻形目=40、鹈形目=50、鹰形目=60、佛法僧目=70、雀形目=80（已在 Task 5 完成）
  - 修改 `syncTitle()`：分类全选时只输出 `地点 · 时间`，不追加分类后缀
  - 修改 `syncTitle()`：生境（如存在）全选时也不追加

  **Must NOT do**:
  - 不改变现有 taxonomy.json 结构

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16
  - **Blocked By**: Task 5（需 taxonomy sortOrder 先调整好）

  **References**:
  - `app.js:lines 335-365` — `syncTitle()` / `filterPartLabel()`

  **QA Scenarios**:

  ```
  Scenario: 分类全选时标题简化
    Tool: Playwright
    Steps:
      1. 打开 #new-book，选择唐山、5月，分类和生境全部选中
      2. 检查标题输入框
    Expected Result: "唐山市 · 5月"（无"全部分类"或"全部"后缀）
    Evidence: .sisyphus/evidence/task-13-title-simplified.png
  ```

  **Commit**: YES（与 Tasks 10, 11 合并提交）
  - Message: `fix(ui): remove probability sort, similar species, optimize title naming`
  - Files: `app.js`, `style.css`

- [ ] 14. **全国/省/市搜索 bug 修复**

  **What to do**:
  - 修改 `matchLocation()` 函数：
    - 当 `location.provinceCode` 为空（全国范围）时，匹配所有 occurrence（return true）
    - 当只有 provinceCode 时，匹配所有该省及其下属市的 occurrence
  - 修改 `generateRecommendedList()` 中地点匹配逻辑：
    - 全国范围不过滤 occurrence（所有记录都匹配）
    - 省级范围匹配 `provinceCode` 相等或该省的市级记录

  **Must NOT do**:
  - 不改变 occurrence 数据结构

  **Recommended Agent Profile**:
  - **Category**: `quick` — 单函数修复
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 16
  - **Blocked By**: None

  **References**:
  - `app.js:lines 467-472` — `matchLocation()` 当前实现
  - `app.js:lines 449-465` — `generateRecommendedList()`

  **QA Scenarios**:

  ```
  Scenario: 全国搜索返回全网记录
    Tool: Playwright
    Steps:
      1. 打开 #new-book，不清地点输入框
      2. 选择全年，全部分类
      3. 点击生成
      4. 确认清单有鸟种（非空）
    Expected Result: 全国搜索不返回 0 种
    Evidence: .sisyphus/evidence/task-14-national-search.png
  ```

  **Commit**: NO（合并到 Wave 2 commit）

- [ ] 15. **Wikipedia 分布信息 + 详情页渲染**

  **What to do**:
  - 修改 `renderBirdDetail()`：详情页底部新增"分布信息"折叠区域
    - 内容取自 `species.distributionText`（Wikipedia 分布描述，Task 4 已写入）
    - 若无 distributionText，显示"暂无可靠分布信息"
  - 修改 `renderBirdDetail()`：详情页底部新增"详细信息"折叠区域
    - 内容取自 `species.description.text`（Wikipedia 摘要，Task 4 已写入）
    - 显示来源链接：Wikipedia 页面 URL
    - 显示许可：CC BY-SA
    - 若摘要超 500 字，显示"展开更多"按钮
  - 移除旧 occurrence 的 sourceRefs 作为分布信息

  **QA Scenarios**:
  ```
  Scenario: 详情页 Wikipedia 分布信息和详细信息
    Tool: Playwright
    Steps:
      1. 打开任何鸟种详情页（有 Wikipedia 数据的）
      2. 展开"分布信息"折叠区，确认中文分布描述（如"分布于华北和华东"）
      3. 展开"详细信息"折叠区，确认中文摘要 + Wikipedia 来源链接
    Expected Result: 分布和详细信息均来自 Wikipedia，带来源标注
    Evidence: .sisyphus/evidence/task-15-distribution-details.png
  ```

  **Commit**: YES — `feat(ui): Wikipedia description and distribution in detail page`
  - **Files**: `app.js`

- [ ] 16. **本地全量验证**

  **What to do**:
  - 运行 `node --check app.js`，验证所有 `data/*.json` 为合法 JSON
  - 运行数据一致性 Python 脚本
  - 统计物种数、图片数、鸣声数、Wikipedia 覆盖率
  - 启动本地 http server + Playwright 验证核心流程

  **QA Scenarios**:

  ```
  Scenario: JSON 文件合法性与数据一致性
    Tool: Bash (python3)
    Steps:
      1. for f in data/*.json; do python3 -m json.tool "$f" >/dev/null || echo "INVALID: $f"; done
      2. python3 -c "import json,pathlib; p=pathlib.Path('data'); s=json.loads((p/'species.json').read_text()); o=json.loads((p/'occurrences.json').read_text()); m=json.loads((p/'media.json').read_text()); ids={x['birdId'] for x in s}; occ_bad=[x for x in o if x.get('sourceRefs') and not isinstance(x['sourceRefs'],list)]; [print(f'{x[\"birdId\"]}: sourceRefs invalid') for x in occ_bad]; [print(f'{x[\"birdId\"]}: bad reliability') for x in o if x.get('reliability') not in ('high','medium')]; [print(f'{x[\"birdId\"]}: bad months') for x in o if not x.get('months')]; print(f'{len(s)} species, {len(o)} occurrences, {len(m)} media keys, {len(occ_bad)} bad sourceRefs')"
    Expected Result: 所有 JSON 合法；无 bad sourceRefs/bad reliability/bad months；species 1100-1500
    Evidence: .sisyphus/evidence/task-16-consistency.txt

  Scenario: app.js 语法检查
    Tool: Bash
    Steps:
      1. node --check app.js
    Expected Result: 无输出（无语法错误）
    Evidence: .sisyphus/evidence/task-16-syntax.txt

  Scenario: 核心流程 Playwright 验证
    Tool: Playwright
    Steps:
      1. 打开 http://localhost:8000/ 确认首页渲染
      2. 打开 #new-book 确认分类多选下拉可见
      3. 生成全国全年推荐清单，确认 birdIds 非空
      4. 打开清单详情页，确认中文科名显示
      5. 打开任一鸟种详情页，确认 Wikipedia 分布/详细信息区存在
      6. 确认 Macaulay 鸣声按钮存在（若有数据）
    Expected Result: 5 个步骤全部通过，无 console error
    Evidence: .sisyphus/evidence/task-16-workflow.png
  ```

  **Commit**: NO（仅在 Task 17 时一起提交）

- [ ] 17. **提交推送 + 线上验证**

  **What to do**:
  - `git add && git commit && git push` 到 main
  - 等待 GitHub Pages build 完成
  - Playwright 开启线上 URL 验证首页加载、分类多选下拉、全国/省级生成、详情页、删除对话框、分享链接

  **QA Scenarios**:
  ```
  Scenario: 线上全流程验证
    Tool: Playwright
    Steps:
      1. 打开 https://monomelemon.github.io/bird-preview-book/
      2. #new-book 分类多选下拉可用，全选时标题简化
      3. 全国搜索返回鸟种，省级搜索返回正确
      4. 详情 Wikipedia 分布和介绍、Macaulay 鸣声
      5. 删除确认自定义弹窗、分享链接可打开
    Expected Result: 线上功能完整，无 console error
    Evidence: .sisyphus/evidence/task-17-live-check.png
  ```

  **Commit**: YES — `release: v2 real data and UI improvements`

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read plan end-to-end. Verify each "Must Have" and "Must NOT Have". Check evidence.

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `node --check app.js`, check all JSON valid, verify data consistency script passes.

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright`)
  Execute ALL QA scenarios from EVERY task. Test cross-task integration.

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verify every task's "What to do" was done, nothing beyond scope.

---

## Commit Strategy

- **Wave 1**: `feat(data): expand to China-wide species with Macaulay media and Wikipedia descriptions`
- **Wave 2**: `feat(ui): multi-select category, save-preview flow, delete dialog, location history`
- **Wave 3**: `chore: verify data consistency and deploy`

---

## Success Criteria

### Verification Commands
```bash
python3 -c "import json; s=json.load(open('data/species.json')); print(len(s),'species')"  # Expected: 1100-1500
python3 -c "import json; m=json.load(open('data/media.json')); print(sum(1 for v in m.values() if v.get('images')),'with images')"  # Expected: 95%+
node --check app.js  # Expected: no errors
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] No fake probability/occurrence data
- [ ] 分类多选下拉可用
- [ ] 保存-预览逻辑正确
- [ ] 删除确认自定义弹窗
- [ ] 地点历史可用
- [ ] 全国搜索返回全网记录
- [ ] 详情页无相似种区域
- [ ] Macaulay 鸣声可播放
- [ ] Wikipedia 信息来源可追溯
