# WOTB WWISE REVERSE PIPELINE V5.0 (VERIFIED BASELINE)
**Target:** Phục dựng project Wwise gốc (Wargaming) từ WoTB game build, chạy hoàn toàn trên Linux qua Wine.
**Core Rule (ANTI-HALLUCINATION):** Mọi cấu trúc parser/logic dưới đây đã được xác nhận bằng hex-dump và dữ liệu thật (xem `## Verified Facts`). Agent AI đọc file này CẤM suy diễn thêm ngoài phạm vi đã verify — nếu cần dữ liệu mới, phải tự chạy lệnh xác minh tương tự trước khi code, không được giả định theo tài liệu SDK Wwise chuẩn.

---

## ⚠️ Giới hạn phục dựng — CẦN HIỂU RÕ trước khi tiếp tục Phase 4

Nguồn dữ liệu là file ĐÃ COMPILE (`.bnk`/`.pck`), không phải project gốc (`.wproj`). Quá trình compile của Wargaming đã LOẠI BỎ VĨNH VIỄN một số thông tin — không có cách nào lấy lại từ dữ liệu hiện có:

| Thành phần | Khả năng phục dựng |
|---|---|
| Audio asset | ✅ Đầy đủ (Phase 1 xong) |
| Event (tên, ID, cấu trúc gọi) | ⚠️ Dữ liệu thô có sẵn (JSON + HIRC), CHƯA viết script import (Phase 4.4, chưa làm) |
| GameSync (State/Switch/RTPC) | ⚠️ Dữ liệu thô có trong `.txtp` header (`STATECHUNKS`, `GAMEVARS`) và HIRC XML, CHƯA viết script trích xuất+import |
| SoundBank (cấu trúc) | ⚠️ Biết file→bank mapping, CHƯA viết script tạo lại SoundBank object |
| **ShareSets** (Effect, Attenuation, Aux Bus) | ⚠️ Dữ liệu thô có trong HIRC (`reflectionsAuxBus`, `OverrideBusId`, `NodeInitialFxParams`) — **CHƯA từng được đưa vào kế hoạch Phase 4 cụ thể, cần bổ sung bước riêng trước khi viết wwise_builder.py** |
| **Soundcaster Sessions** | ❌ **KHÔNG THỂ phục dựng** — chỉ tồn tại trong `.wproj` gốc, bị loại bỏ khi compile ra `.bnk`/`.pck` |
| **Queries đã lưu** | ❌ **KHÔNG THỂ phục dựng** — cùng lý do, chỉ tồn tại trong project gốc |

**Kết luận cho mục tiêu dự án:** "Phục dựng 100% Wwise Project" (ghi ở đầu file) cần hiểu là **100% phần có thể phục dựng từ compiled bank** (audio + hierarchy + gamesync logic + effects), KHÔNG bao gồm artifact chỉ tồn tại ở tầng authoring (Sessions, Queries, comment nhà phát triển, lịch sử version). Đây là giới hạn vật lý của nguồn dữ liệu, không phải giới hạn của pipeline.

---

```
Phase 1 — Carved: 7861 | Unique: 5640 | Collision: 1963 ID (verify khớp tuyệt đối)
Phase 2 — Manifest: 5798 | Orphans: 0
Phase 3 — .txtp: 934 | Dry-run: 934/934 OK | Render .wav: 934/934 thành công
          (verify 3 lớp: đếm file độc lập = 934, code ThreadPoolExecutor dùng
          executor.map() không nuốt exception, nghe thật bằng tai xác nhận
          âm thanh đúng — không chỉ tin log tự báo cáo)
```

**Bài học quan trọng về debug số liệu:** trong quá trình xác minh, có 1 lần báo cáo SAI (nói 1967 dòng, phân bố "1961×1 + 2×3") do so sánh nhầm dữ liệu giữa 2 lần chạy `run_full_carve.py` khác nhau (1 lần trước khi xóa lại `pool/`, 1 lần sau). Chỉ phát hiện được nhờ ép chạy lại toàn bộ 3 lệnh awk NGAY LIỀN NHAU không xen lệnh nào khác ở giữa, và đối chiếu tổng tính được với `wc -l` phải khớp tuyệt đối trước khi tin. **Nguyên tắc rút ra: khi verify số liệu nhiều bước, luôn chạy các lệnh đo liền mạch trong 1 lần, không tách rời qua nhiều lượt hỏi-đáp — dễ lẫn dữ liệu giữa các lần chạy khác nhau của hệ thống.**

---

## Verified Facts (Phase 0 — ĐÃ XÁC NHẬN BẰNG DỮ LIỆU THẬT)

