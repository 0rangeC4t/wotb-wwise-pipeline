# FILE 01 — NỀN TẢNG ỔN ĐỊNH (Phase 0-3) — Fact #1-#13

## SCOPE
Chứa: kiến thức đã verify về format `.pck`/`.bnk`, `SoundbanksInfo.json`, naming, Wine, constraints toàn pipeline.
KHÔNG chứa: việc đang làm (→ 02/03/04), quy tắc vận hành chung (→ 00).
Trạng thái toàn file: [DONE], hiếm đổi. Đọc `00` trước.

**Lưu ý:** pipeline là script rời (`run_full_carve.py`, `linker.py`, `generate_txtp.py`, `wwise_builder.py`, `build_music_hangar.py`) trong `scripts/`. KHÔNG có `run_pipeline.py` gộp.

## Fact #1 [DONE] — Cấu trúc `.pck` (AKPK)
Data Index Section bắt đầu ở offset CỐ ĐỊNH 52 (0x34) — KHÔNG tính động qua Language Map Size (đã thử, sai). Entry 20 byte:
```
uint32 ID          (+0)
uint32 flag=1       (+4)
uint32 SIZE         (+8)   ← SIZE trước OFFSET
uint32 OFFSET       (+12)
uint32 reserved=0   (+16)
```
Bằng chứng: verify trên 4 file bằng seek() thật.
Bug lịch sử: định vị Data Index bằng tìm byte pattern ID riêng của 1 file → 35/36 file khác `find()=-1` → hàm `return []` không log → carver bỏ sót file đó âm thầm. Sau sửa: Carved 7861 (từ 5915), Unique 5640, Manifest 5798, Orphans 0.

## Fact #2 [DONE] — Cấu trúc `.bnk` (DIDX)
Field order NGƯỢC Fact #1 — dùng 2 hàm parse riêng, không chung struct:
```
uint32 ID
uint32 OFFSET   ← OFFSET trước SIZE (ngược AKPK)
uint32 SIZE
```
BKHD/DIDX giống hệt giữa bank ngôn ngữ gốc và bank mod — không có obfuscation riêng.

## Fact #3 [DONE] — Version Engine
`BKHD.dwBankGeneratorVersion=135` → Wwise Authoring 2019.2.15 build 7667. Authoring KHÔNG cần khớp version SDK input. Carver không chặn version khác 135 — log cảnh báo nếu ngoài `KNOWN_GOOD_VERSIONS={135}`, vẫn parse theo layout chuẩn.

## Fact #4 [DONE] — 2 nguồn `SoundbanksInfo.json`
| Nguồn | Nội dung | Dùng khi |
|---|---|---|
| `WwiseSound/SoundbanksInfo.json` | 22 Language chính hãng | NGUỒN CHÂN LÝ DUY NHẤT cho project gốc |
| `out_wwise/dvpl_unpacked/SoundbanksInfo.json` | Gốc + ~70 entry `DP_WoTB_Mod_*` | CHỈ dùng nếu dựng "Community Mod Edition" |
KHÔNG BAO GIỜ trộn 2 nguồn vào project gốc.

ID audio nằm ở 3 vị trí (vị trí 3 dễ bỏ sót): `StreamedFiles[]`; `SoundBanks[].IncludedMemoryFiles[]`; `SoundBanks[].IncludedEvents[].IncludedMemoryFiles[]` (lồng sâu nhất, chứa phần lớn ID Voice/Language).
Bug lịch sử: bỏ sót vị trí 3 → 3617/5633 ID (64%) orphan giả. Sau fix: orphan=0, manifest 2023→5798.
Quy tắc: orphan >10% là dấu hiệu bug parser, không phải dữ liệu thiếu — verify bằng grep thô trực tiếp trong JSON trước khi kết luận orphan thật.

## Fact #5 [DONE] — `gup` là Language chính hãng
`gup` (Girls und Panzer) đứng ngang `en`/`ru`/`vi` trong JSON gốc — KHÔNG phải mod, collab chính thức Wargaming. `DP_WoTB_Mod_gup` MD5 trùng 100% `gup` gốc.

