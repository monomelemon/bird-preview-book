# Learnings - Task 3: clean_species_data.py

## Key Findings

### Family name mapping
- 816 species across 104 unique `family.zh` values, ALL in English before cleanup
- Built comprehensive FAMILY_MAP (104 entries) covering all taxonomic orders
- Families rebuilt in taxonomy.json after cleanup — all 104 now show Chinese names

### Traditional→Simplified Chinese
- 521 names converted from traditional to simplified
- 527 aliases added (original traditional names + V1 birdIds)
- Used character-pair mapping copied from app.js TRAD_TO_SIMP (lines 30-36)
- **Bug found**: codepoint-based transcription of app.js TRAD_TO_SIMP was unreliable
  - Example: 鵲→鹊 mapped as U+9D46 (鵆) instead of U+9D72 (鵲)
  - **Fix**: Rewrote TRAD_TO_SIMP using actual Chinese character strings, not codepoints
  - Added 4 missing mappings: 鳩→鸠, 鴿→鸽, 鸌→鹱, 鸛→鹳

### V1 alias handling
- comkin1: added "翠鸟", "alcedo_atthis" as aliases, chineseName→普通翠鸟
- livbul1: added "白头翁", "pycnonotus_sinensis" as aliases, chineseName→白头鹎
- rbbmag: added "urocissa_erythroryncha" as alias, chineseName→红嘴蓝鹊
- All original traditional names preserved as simplified aliases, then deduplicated

### Wikipedia data
- Modified fetch_wikipedia_v2.py to write `description` and `distribution` into species.json directly
- Added --limit=N flag for batch control
- Ran on 50 species: 2 got descriptions (唐秋沙, 寒林豆雁)
- Distribution extraction regex may need fixing (yielded 0 results)

# Learnings - Tasks 4-9: Wave 2 Fixes

## Task 4: Restore V1 Generate Flow

### Changes made to app.js
- Replaced `savePreviewToStorage()` with `saveGeneratedList(p)` that takes params directly instead of reading from `window._unsavedPreview`
- Added `saved: true` to list objects created by both `saveGeneratedList()` and `createImportList()`
- Removed preview section HTML entirely — no intermediate preview step
- Generate button (now labeled "生成预习本") auto-saves and navigates directly to book page
- `handleNewBookBack()` simplified to just `navigate("home")` since no unsaved state exists on new-book page
- Added `handleBookBack(listId)` — checks `list.saved` flag, warns user if not saved
- Added `saveBookList(listId)` — sets `saved: true` via `StorageService.updateList()` then re-renders
- Share button and save button grouped in a flex div on book detail page header

### Key design decision
Generated lists have `saved: true` by default. The "保存预习本" button only appears for lists where `saved !== true` (legacy lists or edge cases). Back button guard only triggers for unsaved lists.

## Task 5: Save Button try-catch

### Only `saveList()` needed wrapping
- `getLists()`, `getChecks()`, `getNotes()` already use `safeParse()` with try-catch
- Added try-catch around `saveList()`'s `localStorage.setItem()` call
- On error: shows modal "存储空间不足，请清理一些旧清单后重试。"

## Task 6: Audio Player Simplification

### renderSounds() changes
- Removed `<strong>` element that showed caption text (`s.caption || s.type || "鸣声"`)
- Added `controlsList="nodownload noplaybackrate"` to `<audio>` tag
- Kept source attribution line with recordist/license info
- Added CSS: `audio { width: 100%; max-width: 100%; height: 36px; }` for compact mobile display

## Task 7: Media Filtering

### filter_media.py
- Sorts images: Macaulay/eBird first, Wikimedia second
- Flags non-photo types from non-Macaulay sources with `note: "待确认是否为实物照片"`
- Caps at 3 images per bird
- Result: 0 birds trimmed (all already ≤3), 21 images flagged for review

## Task 8: Locations Rebuild

### rebuild_locations.py
- Reads 6208 occurrences → 32 unique location codes
- Chinese admin division format: Province=XX0000, City=XXYY00 (YY≠0), District=XXYYZZ (ZZ≠0)
- **Bug fixed**: City detection regex needed `c[4:6] == "00"` to distinguish cities from districts
- Tangshan (130200) + 5 districts always forced in even if not in occurrences
- Output: 31 provinces, only 河北省 has city-level data (唐山市 with 5 districts)
- All other provinces have province-level records only (no city/district breakdown)

## Task 9: Misc Fixes

### Taxonomy rebuild
- Orders: 27 unique orders from species.json (faithful to source data)
- Families: 103 unique Chinese family names, each mapped to its order
- Edge case: species.json uses "Pterocliformes" (not "沙鸡目") for sandgrouse order — preserved as-is since species.json is read-only per task constraints

### Dead code check
- No `parseCategory()`, `getSelectedLocation()`, `familyOptions`, or `habitatOptions` found in current codebase
- These were already cleaned in previous waves

### formatTaxonomy() verification
- All 816 species have Chinese `family.zh` names → `formatTaxonomy()` displays correctly