### 1. Cấu trúc file `.pck`
- Magic bytes tại offset 0: `41 4B 50 4B` ("AKPK") — xác nhận qua hex-dump `weapon_basic.pck`.
- Cấu trúc: `AKPK` header → Language Map Section → **Data Index Section** → Data Section (blob `.wem` nối liền nhau).
- **Data Index Entry — 20 byte/entry, THỨ TỰ ĐÃ XÁC NHẬN BẰNG THỰC NGHIỆM (khác giả định ban đầu):**
  ```
  uint32 ID         (offset +0)
  uint32 flag=1     (offset +4)   — cờ cố định, luôn = 1
  uint32 SIZE       (offset +8)   — LƯU Ý: size đứng TRƯỚC offset
  uint32 OFFSET     (offset +12)  — offset đứng SAU size
  uint32 reserved=0 (offset +16)
  ```
  Xác minh: entry đầu tiên trong `weapon_basic.pck` có ID=32218762, size=28710, offset=1620.
  `f.seek(1620); f.read(4)` trả về đúng `b'RIFF'` — xác nhận offset đúng vị trí này, không phải giá trị 28710.
  Verify Phase 1 hoàn tất: carve toàn bộ 78/78 entry, 100% magic bytes = `RIFF`.
- Kết luận: dùng `mmap` + đọc offset/size theo ĐÚNG thứ tự trên (size trước, offset sau) để slice `.wem`, KHÔNG scan byte tìm `RIFF`/`RIFX`, và KHÔNG giả định offset đứng trước size (giả định ban đầu đã SAI, chỉ phát hiện qua test thực nghiệm).

### 1b. BUG NGHIÊM TRỌNG đã tìm và sửa: `parse_akpk` hardcode byte pattern, bỏ sót 35/36 file `.pck` ÂM THẦM
- **Bug:** code ban đầu định vị Data Index Section bằng `data.find(b'\x8a\x9e\xeb\x01')` — đây là giá trị ID `32218762`, RIÊNG của `weapon_basic.pck`. Với 35/36 file `.pck` khác, `find()` trả về `-1`, hàm return `[]` — KHÔNG lỗi, KHÔNG log, khiến `run_full_carve.py` âm thầm `continue` bỏ qua toàn bộ file đó trong nhiều giờ mà không ai biết.
- **Cách phát hiện:** không chấp nhận số liệu "carved=5915" khi chưa verify riêng từng file `.pck` — viết script quét entry-count cho cả 36 file, phát hiện 35 file trả về 0.
- **Đã sửa:** Data Index Section trong AKPK **bắt đầu tại offset cố định 52 (0x34)** — xác nhận đúng trên 4 file khác nhau (`weapon_basic`, `ambient`, `engine`, `music_battle`) bằng `seek()` thật, cả 4 đều cho `RIFF` đúng vị trí. (Lưu ý: đã thử tính động qua Language Map Size ở offset 0x14 trước đó — SAI, gây đọc lệch vị trí; offset 52 là hằng số đúng, không phải tính động).
- **Số liệu SAU KHI SỬA — ĐÃ CHỐT FINAL:** Carved 7861 (từ 5915), Unique 5640 (từ 5633), Manifest 5798, Orphans 0. Collision: 1963 unique ID bị ghi đè (mỗi ID ≥3 nguồn khác nhau), tổng 3930 dòng log — đã verify khớp tuyệt đối bằng phép tính chéo (xem mục "PHASE 1 ĐÃ CHỐT FINAL" đầu file).
- **Bài học quan trọng nhất trong toàn bộ dự án**: lỗi im lặng (return `[]` thay vì raise exception) là loại bug nguy hiểm nhất — không bao giờ tin 1 con số "đẹp" (như carved=5915 không có lỗi nào) mà không tự hỏi "liệu có phần nào đang bị bỏ qua mà không báo lỗi?". Luôn verify riêng lẻ từng file input khi số lượng > 1, không chỉ verify tổng.

### 2. Cấu trúc file `.bnk`
- Chunk-based, xác nhận qua hex-dump `en/voiceover_crew.bnk` và `DP_WoTB_Mod_chuck_norris/voiceover_crew.bnk`:
  - `BKHD` (Bank Header) tại offset 0
  - `DIDX` (Data Index) ngay sau BKHD
  - `DATA` (blob byte nối liền)
  - `HIRC` (Hierarchy — chứa object tree: Sound, Event, MusicSegment, v.v.)
- **DIDX Entry — THỨ TỰ FIELD KHÁC AKPK, đã xác nhận qua thực nghiệm:**
  ```
  uint32 ID
  uint32 OFFSET   ← offset đứng TRƯỚC size (ngược với AKPK!)
  uint32 SIZE     ← size đứng SAU offset
  ```
  Xác minh: entry đầu tiên `voiceover_crew.bnk` có id=6268216, offset=1968, size=15893.
  `seek(1968)` đọc đúng `b'RIFF'`. Verify: carve toàn bộ 160/160 entry thành công.
  **CẢNH BÁO CHO AGENT: AKPK (`.pck`) và DIDX (`.bnk`) có thứ tự field NGƯỢC NHAU
  (AKPK: size trước offset; DIDX: offset trước size) — dùng 2 hàm parse riêng biệt,
  KHÔNG dùng chung 1 struct format cho cả hai.**