## Fact #6 [DONE, SỬA 02/10] — Naming & kiến trúc thư mục
`pool/<id>.wem` dùng Source ID số làm tên; tên đẹp chỉ trong `manifest.json`. `pool/` giữ SẠCH chỉ `.wem`. `out_wwise/render_pool/` là thư mục ảo cho render, symlink cả `.wem` (từ `pool/`) và `.bnk` (từ input gốc) — cần cho `vgmstream-cli` phân giải subsong nhúng. `generate_txtp.py` trỏ `-gw` vào `render_pool/`, KHÔNG phải `pool/`. NHƯNG `pool/<id>.wem` phẳng theo ID KHÔNG đủ khi cùng Source ID có audio khác nhau theo ngôn ngữ (xem Fact #31). Với voice theo ngôn ngữ, decode thẳng từ bank, không đi qua `pool/`.

## Fact #7 [DONE] — Phạm vi Music Hierarchy
Chỉ 2/52 bank có Segment/Track/Transition: `music_hangar.bnk` (51 match), `apk.bnk` (17 match). Bank còn lại chỉ `CAkSound` đơn giản.

## Fact #8 [DONE] — Wine khả dụng toàn pipeline
Verify PASS: Activation/UI, CLI headless, `create-new-project`, WAAPI socket, encoder build thật (`.bnk` output >0 byte). Quyết định: dùng Wine cho toàn bộ, không cần máy Windows riêng.

## Fact #9 [DONE, SỬA 02/10] — Trùng ID giữa bank
92/5633 ID unique carve từ nhiều bank, size byte-for-byte giống hệt → shared asset hợp lệ. Chỉ đáng lo nếu cùng ID khác size (chưa gặp).
RXD: KHÔNG áp dụng, xem Fact #31 (557 ID cùng ID khác size).

## Fact #10 [DONE] — Dry-run 934/934 (sửa lại kết luận cũ SAI)
Sau fix #1: 934/934, 0 MISSING_SOURCE. Kết luận cũ "StreamType 0x02 = thiết kế cố ý" SAI — chỉ do bug #1 thiếu 35 file lúc đó chưa phát hiện.

## Fact #11 [DONE] — Orphan cao ở modpack là ĐẶC TÍNH
Test `DP_Modpack_11`: 99 archive, 48599 carve, 40883 manifest, 1357 orphan (~3.7%). Điều tra 10 mẫu bằng đọc HIRC nhị phân trực tiếp: phần lớn vắng mặt hoàn toàn trong JSON — lỗi bất đồng bộ metadata phổ biến của modpack, KHÔNG phải bug linker. Quy tắc: KHÔNG sửa `linker.py` để đoán ID từ tên file.

## Fact #12 [DONE] — Bug copy `.bnk` sai path crewvoice
`render_pool/<lang>/voiceover_crew.bnk` có subdir lang nhưng `wwiser` ghi path không có subdir vào `.txtp` → 864/1964 txtp MISSING_SOURCE. Fix: copy/symlink thêm 1 bản flat khớp path `wwiser` ghi. Sau fix: 1856/1856 OK.

## Fact #13 [DONE, rủi ro còn theo dõi] — Regex `parse_txtp_files` bắt nhầm comment
`re.findall(r'(\d+)\.wem', content)` quét cả dòng comment HIRC. Verify hiện tại: 0 va chạm thật. Rủi ro lý thuyết còn lại: ghi đè sai `friendly_name` nếu ID giả trùng ID thật trong tương lai. Fix đề xuất chưa áp dụng (không cấp thiết): lọc dòng `#` trước khi regex.

## ASSUMPTION_UNVERIFIED
- Cấu trúc AKPK/DIDX ngoài 3 file đã hex-dump — giả định đồng nhất cho 52+ file còn lại, chưa test hết.
- Giới hạn batch payload WAAPI qua Wine — giả định 500 object/batch, chưa test thật (liên quan Fact #20, #30).

## CONSTRAINTS (toàn Phase 1-4)
- KHÔNG hardcode số lượng Language/tên bank/event ID — đọc động từ `SoundbanksInfo.json` + thư mục thật.
- Version check chỉ log cảnh báo, KHÔNG raise lỗi.
- KHÔNG cài thư viện ngoài: `wwiser`, `vgmstream-cli`, stdlib Python, `waapi-client`.
- Carving dùng `mmap` trực tiếp; `ThreadPoolExecutor` CHỈ dùng cho gọi `vgmstream-cli` hàng loạt.
- Mọi lỗi log ra file, CẤM `except: pass`.
- Project GỐC luôn trỏ `WwiseSound/` — KHÔNG đọc nhầm `out_wwise/dvpl_unpacked/`.

## TÓM TẮT PHASE 1-3
| Phase | Script | Output | Trạng thái |
|---|---|---|---|
| 1 | `index_parser.py`+`carve_core.py` | `pool/<id>.wem` phẳng | DONE |
| 2 | `linker.py` | `manifest.json` | DONE |
| 3 | `generate_txtp.py`+`vgmstream-cli` | `out_wwise/wav*/` | DONE |

Phân loại Phase 3 theo `manifest.json` (KHÔNG đoán qua tên thư mục): `lang=None`→sfx_no_language; `lang="gup"`→official_voicepack_gup; `lang∈whitelist`→official_language; else→unknown_review_needed.

## Tái sử dụng cho nguồn khác
Chạy lại đúng script rời (không có `run_pipeline.py`) với `--input`/`--output` khác nhau. Kỷ luật bắt buộc: mỗi nguồn input PHẢI có `--output` RIÊNG, không ghi đè lẫn nguồn khác.

## Checkpoint
`git commit` sau mỗi phase. `manifest.json`/`inject_state.json` backup riêng, không nằm trong `.gitignore`. Lỗi giữa chừng Phase 4: không xoá `.wproj`, resume qua `inject_state.json`.

## Fact #31 [DONE] — Va chạm Source ID giữa ngôn ngữ (RXD)
Đọc DIDX của 37 bank (so size): 557/1565 ID có >1 kích thước khác nhau; cả 557 đều nằm trong
bank ngôn ngữ `rxd_*`. Đây là mức TỐI THIỂU (chưa bắt được khác nội dung cùng size).
`pool/` chỉ giữ 1 bản/ID: 8/8 mẫu khớp `rxd_us` (cuối thứ tự chữ cái).
[ASSUMPTION_UNVERIFIED] cơ chế "bản sau ghi đè bản trước" — chưa đọc code ghi `pool/` (không nằm trong carve_core.py).
Hệ quả: `wav_sid/` (decode từ pool) chỉ đúng 1 ngôn ngữ cho 557 ID này. Phase 4 (`wwise_builder.py`) chưa chạy cho RXD, sẽ ánh xạ sai nếu dùng pool.
Cách đúng: `vgmstream-cli -S 0 -o "<out>/<lang>/?n.wav" render_pool/<lang>/voiceover_crew.bnk`
(`?n` = Source ID). Verify: 26 bank, mỗi bản thường 592 stream, `_auto` 600 -> 15496 file, 0 lỗi.
Không dùng `ls` trong pipe (alias eza --color=always chèn mã màu); dùng `find -print0`.
