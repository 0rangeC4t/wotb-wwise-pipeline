# AUDIT TĨNH TOÀN BỘ CODE — wotb-wwise-pipeline (lần 2, phân tích sâu)

Ngày: 04/10/2026. Không chạy pipeline, không sửa file nào. Chỉ đọc code + `py_compile` + `grep`.

## 0. Cách đọc báo cáo

| Nhãn | Nghĩa |
|---|---|
| **[XÁC NHẬN]** | Thấy trực tiếp trong code hoặc đã chạy lệnh kiểm (ghi rõ dòng/lệnh) |
| **[SUY LUẬN]** | Hợp lý từ code + hiểu biết về Wwise/vgmstream, CHƯA kiểm trên dữ liệu thật. Có lệnh kiểm ở mục 6 |
| Mức **P0** | Làm sai kết quả đang có hoặc chặn Phase 4 RXD |
| Mức **P1** | Sai âm thầm hoặc phá quy tắc R6 / CONSTRAINTS, nên sửa trước khi mở rộng |
| Mức **P2** | Vệ sinh, độ bền, dễ nhầm |

**Giới hạn:** bản code trong `/mnt/project/` là snapshot chỉ đọc (file 05 đã cảnh báo "bản cũ"). Cần đối chiếu `git diff` với repo thật trước khi coi bất kỳ mục nào là còn hiệu lực. Chưa thấy: `tools/wwiser`, script sinh `music_hierarchy_investigation.md`, script ghi/dọn `wav_sid`, `wav_music`, `wav_lang`.

---

## 1. Đính chính so với báo cáo lần trước

| # | Lần trước nói | Thực tế sau khi kiểm lại |
|---|---|---|
| 1 | "File 05 nhầm: dry-run không quét crewvoice, nhưng `dryrun_validate` dùng `os.walk`" | **Tôi nhầm.** File 05 nói về `fix_random_container_render.py --dry-run`, script này dùng `os.listdir` (dòng 154) nên đúng là không quét `crewvoice/`. File 05 nhất quán với code. Hai script khác nhau, đừng gộp |
| 2 | "Carver ghi đè ID khác size mà không log" (lặp lại mục vệ sinh của file 05) | **Sai với code hiện tại.** `run_full_carve.py` dòng 36–66 CÓ ghi `logs/carve_collisions.log`. Mục vệ sinh của file 05 đã lỗi thời, hoặc file log đã bị xoá (script `os.remove` nó mỗi lần chạy, dòng 41–42). Xem C-06 |
| 3 | "File 01 mô tả version check chỉ log cảnh báo" | Nặng hơn: **không có version check nào chạy.** `parse_bkhd` định nghĩa ở `index_parser.py:3` nhưng grep không thấy ai gọi, `KNOWN_GOOD_VERSIONS` không tồn tại. Ràng buộc "version check chỉ log" đang thực chất là "không check" |
| 4 | `build_clean.py` "sẽ báo IndentationError" | **Đã xác nhận bằng `py_compile`:** `IndentationError: unexpected indent (build_clean.py, line 157)`. Đây là file duy nhất trong 70 file không biên dịch được |

---

## 2. Tóm tắt các phát hiện chính