- Cấu trúc BKHD/DIDX giống hệt nhau giữa bank ngôn ngữ gốc và bank mod → không có custom obfuscation.

### 3. Version Wwise Engine
- `BKHD` chunk field `dwBankGeneratorVersion` = **135** (xác nhận qua `weapon_basic.bnk` và `en/voiceover_crew.bnk`, nhất quán trên toàn bộ file đã kiểm tra).
- Khớp với Authoring Tool đã cài: **Wwise 2019.2.15, build 7667**.
- Dùng đúng version Authoring này để chạy WAAPI/WwiseConsole (Phase 4) — Authoring KHÔNG cần khớp version SDK đã build ra file input, vì Phase 4 chỉ tạo project mới qua WAAPI, không mở lại file `.bnk` cũ.
- **Input files (`.pck`/`.bnk`) có thể đến từ nhiều bản build WoTB khác nhau theo thời gian** (game cập nhật liên tục). Cấu trúc chunk `BKHD/DIDX/DATA/HIRC` ổn định xuyên suốt dòng 2019.2.x, nên carver KHÔNG được hardcode check `version == 135` để từ chối file. Thay vào đó: đọc version ra, log nếu nằm ngoài `KNOWN_GOOD_VERSIONS = {135}` nhưng VẪN tiếp tục parse theo layout chuẩn — cảnh báo không phải chặn. Agent tự thêm version mới vào whitelist sau khi verify thật (hex-dump + carve thử + so kết quả) trên file thuộc bản build đó.

### 4. Hai nguồn `SoundbanksInfo.json` — QUAN TRỌNG, PHẢI PHÂN BIỆT RÕ
- **`WwiseSound/SoundbanksInfo.json`** (bản GỐC, sạch): chỉ có **22 Language entry chính hãng**:
  `English(US), arb, gup, pbr, vi, uk, tr, th, sv, ru, pl, ko, ja, it, fr, fi, en, es, de, cs, cn, en_gb`
  → Đây là **NGUỒN CHÂN LÝ DUY NHẤT** cho việc phục dựng project gốc Wargaming.
- **`out_wwise/dvpl_unpacked/SoundbanksInfo.json`** (bản đã bị mod Dương Phạm merge): có thêm ~70 entry `DP_WoTB_Mod_*` được đăng ký NGANG HÀNG với Language thật (dùng đúng field `Language` để cắm mod vào — đây là kỹ thuật hợp lệ trong Wwise, không phải hack/obfuscation).
  → CHỈ dùng nguồn này nếu chủ động muốn dựng thêm nhánh "Community Mod Edition", KHÔNG BAO GIỜ trộn vào project gốc.

### 5. `gup` = Girls und Panzer — Language chính hãng, KHÔNG phải mod
- Xác nhận trong file JSON gốc `WwiseSound/SoundbanksInfo.json`: `gup` đứng ngang hàng `en`, `ru`, `vi` như 1 Language thật của Wargaming (collab chính thức).
- `DP_WoTB_Mod_gup/voiceover_crew.bnk` và `gup/voiceover_crew.bnk`: MD5 **trùng 100%** (`4aa3ee3a5ad699c2e318d388e2d4719b`), `cmp -l` trả về 0 khác biệt → bản mod chỉ copy nguyên bản gốc, không chỉnh sửa gì.

### 6. Naming convention — không có xung đột trùng tên
- Wwise/Wargaming đã tự gắn hash suffix vào tên file: `co tam (1)_3F75BDB9.wem` — hash này (`3F75BDB9`) gắn theo context/bank cụ thể.
- KHÔNG cần tự nghĩ thêm cơ chế chống trùng tên khi carve — giữ nguyên convention gốc.
- Chiến lược naming: filesystem dùng **Source ID số làm tên file** (`pool/<id>.wem`), friendly name tách riêng vào `manifest.json` — không nhồi cả hai vào 1 filename.
- **CẬP NHẬT (đã verify bằng A/B test thật, sau đó tối ưu lại):** ban đầu phát hiện cần symlink `.bnk` để `vgmstream-cli` phân giải subsong nhúng qua cú pháp `<bank>.bnk#<index>` — bằng chứng: gỡ symlink `.bnk` khỏi `pool/` → dry-run OK giảm từ 926 xuống 669 (mất 257 file). Sau đó tối ưu kiến trúc: **KHÔNG trộn `.bnk` vào `pool/` gốc** (giữ `pool/` sạch, thuần `.wem`, đúng thiết kế ban đầu). Thay vào đó tạo `out_wwise/render_pool/` — thư mục ảo riêng chỉ dùng cho mục đích render, chứa symlink của cả `.wem` (từ `pool/`) và `.bnk` (từ input gốc). `generate_txtp.py` trỏ `-gw` vào `render_pool/`, không phải `pool/`. Verify lại sau khi tách: vẫn giữ đúng OK=926/934, không lệch.
- `scripts/linker.py` khi scan `pool_dir` để tính `carved_ids` lọc đúng đuôi `.wem` (`if f.endswith('.wem')`) — xác nhận carved_ids=5633 không bị ảnh hưởng bởi việc có/không có `.bnk` lẫn trong thư mục.

### 7. Music Hierarchy — chỉ tập trung ở 2/52 bank
Quét toàn bộ 52 file `.bnk` trong `WwiseSound/` gốc, tìm `CAkMusicSegment|CAkMusicTrack|CAkMusicSwitchCntr|CAkMusicRanSeqCntr`:
- **`music_hangar.bnk`**: 51 match — Music Hierarchy phức tạp nhất (nhạc nền Hangar cần loop/crossfade mượt).
- **`apk.bnk`**: 17 match — mức trung bình, cần review thêm để hiểu vai trò.
- **TẤT CẢ các bank còn lại** (`music_battle.bnk`, `music_maps_*.bnk` theo từng map, `music_result_screen.bnk`, `Init.bnk`, `DP_music_battle.bnk`...): chỉ chứa `CAkSound` đơn giản, KHÔNG có Segment/Track/Transition.
- Ý nghĩa: Phase Music Reconstruction nhẹ hơn dự kiến ban đầu — ~50 bank chỉ cần dựng Sound + Random/Sequence Container qua WAAPI; chỉ 2 bank cần xử lý kỹ Segment/Transition riêng.
- Lưu ý phụ: object path nội bộ của 1 bank có thể không khớp tên file vật lý (vd: `DP_music_battle.bnk` có `objpath="\\SoundBanks\\Default Work Unit\\Nordskar"` — "Nordskar" là tên bản đồ, không phải tên file).

### 8. Wine Compatibility — XÁC NHẬN KHẢ DỤNG
Setup: `WINEPREFIX=$HOME/.wwise_wine`, Wwise 2019.2.15.7667 cài qua Audiokinetic Launcher.
- **Test 1 (Activation/UI)**: PASS — `Wwise.exe` mở được, không crash (log chỉ có `fixme` vô hại), tương tác UI được (save dialog xuất hiện đúng).
- **Test 2 (CLI headless)**: PASS — `WwiseConsole.exe` chạy độc lập không cần GUI, in đúng danh sách operations: `create-new-project`, `generate-soundbank`, `waapi-server`, `tab-delimited-import`, v.v.
- **Test 3 (create-new-project syntax)**: PASS — `--help` trả về đúng cú pháp:
  ```
  WwiseConsole create-new-project "C:\MyProject\MyProject.wproj" --platform "Windows" "Linux"
  ```
- **Test 4 (WAAPI socket + encoder build thật)**: PASS, full Wine pipeline khả dụng. Đã chạy WAAPI socket connectivity kết nối thành công, đồng thời tab-delimited-import và generate-soundbank giải mã/build Vorbis thật thành công ra file .bnk > 0 bytes không gặp lỗi "codec not found" hay "vorbis encoder failed".
- Quyết định: tiếp tục dùng Wine cho toàn bộ pipeline, KHÔNG cần dual-boot/máy Windows riêng, trừ khi Test 4 phát hiện vấn đề (đặc biệt là soundbank encoder — nếu fail, có thể dùng phương án hybrid: mọi thứ qua Wine trừ bước build cuối).

### 9. Cấu trúc `SoundbanksInfo.json` — CẢNH BÁO LỒNG SÂU, dễ bỏ sót
- ID file audio trong JSON nằm ở **3 vị trí khác nhau**, PHẢI đọc cả 3, thiếu 1 sẽ gây orphan giả:
  1. `SoundBanksInfo.StreamedFiles[]` — file streaming (.pck), cấp ngoài cùng
  2. `SoundBanksInfo.SoundBanks[].IncludedMemoryFiles[]` — file embedded cấp bank, KHÔNG qua Event
  3. `SoundBanksInfo.SoundBanks[].IncludedEvents[].IncludedMemoryFiles[]` — **LỒNG SÂU HƠN, dễ bỏ sót nhất**, chứa phần lớn ID Voice/Language (xác nhận qua ID `1000066695`, language=`fi`, nằm trong Event `ingame_voice_notifications_VO_gun_damaged`)