| ID | Mức | Tệp | Một dòng | Bằng chứng |
|---|---|---|---|---|
| C-01 | P0 | `build_clean.py` | Không biên dịch; nếu sửa rồi chạy sẽ xoá thư mục `apk_bnk` đã DONE (Fact #22) | XÁC NHẬN |
| C-02 | P0 | `wwise_builder.py` | `lang is None` không bao giờ đúng sau Fact #27 → mọi SFX thành "Sound Voice" | XÁC NHẬN (dòng 145) |
| C-03 | P0 | `wwise_builder.py` | Ánh xạ SID→wav lấy wav render của txtp, chỉ vá riêng Random-bug; Sequence/Switch/Layer vẫn sai | XÁC NHẬN code, SUY LUẬN tác động |
| C-04 | P0 | `wwise_builder.py` | Mô hình 1 SID → 1 wav → 1 object không biểu diễn được 557 SID khác nội dung giữa 26 ngôn ngữ RXD | XÁC NHẬN code |
| C-05 | P0 | `wwise_builder.py`+`fix_random…` | Phát hiện Random-bug đệ quy (builder) nhưng decode không đệ quy (fix) → crewvoice rơi vào khe, không báo | XÁC NHẬN (dòng 154 vs 81) |
| C-06 | P1 | `run_full_carve.py` | "Bản cuối thắng" phụ thuộc thứ tự `os.walk`; log va chạm không dọn pool cũ; có sẵn 1 oracle miễn phí cho Fact #31 | XÁC NHẬN |
| C-07 | P1 | `reboot_wwise.py` + `build_music_hangar.py` + 3 script link | Hai đường dựng playlist nhạc mâu thuẫn; đường được verify (Fact #23) không có script nào tái lập trọn vẹn từ đầu; GUID hardcode theo một phiên bản project | XÁC NHẬN |
| C-08 | P1 | `render_wav.py` | Không dùng `-i` (khác `dryrun_validate.py`) → file có loop sẽ bị kéo dài + fade; ứng viên giải thích "quá dài" | XÁC NHẬN lệnh, SUY LUẬN hiệu ứng |
| C-09 | P1 | `linker.py` | `except Exception: pass`, `friendly_name/object_path` có thể bị điền bằng đường dẫn hệ thống tệp | XÁC NHẬN |
| C-10 | P1 | `index_parser.py` | Giả định AKPK block-size = 1 và bỏ trường cuối (nghi là language ID) | SUY LUẬN |

---

## 3. Chi tiết theo tầng

### 3.1. Tầng carve (`index_parser.py`, `carve_core.py`, `run_full_carve.py`)

**C-06 [P1, XÁC NHẬN] — Thứ tự ghi `pool/` và log va chạm**
- `run_full_carve.py` duyệt `os.walk` KHÔNG sắp xếp, rồi mỗi archive ghi `open(out_path,'wb')` đè lên bản trước. Đây chính là "code ghi pool/" mà Fact #31 ghi `[ASSUMPTION_UNVERIFIED]`: giờ đã thấy, cơ chế "bản sau đè bản trước" là đúng.
- Hệ quả: việc 8/8 mẫu khớp `rxd_us` (cuối bảng chữ cái) là kết quả của thứ tự duyệt của hệ tệp (thường trả theo thứ tự thư mục, không đảm bảo chữ cái). Chạy lại trên máy/filesystem khác có thể ra ngôn ngữ khác. Không được dùng `pool/` cho ID thuộc nhóm 557.
- Log va chạm chỉ ghi khi `os.path.exists(out_path)` và size khác. Nếu `pool/` còn file của lần chạy trước (script không dọn), lần đầu một ID xuất hiện cũng bị so với bản cũ → log lẫn lộn giữa các lần chạy. Cùng size nhưng khác nội dung thì không bao giờ được ghi (hash đã chứng minh 557 = 557, nên hiện chưa phát sinh).
- **Tận dụng:** nếu `logs/carve_collisions.log` của lần chạy RXD còn trên đĩa (hoặc chạy lại với `pool/` mới), nó liệt kê đúng ID nào xung đột, giữa archive nào. Đây là một nguồn đối chiếu độc lập cho cổng G1, không cần viết code mới.
- Ngoài ra `carve_core` trả `dict[fid]`, nên ID trùng *trong cùng một archive* (ví dụ `.pck` đa ngôn ngữ) gộp im lặng, không log.
- `if not index: continue` (không log): bank thật sự không có DIDX và bank parse hỏng không phân biệt được. Vi phạm tinh thần R6.

**C-10 [P1, SUY LUẬN] — Giả định AKPK có thể chỉ đúng cho 4 file đã hex-dump**
- `parse_akpk` đọc `count` tại offset cố định 52 rồi coi mọi entry 20 byte là `(id, flag, size, offset, reserved)` và dùng `offset` làm byte offset thô.
- Theo hiểu biết về định dạng AKPK, bảng này là bảng "Sounds" với trường thứ 2 là *block size* (nhân vào start block để ra byte offset) và trường thứ 5 là *language ID*. Nếu đúng: (a) pck có block size ≠ 1 sẽ cho offset sai; (b) cùng ID ở nhiều ngôn ngữ trong một `.pck` sẽ bị `dict[fid]` gộp. Fact #1 ghi `flag=1`, `reserved=0` đã thấy trên 4 file (`ASSUMPTION_UNVERIFIED` nói giả định đồng nhất cho phần còn lại). Cần kiểm tra thống kê trên mọi `.pck` (mục 6.1).
- Bảng "Banks" và "Externals" không được đọc. Hợp lý nếu bảng Banks rỗng ở mọi file; chưa có bằng chứng.
- Offset 52 cố định là mô tả "đã verify" nhưng lý do vật lý (Language map nhỏ cố định?) chưa được giải thích. Một pck có Language map khác kích thước sẽ lệch.

**Các lỗi nhỏ ở tầng này (P2, XÁC NHẬN)**
- `parse_didx`: `data.find(b'DATA')` lấy lần xuất hiện đầu tiên trong toàn file. Đúng ra DATA chunk nằm ngay sau DIDX (`didx_pos + 8 + didx_size`). Xác suất một ID/offset trùng chuỗi `DATA` rất nhỏ nhưng không bằng 0, và nếu có DIDX mà không có DATA thì trả `[]` im lặng.
- `parse_didx` đọc nguyên file vào RAM (bank 11 MB ổn, file lớn hơn thì không).
- `parse_akpk` còn `print` debug cho 2 entry đầu.
- `carve_core`: không kiểm `offset+size <= len(file)`; slice vượt biên trả dữ liệu cụt, không báo.

---

### 3.2. Tầng manifest (`linker.py`)

**C-09 [P1, XÁC NHẬN] — Ba vấn đề**
1. `parse_txtp_files` có `except Exception: pass` (dòng 27–28) — vi phạm CONSTRAINTS "CẤM except: pass".
2. Bước làm giàu bằng txtp gán `friendly_name = tên file txtp` và `object_path = đường dẫn hệ thống tệp` khi manifest chưa có. `wwise_builder.py` sau đó đổi `/`→`\` và ghép sau `\Actor-Mixer Hierarchy\Default Work Unit\` → có thể tạo đối tượng với path chứa đường dẫn đĩa (ví dụ `out_wwise\txtp\crewvoice\...`). Chỉ xảy ra với ID thiếu `ShortName` trong JSON, nên có thể hiếm; nên đếm xem có bao nhiêu mục như vậy.
3. `friendly_name` trong `parse_txtp_files` lấy theo txtp đầu tiên gặp trong `os.walk` → không xác định khi cùng SID nằm ở nhiều txtp.

**Các lỗi nhỏ**
- `_register(sf.get("Id"), …)`: nếu `Id` là `None` thì `manifest[None]` → khi `json.dump` thành khoá `"null"`. Chưa ai kiểm.
- Chỉ đọc 3 vị trí của Fact #4. 70 ID JSON bị loại (69 SFX bank ngoài RXD, 0 trong pool) có thể là do một vị trí thứ tư. Cần grep thô (Fact #4 đã dạy cách), xem 6.4.
- `manifest["language"]` là hợp (union) các ngôn ngữ qua mọi bank, nên **mất thông tin "ngôn ngữ nào có audio khác"**. Đúng với dữ liệu nhưng không đủ để builder biết khi nào cần nhiều wav/ID.
- Log mặc định `logs/report_dryrun.log` do 3 script dùng chung với ý nghĩa khác nhau: `linker` ghi orphan (ghi đè), `dryrun_validate` ghi OK/MISSING (ghi đè), `render_wav` đọc danh sách MISSING. Chạy `linker` sau `dryrun_validate` xoá danh sách bỏ qua → `render_wav` thử render cả file thiếu nguồn rồi đếm là "Failed".

---

### 3.3. Tầng txtp / render (`generate_txtp.py`, `render_wav.py`, `dryrun_validate.py`, `fix_random_container_render.py`)

**C-05 [P0, XÁC NHẬN] — Hai định nghĩa quét txtp khác nhau**
- `fix_random_container_render.py:154`: `sorted(os.listdir(txtp_dir))` + `os.path.isfile` → chỉ txtp ở thư mục gốc; bỏ qua toàn bộ `crewvoice/<lang>/`.
- `wwise_builder.py:81` (nhánh tự phát hiện): dùng `os.walk` + `is_random_container_bug` → thấy cả crewvoice.
- Kết quả: với RXD, builder coi các SID trong crewvoice là "bị ảnh hưởng", nhưng `wav/<SID>.wav` không do script fix sinh ra (nó không quét crewvoice) → điều kiện `is_affected and os.path.exists(sid_wav_path)` sai → rơi sang nhánh dùng wav render của txtp. Không lỗi, không log. Cùng lớp lỗi im lặng đã gặp ≥3 lần (R6).
- Logic phát hiện còn bị **nhân đôi**: hàm `is_random_container_bug` trong file fix và khối inline trong `main()` của cùng file là hai bản copy, không dùng chung → dễ lệch nhau khi sửa.

**C-05b [P0, XÁC NHẬN] — Bộ lọc "không có `CAkLayerCntr`"**
- Cả `is_random_container_bug` và khối inline loại txtp nếu có `CAkLayerCntr`. Với `RXD_gun_reloaded` (Layer → 2 Random 5 con / 10 con, Fact #32) thì Random bên trong bị gộp hay không phụ thuộc cách `wwiser` ghi txtp; hiện điều kiện này bỏ qua toàn bộ nhánh đó. Fact #17 chỉ chứng minh "Layer gộp 1 file là đúng khi nghe", **không** chứng minh "ánh xạ từng Sound con → file riêng" đúng.
- Mục đích khác nhau: để *nghe* thì gộp Layer là đúng; để *dựng từng Sound con* thì cần SID riêng. Hai mục đích đang dùng chung một bộ lọc.

**C-08 [P1] — `render_wav.py` không truyền `-i`**
- XÁC NHẬN: `dryrun_validate.py:36` dùng `vgmstream-cli -m -i`, còn `render_wav.py:85` dùng `vgmstream-cli -o … txtp` (không `-i`), `fix_random_container_render.py:115` cũng không có `-i`.
- SUY LUẬN: `vgmstream-cli` mặc định phát 2 vòng + fade cho luồng có cờ loop. Nếu txtp/wem mang loop, wav ra dài hơn thật. Khớp một phần triệu chứng "quá dài" đã nghe, và không liên quan đến sample rate. Cần kiểm (6.3).
- Việc thử nhận định "sai tốc độ do trộn sample rate khác nhau" (file 05) vẫn chưa kiểm chứng; hai giả thuyết (loop và sample rate) nên được tách ra khi test.

**C-11 [P1] — Gập `crewvoice/` bằng regex tên**
- `generate_txtp.py`: regex `\{l=([a-zA-Z()_]+)\}`. Ngôn ngữ có chữ số hoặc dấu `-` (chưa gặp với RXD nhưng không chắc với nguồn khác) không khớp; file ở lại thư mục gốc, không cảnh báo.
- `shutil.move(src, dest)` đè nếu cùng tên (không kiểm).
- Lỗi wwiser chỉ `print`, không ghi file → vi phạm "mọi lỗi log ra file".
- Nhánh fallback quét thư mục con của input có `.bnk` làm "ngôn ngữ", nên thư mục như `core/` bị coi là ngôn ngữ.
- Script ghi symlink `SoundbanksInfo.json`/`PluginInfo.json` **vào cây input** (là repo mod RXD gốc) — làm bẩn nguồn.
- `-gd` có mặt ở `generate_txtp.py` nhưng không có ở `generate_txtp_no_gd.py`; ý nghĩa cờ này không được ghi lại ở đâu trong 5 file tài liệu.

**C-12 [P2] — `generate_txtp_no_gd.py`**
- Vẫn mang bug Fact #26 (`render_pool` hardcode `out_wwise/render_pool`) và danh sách ngôn ngữ hardcode, trái CONSTRAINTS. Dễ chạy nhầm. Nên chuyển vào `archive/`.

---

### 3.4. Tầng builder (`wwise_builder.py`)

**C-02 [P0, XÁC NHẬN] — Phân loại SFX/Voice hỏng sau Fact #27**
- Dòng 145: `obj_type = "Sound SFX" if lang is None else "Sound Voice"`. `linker.py` giờ luôn ghi `language` là list (SFX = `[]`). `[] is None` là `False` → mọi SID, kể cả SFX, thành `Sound Voice`.
- Đây là hệ quả kinh điển của R8: sửa Fact #27 nhưng không rà người dùng cuối của trường `language`. Tài liệu Phase 3 ở file 01 (`lang=None`→sfx_no_language) có cùng lỗi thời.

**C-03 [P0] — Nguồn audio = wav render của txtp**
- XÁC NHẬN: nhánh `else` (SID không thuộc danh sách Random-bug) lấy `wav_dir/<đường dẫn txtp>.wav`, chọn `matching_txtps[0]` theo thứ tự txtp đã sắp xếp.
- SUY LUẬN (cần dữ liệu): file này là kết quả *phát* của event/container, có thể là nhiều nguồn nối tiếp (Sequence), nhiều nguồn song song (Layer), hay đúng một nguồn. Chỉ Random-bug được xử lý riêng. Sequence (`eMode: 0x01`), Switch, Blend không có phát hiện tương ứng. Một SID dùng chung giữa nhiều txtp nhận wav của txtp *đầu tiên theo thứ tự tên*, hoàn toàn tuỳ ý.
- Vì `wav_sid` (1565/1565 cho RXD) đã có, hướng an toàn là: chỉ dùng wav render khi có bằng chứng txtp đó chỉ chứa đúng 1 nguồn và nguồn đó là SID đang xét; còn lại dùng wav decode theo SID. Cần quyết định ở G1.
- Hệ quả khác: SID không xuất hiện trong bất kỳ txtp nào (ví dụ nguồn Music chưa tới, nguồn mồ côi) không có trong `valid_mapping` → bị loại im lặng, không đếm. Đây là ứng viên giải thích 147 dòng "nhiễu regex" của Fact #16 (SUY LUẬN, chưa kiểm).

**C-04 [P0, XÁC NHẬN code / SUY LUẬN Wwise] — Không biểu diễn được đa ngôn ngữ**
- `valid_mapping[sid]` là một đường dẫn. File `import.txt` có 3 cột (Audio File, Object Type, Object Path), không có thông tin ngôn ngữ nào. Với 557 SID có nội dung khác theo ngôn ngữ, builder tạo tối đa 1 Sound/1 wav.
- SUY LUẬN (cần xác nhận với Wwise 2019.2): một Voice Sound cần một nguồn riêng cho mỗi ngôn ngữ, nạp bằng tuỳ chọn ngôn ngữ của import (WAAPI có tham số ngôn ngữ trong `audio.import`; chưa rõ cột tương ứng trong tab-delimited). Đây là chủ đề của spike G2, không chỉ chuyện sửa path.
- Fact #14 ghi "Language mapping 20/21 khớp qua tag `{l=xx}` trong tên file": đó là cách *verify*, không phải cách *tạo*. Cách builder thực sự gán ngôn ngữ vào object trong TestProject chưa được tài liệu hoá; cần đọc lại trước khi tin rằng nó khái quát hoá được.

**C-13 [P0 khi dùng cho RXD, XÁC NHẬN] — Phụ thuộc trạng thái của TestProject**
- `txtp_dir = 'out_wwise/txtp'` hardcode (dòng 14).
- Đọc `random_bug_files.txt` và `out_wwise/random_container_bug_list_20260802.txt` từ cwd; nếu có thì **bỏ qua hoàn toàn phát hiện tự động**. Chạy trong thư mục TestProject cho RXD sẽ áp danh sách của TestProject. Định dạng file giả định mỗi dòng có đúng 2 trường (`parts[1]` là đường dẫn), dòng khác bị bỏ im lặng.
- `disambiguation_log.json`, `gamesync_map.json` ghi vào cwd, không theo `--output`; nguồn thứ hai ghi đè nguồn thứ nhất.
- Không đếm/log SID bị bỏ ở 3 điểm: `friendly_name is None`, không có trong `valid_mapping`, không có wav.
- Phân biệt hoa-thường khi phát hiện trùng đường dẫn (Python) có thể khác Wwise (SUY LUẬN: Wwise không phân biệt hoa-thường trong tên đối tượng cùng cấp). Tên không lọc ký tự cấm.
- Regex gamesync hardcode theo dạng mô tả của `wwiser` hiện tại; không thấy phiên bản wwiser được ghi lại trong tài liệu (RUNBOOK chưa có).

---

### 3.5. Tầng nhạc / patch `.wwu` (`build_*`, `reboot_*`, `link_*`, `reassign_*`, `test_wwu_edit.py`)

**C-07 [P1, XÁC NHẬN] — Hai đường dựng mâu thuẫn và không có đường nào tái lập kết quả đã verify**

| Đường | Cách tạo playlist | Schema patch | Trạng thái |
|---|---|---|---|
| A: `build_music_hangar.py` bước 9 → `reboot_wwise.py` | Dùng `PlaylistItemType` làm *cả* loại item lẫn kiểu nhóm (root=1, random=2, step-random=4, segment=0; dòng 394, 419, 450, 503); `setReference` (đã biết no-op, Fact #23) | `<ReferenceList><Reference Name="Segment"><ObjectRef…>` | **Không khớp Fact #23** |
| B: `build_playlist_tree.py`/`build_playlist_hangar.py` → `reassign_guids_and_link.py`/`link_music_playlist_segments.py` | Type 0/1 = Group/Segment, `PlayMode` 0–3 cho kiểu phát (khớp các test_*) | `<SegmentRef>` sau `</PropertyList>` | Khớp Fact #23 (đã diff byte-cho-byte) |

- `build_playlist_hangar.py` (đường B) **gọi `reboot_wwise.py` (đường A)** ở cuối → sẽ chèn thêm `ReferenceList/ObjectRef` lên các leaf, có thể chồng lên `SegmentRef`. Cần kiểm xem hai khối này cùng tồn tại có phá schema không.
- Cả hai đều xoá sạch con của root playlist của container `1054648317` rồi dựng lại (Fact #23 đã DONE). Chạy nhầm là mất công verify.
- Mô hình hai nghĩa của `PlaylistItemType` (0 = Segment ở A; 0 = Group ở B) cho thấy A là phiên bản trước khi hiểu đúng. Cần ghi rõ trong tài liệu: A bị thay thế bởi B.

**C-07b [P1, XÁC NHẬN] — GUID hardcode theo từng phiên bản project**
- Hai "họ" GUID cho cùng segment `860825692`:
  - `{5D36B392-…}`: `test_wwu_edit.py`, `test_bug1_fix.py`, `test_inspect_seg.py` (project cũ).
  - `{C48BAD93-…}`: `reboot_wwise.py`, `reassign_guids_and_link.py`, `link_music_playlist_segments.py`, `test_create_with_ref.py`, `test_playlist_build.py`, `test_same_container.py` (project hiện tại).
- `build_music_hangar` tạo segment mới với `onNameConflict: merge`; GUID chỉ ổn định nếu đối tượng đã tồn tại. Dựng từ đầu cho ra GUID khác → `reboot_wwise.py` vá không đúng đối tượng. Regex không khớp thì `if match:` (không `else`, `test_wwu_edit.py:30`, `reboot_wwise.py:47`) **không in gì**: lỗi im lặng đúng kiểu R6.
- `reassign_guids_and_link.py` ánh xạ GUID *sinh ra* → GUID *kỳ vọng* bằng `str.replace` trên toàn file, ghép từ một lần chạy cụ thể (`build_tree_good.txt`). Không tái dùng được.
- Hệ quả cho RXD: nếu phải vá `.wwu` (R7), cần cách tra GUID *động* qua WAAPI thay vì hằng số.

**C-14 [P1] — Rủi ro nhỏ khi vá XML bằng regex (XÁC NHẬN code / SUY LUẬN tác động)**
- `<MusicCue Name="Exit Cue" ID="…">` yêu cầu thẻ mở không tự đóng; nếu cue được ghi `…"/>` thì không khớp và bị bỏ qua im lặng.
- Regex leaf `<MusicPlaylistItem …ID="…"[^>]*>.*?</MusicPlaylistItem>` sẽ nuốt sang phần tử kế nếu leaf tự đóng (`/>`); với leaf đang có `PropertyList` thì ổn.
- Chèn `EndPosition`/`TimeMs` vào đầu `PropertyList` mà không theo thứ tự đã verify (R7). Wwise có thể chấp nhận, nhưng chưa có bằng chứng.
- Đọc/ghi `.wwu` ở chế độ text → CRLF thành LF ở `reboot_wwise.py`/`test_wwu_edit.py`, trong khi `link_*`/`reassign_*` ghi `\r\n`. Diff git nhiễu; có thể gây xung đột nếu cùng sửa.
- `pkill -9 -f wine` (`reboot_wwise.py:24`, `reboot_and_verify.py:15`) giết **mọi** tiến trình wine, kể cả khi bước save trước đó thất bại → có thể mất thay đổi chưa lưu. Và `start_waapi.py` không kiểm tra cổng 8080 đã bận, nên "đã kết nối" có thể là server cũ.

**C-01 [P0, XÁC NHẬN] — `build_clean.py`**
- `py_compile`: `IndentationError … line 157`. Khối `import_args = {` nằm lệch thụt lề, ngoặc không đóng; `wine_wav_path`, `segment_path`, `expected_track` dùng mà chưa định nghĩa; vòng đổi tên track thiếu phần đầu.
- Đây là phiên bản dở trong 7 file chưa commit của Fact #24. Bản đã commit (đã build apk, Fact #22) là bản đúng.
- Ngay đầu khi chạy: xoá `apk_bnk`, `apk_bnk_01`, `apk_bnk_02`, `apk.bnk` (`except Exception: pass`, dòng 54–55). Sau khi sửa cú pháp, chạy lại sẽ phá `apk.bnk` đã hoàn tất.
- Số mong đợi `(7, 7, 3)` hardcode ở bước verify; mismatch chỉ log, không fail.

**C-15 [P1] — `build_music_hangar.py` hardcode nặng**
- `segment_durations` 4 segment, `container_id = "1054648317"` và 4 segment ID, và các nhóm playlist đều viết cứng. Trái CONSTRAINTS "KHÔNG hardcode". Không dùng được cho `music_hangar` của nguồn khác, và cũng không dùng được cho SwitchContainer.
- Bước verify chỉ log `MATCH`, không `assert`/exit code → "đã verify" chỉ đúng khi người đọc log.
- Phụ thuộc `music_hierarchy_investigation.md` mà không có script sinh trong project; `dryrun_music_hierarchy.py` còn có dòng `'MATCHES' if len(objects_to_create) in (17, 51)` — tự kiểm tra theo kết quả mong đợi, không phải kiểm tra độc lập.

---

### 3.6. Script thăm dò và tiện ích (`test_*.py`, `find_*.py`, `delete_temp.py`, …)

- Không có assertion hay exit code; chỉ `print`. Không dùng làm hồi quy được. Giá trị còn lại là *tài liệu sống* về hành vi WAAPI 2019.2 (và nên được tóm vào tài liệu, đây chính là bằng chứng cho Fact #23/#24).
- Khối `finally` dùng `container_guid`/`container_id` có thể chưa được gán nếu bước tạo lỗi → `NameError` che lỗi gốc (`test_seg_*`, `test_types`, `test_playlist_properties`, `test_exitcue_property`, `test_seg_cues_query`, …).
- `find_throwaways.py` chỉ xoá tên chứa `throwaway`/`testbuild`; các script test khác tạo `Test_Cntr_*`, `Test_Seg_*`, `Test_*_Item` — nếu script chết giữa chừng, rác này **không** được dọn.
- `test_same_container.py`, `test_create_with_ref.py`, `test_playlist_ref_names.py` đụng vào GUID của container/root thật; `test_playlist_build.py` cố tình để rác lại.
- `delete_temp.py` xoá một GUID cứng, chỉ đúng với một lần chạy.
- `extract_source_ids` tính `sids_comment` nhưng không dùng (docstring nói có đối chiếu chéo — không).
- `dryrun_validate.py` chạy tuần tự từng file bằng `subprocess` (RXD 1765 file ⇒ chậm; còn lại không có hậu quả).
- Đường dẫn `/home/orange_meow/...` nằm trong `start_waapi.py`, `reboot_wwise.py`, `reboot_and_verify.py` và đường dẫn project `…/TestProject.wproj` trong nhiều test. Spike trên project nháp sẽ cần tham số hoá.

---

## 4. Lệch giữa tài liệu và code

| Nơi | Tài liệu nói | Code thực tế |
|---|---|---|
| File 01, CONSTRAINTS | "Version check chỉ log cảnh báo" | Không có check nào được gọi (xem mục 1.3) |
| File 01, Phase 3 | Phân loại `lang=None`→sfx | Không còn `None` sau #27; builder cũng chưa cập nhật |
| File 01, Fact #31 | "Chưa đọc code ghi `pool/`" | Code là `run_full_carve.py:55–69`: ghi đè theo thứ tự `os.walk` |
| File 05 §4 | "Carver ghi đè ID khác size mà không log" | Có log `logs/carve_collisions.log` (bị xoá mỗi lần chạy) |
| File 05 §2 | "Dry-run không quét crewvoice" | Đúng với `fix_random_container_render.py`, không đúng với `dryrun_validate.py` — tài liệu cần nêu tên script |
| File 02, Fact #12 | "copy thêm bản flat khớp path wwiser ghi" | `generate_txtp.py` hiện dùng `-gw render_pool/<lang>` (cách khác) |
| File 02, Fact #23 | Schema `SegmentRef` | `reboot_wwise.py` và `build_music_hangar.py` vẫn dùng schema cũ |
| File 02, Fact #17 | 1400 SID ảnh hưởng, 1032 được decode | `wwise_builder` chỉ ưu tiên wav-SID cho tập "affected" của fix script; 368 SID chênh lệch chưa được xử lý |

---

## 5. Ảnh hưởng tới các cổng G0–G4 (file 05)

| Cổng | Phát hiện liên quan | Việc phải làm trước khi qua cổng |
|---|---|---|
| G0 chốt mục tiêu | C-04 cho thấy "1 ngôn ngữ" là phạm vi tối thiểu hợp lý, vì builder hiện không biểu diễn được đa ngôn ngữ | Chốt `rxd_it` là phạm vi G0 |
| G1 dữ liệu | C-03, C-05, C-06 | Quyết định nguồn audio theo *từng loại SID* (xem 7.2); đối chiếu `carve_collisions.log` |
| G2 công cụ | C-04, C-07, C-07b, C-14 | Spike phải có cách gán ngôn ngữ cho Sound; tra GUID động; kiểm tra đồng thời schema vá `.wwu` |
| G3 verify | C-15 (verify chỉ log) | Script so cấu trúc phải trả exit code ≠ 0 khi lệch |
| G4 repo | C-01, tài liệu lệch (mục 4) | Không commit `build_clean.py` hiện tại; sửa tài liệu theo bảng mục 4 |

---

## 6. Danh sách lệnh kiểm chứng cho các mục SUY LUẬN

> Tất cả đều chỉ đọc. Tránh `ls` trong pipe (alias `eza --color=always`); dùng `find -print0`.

### 6.1. AKPK: block size và language ID (C-10)
Viết (hoặc chạy) một script chỉ-đọc quét mọi `.pck`: in tập giá trị khác nhau của trường 2 và trường 5 của mọi entry, cùng số ID trùng trong cùng một file. Nếu trường 2 chỉ có `1` và trường 5 chỉ có `0` ở mọi file ⇒ giả định an toàn.

### 6.2. Va chạm ID trong pool (C-06)
```bash
wc -l logs/carve_collisions.log
cut -d, -f1 logs/carve_collisions.log | sort -u | wc -l     # kỳ vọng 557 nếu log còn từ lần chạy RXD
```

### 6.3. Loop làm wav dài hơn (C-08)
So độ dài `wav` render với độ dài `.wem` gốc, và xem `vgmstream-cli -m` có dòng loop không:
```bash
vgmstream-cli -m <file.txtp> | grep -i loop
vgmstream-cli -m -i <file.txtp> | grep -i "stream total samples"
vgmstream-cli -m    <file.txtp> | grep -i "stream total samples"
```
Hai số khác nhau ⇒ loop đang kéo dài kết quả.

### 6.4. Vị trí thứ tư trong `SoundbanksInfo.json` (C-09, 70 ID bị loại)
Lấy 3–5 ID trong nhóm 70 và `grep -n "<ID>" SoundbanksInfo.json`, xem khoá cha. Nếu cha là mảng chưa được đọc (ví dụ `ReferencedStreamedFiles`) thì thêm vào `linker`.

### 6.5. Nguồn audio của builder (C-03)
Với RXD: đếm txtp theo kiểu
```bash
grep -L "CAkSound\[" -r out_wotb_rxd/txtp | wc -l
grep -l "eMode: 0x01" -r out_wotb_rxd/txtp | wc -l     # Sequence
grep -l "CAkSwitchCntr" -r out_wotb_rxd/txtp | wc -l   # Switch
```
Kỳ vọng các nhóm Sequence/Switch là nơi `wwise_builder` có thể dùng wav gộp sai.

### 6.6. Số SID builder bỏ im lặng
Chạy `wwise_builder.py` trên bản sao trong thư mục tạm, so `len(valid_mapping)` với số SID trong manifest có `friendly_name`: chênh lệch chính là tập bị loại.

---

## 7. Thứ tự xử lý đề xuất (chưa làm gì)

### 7.1. Bảo toàn (không viết code mới)
1. Đối chiếu bản trong repo với snapshot này bằng `git status`/`git diff` (xác định phiên bản nào đang hiệu lực).
2. **Không chạy** `build_clean.py`, `build_playlist_hangar.py`, `build_playlist_tree.py`, `build_music_hangar.py`, `find_throwaways.py` trên project có kết quả đã DONE.
3. Chạy các lệnh 6.2 và 6.3; chúng rẻ và trả lời hai câu hỏi lớn nhất (nguồn va chạm, nguyên nhân "quá dài").

### 7.2. Quyết định thiết kế (G1)
Bảng đề xuất cần bạn chốt, không phải mặc định:

| Loại SID | Nguồn audio đề xuất | Lý do |
|---|---|---|
| Voice, 557 SID khác nội dung giữa ngôn ngữ | `wav_lang/<lang>/<SID>.wav` | Duy nhất đúng theo ngôn ngữ |
| Voice, SID giống hệt giữa ngôn ngữ | `wav_lang` (bất kỳ) hoặc `wav_sid` | Hash đã chứng minh trùng nội dung |
| SFX | `wav_sid/<SID>.wav` | Một nguồn một file, không phụ thuộc txtp |
| Music | `wav_music/<SID>.wav` | Đã thống nhất ở Fact #22 |
| Wav render txtp | Chỉ để nghe | Đã có bằng chứng méo/chồng tiếng |

### 7.3. Sửa mã (sau khi chốt 7.2, mỗi việc một commit, theo R9)
1. `wwise_builder.py`: tham số hoá `--txtp-dir`, đầu ra log, bỏ đọc file danh sách cứng; sửa `lang is None` → `not lang`; đếm/ghi SID bị loại; chọn nguồn theo bảng 7.2.
2. `fix_random_container_render.py`: quét đệ quy và dùng chung một hàm phát hiện với builder; nhận `--pool-dir` hoặc nguồn từ bank cho đa ngôn ngữ.
3. `render_wav.py`/`fix_…`: thêm `-i` (hoặc cờ tường minh) sau khi 6.3 xác nhận.
4. `run_full_carve.py`: sắp xếp thứ tự duyệt, dọn pool cũ có cảnh báo, log ID trùng trong cùng archive, log bank trống.
5. `linker.py`: bỏ `pass`, ghi lỗi ra file; không dùng đường dẫn hệ thống tệp làm `object_path`.
6. Nhạc: ghi rõ đường B thay thế đường A trong tài liệu; chuyển các script cũ vào `archive/`; viết bước tra GUID động trước khi nghĩ đến `.wwu` cho RXD.
7. Dọn: chuyển `generate_txtp_no_gd.py`, `test_*` thăm dò cũ vào `archive/` (giữ nội dung làm tài liệu Fact #23/#24).

### 7.4. Không nằm trong audit này
- `tools/wwiser` và phiên bản đang dùng (cần ghi vào RUNBOOK).
- Script sinh `music_hierarchy_investigation.md`.
- Mô hình bus/volume routing của RXD (Init.bnk không có).
- Giới hạn batch WAAPI (giả định 500/batch, chưa test).

---

## 8. Bảng đếm nhanh

| Mức | Số mục | Ghi chú |
|---|---|---|
| P0 | 6 (C-01, C-02, C-03, C-04, C-05, C-13) | Chặn hoặc làm sai Phase 4 RXD |
| P1 | 9 (C-06…C-12, C-14, C-15) | Sai âm thầm, vi phạm R6/CONSTRAINTS |
| P2 | nhiều (mục 3.1, 3.3, 3.6) | Vệ sinh, độ bền |
| Đã xác nhận bằng lệnh | `py_compile` (1 lỗi / 70 file), `grep` (`lang is None`, `listdir`, `pkill`, `parse_bkhd`, GUID hai họ, log va chạm) | |