- Bug thực tế đã xảy ra: linker.py ban đầu chỉ đọc vị trí 1+2, bỏ sót vị trí 3 → 3617/5633 ID (64%) bị báo orphan giả dù có mapping thật trong JSON. Sau khi thêm vòng lặp đọc `IncludedEvents[].IncludedMemoryFiles[]`: orphan giảm về 0, manifest tăng từ 2023 lên 5798 entry.
- **Bài học cho agent**: khi parse JSON có cấu trúc Event/SoundBank lồng nhau, PHẢI test bằng cách lấy 1 ID orphan bất kỳ, `grep` thô trực tiếp trong file JSON (không qua code) để xác nhận ID có tồn tại thật hay không, trước khi kết luận "orphan thật". Orphan cao bất thường (>10%) là dấu hiệu bug parser, không phải dữ liệu thiếu.

### 9b. Bug đã biết trong `linker.py` (`parse_txtp_files`) — CÓ THẬT nhưng VÔ HẠI trên dữ liệu hiện tại
- `re.findall(r'(\d+)\.wem', content)` quét TOÀN BỘ nội dung file `.txtp`, kể cả dòng comment HIRC (bắt đầu bằng `#`). Vì hash suffix Wwise là hex (vd `97F42061`), nếu đuôi hash tình cờ toàn chữ số (`...42061`), regex bắt nhầm đoạn đó làm Source ID giả (vd trích ra `42061` từ `login_drone_drums_loop_01_97F42061.wem`).
- Verify: `python3 -c "import json; m=json.load(open('manifest.json')); print(m.get('42061'))"` → `None`. Xác nhận ID giả này KHÔNG trùng bất kỳ ID thật nào trong manifest hiện tại → KHÔNG gây sai lệch friendly_name/object_path trên dữ liệu đã có.
- **Rủi ro còn lại (lý thuyết, chưa xảy ra)**: nếu 1 ID giả trích từ hash trùng ngẫu nhiên với 1 ID thật, friendly_name của ID đó có thể bị enrichment ghi đè sai (chỉ ảnh hưởng cosmetic, KHÔNG ảnh hưởng orphan calculation vì bước đó tính trước enrichment).
- **Fix đề xuất (chưa áp dụng, không cấp thiết)**: lọc bỏ dòng bắt đầu bằng `#` trước khi regex trong `parse_txtp_files()`.

### 10. Trùng lặp ID giữa các bank — BÌNH THƯỜNG, không phải lỗi
- 92/5633 ID unique bị carve nhiều lần từ các bank khác nhau (vd: cùng 1 ID xuất hiện trong cả `engine.bnk` và `engine_basic.bnk`, size byte-for-byte giống hệt nhau).
- Đây là shared asset hợp lệ (game dùng chung 1 file âm thanh cho nhiều bank/context) — ghi đè cùng nội dung vào `pool/<id>.wem` là AN TOÀN, không cần xử lý đặc biệt.
- Chỉ cần lo ngại nếu 2 bank có CÙNG ID nhưng KHÁC size — dấu hiệu ID collision thật (chưa gặp trường hợp này).

### 11. Dry-run validation Phase 3 — ĐÃ CẬP NHẬT: 934/934 sau khi sửa bug parse_akpk, kết luận cũ SAI
- **Kết luận CŨ (SAI, đã bị bác bỏ):** ban đầu 926/934 OK, 8 MISSING_SOURCE kết luận là `StreamType 0x02 [Streaming]` = thiết kế cố ý, external source không có trong archive.
- **Sự thật sau khi sửa bug `parse_akpk` (Fact #1b):** sau khi carve đủ 36/36 file `.pck` (trước đó chỉ carve đúng 1 file do bug hardcode byte pattern), toàn bộ 8 file MISSING_SOURCE tự nhiên trở thành OK — **934/934, 0 MISSING_SOURCE**.
- **Verify cụ thể cho 1 case** (`play_hng_pl_wind_ghust.txtp`, Source ID `995087964`, path gốc `Hangar\\Hangar_Platoon\\amb_ghust_02_stereo...wem`): xác nhận `pool/995087964.wem` giờ tồn tại thật (203KB, magic `RIFF` đúng qua `xxd`), đến từ 1 trong 35 file `.pck` từng bị bỏ sót (khả năng cao `hangar_platoon.pck`/`hangar_normal.pck` theo path).
- **BÀI HỌC QUAN TRỌNG NHẤT:** kết luận "StreamType 0x02 = thiết kế cố ý" tưởng như đã verify bằng bằng chứng thật (đọc HIRC, grep, scan byte) ở thời điểm đó — nhưng **bằng chứng đúng không có nghĩa là kết luận đúng**, vì bằng chứng bị giới hạn bởi 1 bug khác (carving thiếu 35 file) chưa được phát hiện lúc đó. Đây là lời nhắc: khi sửa 1 bug gốc (upstream), PHẢI quay lại rà soát mọi kết luận trước đó dựa trên dữ liệu bị ảnh hưởng bởi bug đó — không chỉ cập nhật con số, mà phải xét lại cả DIỄN GIẢI đã đưa ra dựa trên con số cũ.

### 12. Modpack cộng đồng (test: DP_Modpack_11) — tỷ lệ orphan cao hơn NHIỀU so với data gốc, đây là ĐẶC TÍNH của modpack, không phải bug pipeline
- Chạy thử pipeline (đã parameterize --input/--output) trên modpack Dương Phạm: 99 archive, 48599 file carve (36593 unique), 40883 manifest entry, **1357 orphan**.
- So với data gốc Wargaming (5633 carved, 0 orphan) — tỷ lệ orphan modpack (~3.7%) cao hơn hẳn.
- Điều tra 10 orphan mẫu, xác nhận bằng đọc HIRC nhị phân trực tiếp (không chỉ text-match filename):
  - 1 case tưởng "orphan giả" (trùng số trong tên file với 1 Id khác `610144283`) nhưng sau khi đọc HIRC xác nhận là **trùng hợp ngẫu nhiên tên file, KHÔNG liên quan nhau** — object HIRC thật (`CAkSound` id=397957780) gọi Source `1000714242` hoàn toàn không được khai báo trong `SoundbanksInfo.json` của modpack.
  - 9/10 orphan còn lại: hoàn toàn vắng mặt trong JSON dưới mọi hình thức.
- **Kết luận: đây là lỗi bất đồng bộ metadata phổ biến của modpack cộng đồng** — tác giả mod thường đóng gói/gộp file `.bnk` nhưng không tái tạo đầy đủ `SoundbanksInfo.json` tương ứng. KHÔNG sửa linker.py để "đoán" ID từ tên file — làm vậy có nguy cơ link nhầm 2 asset khác nhau vô tình trùng tên (rủi ro cao hơn với modpack tổng hợp nhiều tác giả).
- **Bài học cho agent**: KHÔNG giả định pipeline áp dụng cho data gốc sẽ cho tỷ lệ orphan tương tự với modpack — mỗi nguồn input cần điều tra orphan riêng bằng bằng chứng nhị phân thật (đọc HIRC, không chỉ text-match), vì lý do orphan có thể khác nhau hoàn toàn giữa các nguồn.

```markdown
- [ ] Wine Test 4: WAAPI server (chạy trong Wine) accept connection từ waapi-client
      Python native trên Linux qua localhost:<port>
- [ ] Wine Test 4b: generate-soundbank thật với audio thật → xác nhận Vorbis
      encoder không thiếu DLL (cần winetricks vcrun2019 trước)
- [ ] Nội dung thật của apk.bnk (17 Music object) — vai trò trong game là gì
- [ ] Xác nhận danh sách 52 bank ở WwiseSound/ đã đầy đủ (có bank nào bị bỏ sót
      trong lần liệt kê ls không, đặc biệt các map chưa quét)
```

---

## Assumptions Log — PHÂN BIỆT RÕ ĐÃ VERIFY vs CHƯA

### Đã verify (an toàn để code theo)
Toàn bộ 8 mục trong `Verified Facts` ở trên.

### CHƯA verify — agent PHẢI tự confirm bằng dữ liệu trước khi dùng
- Cấu trúc AKPK/DIDX của các file `.pck`/`.bnk` KHÁC ngoài 3 file mẫu đã hex-dump (weapon_basic, voiceover_crew x2, music_battle, music_hangar) — giả định đồng nhất nhưng chưa kiểm tra toàn bộ 52+ file.
- HIRC object type đầy đủ trong `music_hangar.bnk` và `apk.bnk` (đã biết CÓ Music object, nhưng chưa đọc chi tiết cấu trúc Playlist/Transition Rule bên trong).
- WAAPI batch payload size giới hạn thực tế qua Wine (giả định 500 object/batch theo khuyến nghị chung, chưa test giới hạn thật).

---

## Constraints cho Agent

- **Đa dạng bản build input**: Mục tiêu tool là đọc được `.pck`/`.bnk` từ NHIỀU bản build WoTB khác nhau theo thời gian (game cập nhật liên tục), không chỉ bản đang có trong tay. Do đó: KHÔNG hardcode số lượng Language (vd "22 Language"), danh sách tên bank cụ thể (vd "52 bank"), hay danh sách event ID cố định ở bất kỳ đâu trong code. Luôn đọc động từ `SoundbanksInfo.json` và cấu trúc thư mục thật của bản build đang xử lý tại thời điểm chạy. Các con số trong `Verified Facts` (22 Language, 52 bank...) là SỰ THẬT CỦA 1 BẢN BUILD CỤ THỂ đã test, không phải hằng số của toàn bộ dòng game.
- Version check (`BKHD.dwBankGeneratorVersion`) chỉ log cảnh báo khi gặp version ngoài whitelist đã verify — KHÔNG raise lỗi/từ chối xử lý file (xem Verified Facts #3).
- KHÔNG cài thêm thư viện ngoài: `wwiser`, `vgmstream-cli`, stdlib Python (`mmap`, `struct`, `json`), `waapi-client` (chỉ cho Phase 3).
- KHÔNG viết `ProcessPoolExecutor`/`ThreadPoolExecutor` cho carving — dùng `mmap` trực tiếp offset-based (O(1), đã xác nhận cấu trúc AKPK/DIDX phù hợp).
- `ThreadPoolExecutor` CHỈ dùng cho việc gọi `subprocess.run(vgmstream-cli, ...)` hàng loạt (I/O + external process, GIL không cản trở).
- Mọi script phải chạy độc lập qua CLI argument, không hardcode path.
- Mọi lỗi phải log ra file, KHÔNG được `except: pass` nuốt lỗi im lặng.
- Toàn bộ carving/render cho project GỐC phải trỏ vào `WwiseSound/` (bản sạch), KHÔNG được đọc nhầm từ `out_wwise/dvpl_unpacked/` root (đã bị mod merge) trừ khi đang làm rõ nhánh Community Mod.
- **Quản lý Task trong Cline (hoặc agent tương tự)**: tạo Task MỚI khi chuyển sang Phase khác, khi 1 bug lớn đã đóng xong và verify đầy đủ, hoặc khi thấy phản hồi chậm bất thường (dấu hiệu context quá dài). KHÔNG tách quá vụn (mỗi câu hỏi nhỏ 1 task riêng) — giữ chung 1 task cho các lượt hỏi-đáp liên quan trực tiếp tới nhau, vì agent cần nhớ bối cảnh ngay trước đó để làm việc hiệu quả.

---

## Phase 1: Unified Carver Core

**Mục tiêu:** 1 module carving dùng chung cho cả AKPK (`.pck`) và DIDX (`.bnk` embedded).

1. Viết `index_parser.py`:
   - `parse_akpk(filepath) -> List[{id, offset, size}]`
   - `parse_didx(filepath) -> List[{id, offset, size}]` (offset tính từ đầu DATA chunk, cần cộng thêm offset của DATA chunk trong file)
2. Viết `carve_core.py`:
   - `carve_by_index(filepath, index_table) -> Dict[id, bytes]` dùng `mmap`, dùng CHUNG cho cả 2 nguồn trên.
3. Output: đổ toàn bộ `.wem` cắt ra vào **1 thư mục phẳng** `pool/<source_id>.wem` — KHÔNG giữ cấu trúc thư mục gốc, KHÔNG rename theo friendly name ở bước này.

**Verify trước khi qua Phase 2:**
- [ ] Carve thử 5 file từ `weapon_basic.pck`, so 4 byte đầu mỗi file cắt ra phải là `RIFF`/`RIFX`
- [ ] Carve thử `en/voiceover_crew.bnk`, so sánh số lượng file cắt ra khớp với `count` trong `DIDX` chunk
- [ ] Tổng size các file carve ra + offset cuối cùng KHÔNG vượt quá filesize thật

---

## Phase 2: Naming Manifest & Linker

**Mục tiêu:** Tách metadata (mutable) khỏi data (immutable).

1. `linker.py` đọc `WwiseSound/SoundbanksInfo.json` (BẢN GỐC, không phải bản mod-merge) + `.txtp` từ wwiser, sinh ra `manifest.json`:
   ```json
   {
     "<source_id>": {
       "friendly_name": "...",
       "object_path": "...",
       "language": "en | gup | null (nếu SFX)"
     }
   }
   ```
2. ID không tìm thấy trong JSON (orphan) → `"friendly_name": null`, KHÔNG crash, ghi vào `report_dryrun.log` để review sau.
3. KHÔNG rename file trong `pool/` — mọi mapping tên đẹp chỉ tồn tại trong `manifest.json`, dùng khi generate `import.txt` ở Phase 4.

---

## Phase 3: Linux Extraction Pipeline

1. `wwiser` export `.txtp` (routing) + HIRC XML (structure) từ `WwiseSound/` gốc.
2. Dry-run validate TRƯỚC khi render hàng loạt:
   ```bash
   vgmstream-cli -m -i file.txtp   # chỉ đọc metadata, cực nhanh
   ```
   Gom kết quả vào `report_dryrun.log`: `OK: N / MISSING_SOURCE: N (liệt kê rõ)`.
   **CHỈ render thật khi `MISSING_SOURCE = 0`.**
3. Render thật: `ThreadPoolExecutor` gọi `subprocess.run(vgmstream-cli...)`, output `.wav` đặt tên theo Source ID (không phải friendly name).
4. Phân loại theo `manifest.json`, KHÔNG đoán qua tên thư mục:
   ```python
   def classify(entry):
       lang = entry["language"]
       if lang is None: return "sfx_no_language"
       elif lang == "gup": return "official_voicepack_gup"
       elif lang in LANG_ISO_WHITELIST: return "official_language"
       else: return "unknown_review_needed"
   ```

---

## Phase 4: Windows/Wine Reconstruction (WAAPI Pipeline)

**Môi trường:** Wine (`WINEPREFIX=$HOME/.wwise_wine`), Wwise 2019.2.15.7667 — đã xác nhận CLI headless hoạt động (Verified Facts #8).

1. **Trước khi bắt đầu:** hoàn thành Wine Test 4 (còn treo ở trên) — nếu encoder build fail, quyết định hybrid fallback (build cuối trên máy Windows riêng).
2. `WwiseConsole.exe create-new-project` tạo `.wproj` rỗng.
3. Đăng ký **22 Language** đúng theo `WwiseSound/SoundbanksInfo.json` gốc (bao gồm `gup` như 1 Language thật, KHÔNG dựng thêm Switch Group riêng cho CrewVoicePack — đây chính là cơ chế Language built-in).
4. `wwise_builder.py` qua WAAPI dựng skeleton Actor-Mixer Hierarchy dựa trên `manifest.json` + HIRC XML.
5. **Music Hierarchy đặc biệt cho `music_hangar.bnk` và `apk.bnk`:** đọc kỹ HIRC XML của 2 file này, dựng Segment/Track/Transition qua WAAPI riêng, KHÔNG áp dụng logic đơn giản (Sound + Container) như 50 bank còn lại.
6. Bulk import qua `WwiseConsole.exe tab-delimited-import` dùng `import.txt` sinh từ `manifest.json`.
7. **Idempotent injection:** `inject_state.json` theo dõi ID nào đã inject. Script check state trước khi gọi WAAPI, skip nếu đã `done`.
8. Batch WAAPI: giới hạn 500 object/payload (giả định, cần verify giới hạn thật ở Test 4).
9. Checkpoint: `git commit` sau mỗi phase con.
10. Compile cuối: `WwiseConsole.exe generate-soundbank`.

---

## Ghi chú: Tái sử dụng Pipeline cho nguồn khác (không cần Phase riêng)

Toàn bộ Phase 1-4 được viết theo nguyên tắc KHÔNG hardcode số liệu cụ thể của 1 bản build (xem Constraints). Do đó, để phục dựng bất kỳ nguồn khác cùng định dạng Wwise (ví dụ: bản đã bị mod merge như `out_wwise/dvpl_unpacked/`), KHÔNG cần viết phase/script mới — chỉ cần chạy lại đúng pipeline Phase 1-4 với 2 tham số khác:

```bash
python3 run_pipeline.py --input <đường_dẫn_WwiseSound_khác> --output <thư_mục_output_riêng>
```

**Kỷ luật bắt buộc duy nhất:** mỗi nguồn input phải có `--output` RIÊNG (pool/, manifest.json, wproj/ khác nhau) — TUYỆT ĐỐI không ghi đè lẫn vào output của nguồn khác, để giữ được khả năng phân biệt provenance (nguồn gốc dữ liệu chính hãng Wargaming vs nội dung cộng đồng/mod). Đây chính là bài học từ 2 nguồn `SoundbanksInfo.json` ở Verified Facts #4 — không lặp lại lỗi trộn 2 nguồn.

Nếu dựng lại nội dung mod cộng đồng (như Dương Phạm), ghi rõ credit/nguồn gốc trong tài liệu đi kèm output đó — đây là công sức của tác giả mod, không phải asset gốc game.

---

## Checkpoint Strategy (áp dụng toàn bộ Phase 1-5)

- Sau mỗi phase: `git add -A && git commit -m "phase-N-complete"`.
- `manifest.json` và `inject_state.json` là 2 file trạng thái sống còn — backup riêng, không để lẫn vào `.gitignore`.
- Nếu lỗi giữa chừng ở Phase 4: KHÔNG xóa `.wproj`, chỉ cần script đọc lại `inject_state.json` và resume.

- Sau mỗi phase: `git add -A && git commit -m "phase-N-complete"`.
- `manifest.json` và `inject_state.json` là 2 file trạng thái sống còn — backup riêng, không để lẫn vào `.gitignore`.
- Nếu lỗi giữa chừng ở Phase 4: KHÔNG xóa `.wproj`, chỉ cần script đọc lại `inject_state.json` và resume.