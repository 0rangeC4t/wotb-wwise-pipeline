# FILE 02 — TESTPROJECT PHASE 4 (WAAPI Reconstruction) — Fact #14-#25

## SCOPE
Chứa: toàn bộ tiến độ/bug/kỹ thuật build WAAPI cho `TestProject.wproj`.
KHÔNG chứa: nhánh RXD (→ 03), kế hoạch tương lai (→ 04).
Trạng thái nhánh: [PAUSED] — dừng chủ động, KHÔNG xoá project, không quay lại trừ khi chủ động chọn (→ 04).

## TỔNG QUAN 10 BƯỚC
| Bước | Nội dung | Trạng thái |
|---|---|---|
| 1 | Wine Test (Windows+Android build) | DONE |
| 2 | `create-new-project` | DONE |
| 3 | Add 22 Language | DONE |
| 4 | `wwise_builder.py` (import.txt + gamesync) | DONE — Fact #14 |
| 5 | Music Hierarchy | IN_PROGRESS ~55-65% — Fact #22-#24 |
| 6 | Bulk import | DONE (4874/4874 ban đầu); ASSUMPTION_UNVERIFIED cho 763 dòng mới — Fact #25 |
| 7 | `inject_state.json` | NOT_STARTED |
| 8 | Test giới hạn batch WAAPI | NOT_STARTED (giả định 500/batch, chưa test) |
| 9 | Checkpoint git | DONE, duy trì đều |
| 10 | Compile SoundBank cuối | SKIPPED — quyết định dự án (mục tiêu học/xem cấu trúc, không release bank) |

## Fact #14 [DONE] — 4 bug `wwise_builder.py` (build đầu tiên)
| # | Bug | Fix |
|---|---|---|
| 1 | `.wav` đặt tên theo txtp-stem, `manifest.json` key theo `source_id` — không match 1-1 | Parse nội dung `.txtp` dựng bảng `source_id→.wav` |
| 2 | Định nghĩa "ambiguous" sai (nhầm multi-source-1-txtp thành mơ hồ) | Sửa đúng: ambiguous = 1 source_id ở NHIỀU file `.txtp` |
| 3 | 202 group Object Path collision — `tab-delimited-import` FAIL HOÀN TOÀN (0 object) khi 2+ dòng share path | Append `_<source_id>`, log `disambiguation_log.json` |
| 4 | Wine path double-prefix — Unix path bị hiểu nhầm tương đối, nối lặp đôi | Convert sang `Z:\...` trước khi ghi |

Kết quả verify (bằng GUID): import.txt 4874 dòng, Bulk import 4874/4874, 0 warning/error. Language mapping 20/21 khớp qua tag `{l=xx}` trong tên file (field `<Language>` trong `.wwu` luôn ghi cứng `SFX`, không dùng để verify).

## Fact #15 [DONE] — `gamesync_map.json`
State Group: 1 | Switch Group: 18 | Game Parameter: 41 | 647 source_id có gamesync reference | 449/1856 txtp có gamesync data.
Verify: `grep -l STATECHUNKS out_wwise/txtp/*.txtp` = 16 file.

## Fact #16 [DONE] — Gap 616→763 dòng bị bỏ sót trong import.txt
| Nhóm | Số lượng | Kết luận |
|---|---|---|
| Đủ wav+txtp+wem, bị bỏ sót do bug cùng lớp Fact #14 | 616 | Bug thật, đã fix |
| Convolution Reverb IR asset | 3 | Đúng thiết kế, thuộc ShareSets (chưa làm) |
| Bank sự kiện theo mùa không có trong snapshot | 8 | Đặc tính, không phải bug |

Sau fix: import.txt 4874→5637 (+763). Chênh lệch 147 dòng còn lại là nhiễu regex hậu tố `_<SID>` — 0 object mất thật. Đã đóng về LOGIC — nhưng xem Fact #25 (đã bulk-import thật chưa vẫn UNVERIFIED).

## Fact #17 [DONE] — Random Container render collision (277 txtp/1400 SID)
Root cause: `CAkRanSeqCntr` (Random, `eMode=0x00`) ≥2 `CAkSound` con → `wwiser` gộp cả playlist vào 1 `.txtp`/`.wav` → object con gán nhầm audio.
Phân biệt `CAkLayerCntr` (nhiều Sound con phát ĐỒNG THỜI — gộp 1 file là ĐÚNG): 521 file/7659 SID là LayerCntr an toàn, 277 file/1400 SID là RanSeqCntr Random (bug thật).
Fix (DONE): (1) decode riêng từng SID qua `vgmstream-cli` trực tiếp từ `pool/` — 1032/1032 SID OK. (2) `wwise_builder.py` ưu tiên `out_wwise/wav/<SID>.wav` cho 1032 SID này.
Verify 3 lớp: line count import.txt không đổi, spot-check 9 SID, đếm khớp đúng 1032.

## Fact #18 [DONE, từng bị doc lag] — Lệnh khởi động WAAPI server
```bash
WINEPREFIX=$HOME/.wwise_wine wine "/home/orange_meow/.wwise_wine/drive_c/Audiokinetic/Wwise_2019.2.15.7667/Authoring/x64/Release/bin/WwiseConsole.exe" waapi-server "/mnt/data/wotb-wwise-pipeline/wproj/TestProject/TestProject.wproj" --allow-migration &
```
Có bản ghi cũ từng nói lệnh này "chưa lưu" dù thực tế đã dùng được — dấu hiệu tài liệu có thể lag ở chỗ khác chưa phát hiện.

## Fact #19 [DONE] — Game Syncs tạo qua WAAPI
Trước đó pipeline chỉ tạo object hierarchy (Segment/Track/Container/Cue), CHƯA tạo THẬT State/Switch Group trong Game Syncs.
Danh sách: 1 State Group (`STATE_view_play_mode`→`arcade`/`sniper`), 18 Switch Group (2-3 switch/group).
Đã tạo: type/path `StateGroup`/`State` dưới `\States\Default Work Unit`, `SwitchGroup`/`Switch` dưới `\Switches\Default Work Unit`. Verify `.wwu`: 1 StateGroup đúng 2 state con (+1 "None" mặc định), 18 SwitchGroup đúng 37 switch con. Commit `be7312f`.
→ Sẵn sàng cho gán SwitchContainer (Fact #24 — CHƯA làm).

## Fact #20 [NOT_STARTED] — Script tạo object `SoundBank`
Biết file→bank mapping, CHƯA có script tạo object `SoundBank` dưới `\SoundBanks\` + gán Inclusions.
`[OPEN_QUESTION]` Bước 10 (generate soundbank cuối) đã SKIPPED chủ động — nếu không cần build `.bnk` cuối, mục đích thật của việc tạo object `SoundBank` này cần xác nhận lại (chỉ hoàn chỉnh cấu trúc tham khảo, hay lý do khác?).
Kế hoạch nếu làm: (1) test 1 `SoundBank` cho bank `apk`, verify qua `.wwu`; (2) xác định cơ chế gán object vào SoundBank — field `Inclusions` hay API `ak.wwise.core.soundbank.*`, CHƯA XÁC ĐỊNH, cần test thật; (3) bulk tạo ~52 bank chỉ sau khi (1)(2) verify đúng.

## Fact #21 [ASSUMPTION_UNVERIFIED] — SwitchContainer `109552928` báo "0 arguments"
Ghi nhận trước khi Fact #19 (Game Syncs) tồn tại. 2 khả năng chưa phân biệt: (a) Game Sync thật chưa có lúc query, (b) bản chất Decision Tree đúng là không cần argument. Việc cần làm: query lại SAU khi Fact #19 DONE, so sánh kết quả.

## Fact #22 [DONE] — `apk.bnk` (17 object) hoàn tất
2 bug đã fix: (1) audio Interactive Music phải trỏ `out_wwise/wav_music/<SID>.wav` (tự decode từ `pool/`); (2) Entry/Exit Cue là property `TimeMs` (Real64) trên `MusicCue` CÓ SẴN trong `<CueList>`, kèm `EndPosition` (Real64) ở cấp `MusicSegment`.
Verify: diff `.wwu` khớp đúng duration; xác nhận bằng tai thật trong Wwise GUI. KHÔNG cần đụng lại.

## Fact #23 [DONE] — Music Playlist tree (`music_hangar.bnk`) — phần khó nhất dự án
Kết luận chính: WAAPI 2019.2 KHÔNG hỗ trợ set Segment reference qua API chuẩn — `setReference("Segment",...)` silently no-op (giới hạn version thật, chỉ expose qua `PlaylistRoot` từ WAAPI 2023.1+).
Schema đúng (xác nhận từ project mẫu "Wwise Adventure Game"):
```xml
<MusicPlaylistItem Name="" ID="{item_guid}" ShortID="...">
    <PropertyList><Property Name="PlaylistItemType" Type="int16" Value="1"/></PropertyList>
    <SegmentRef Name="{segment_name}" ID="{segment_guid}"/>
</MusicPlaylistItem>
```
`SegmentRef` sibling độc lập của `PropertyList`, KHÔNG trong `ReferenceList`.
Cấu trúc `MusicPlaylistContainer`: `ReferenceList` / `ChildrenList` (MusicSegment con) / `TransitionList` (`[ASSUMPTION_UNVERIFIED]` — default rỗng do WAAPI tự tạo, CHƯA xác nhận khớp behavior gốc) / `Playlist` (root MusicPlaylistItem).
Cách patch: `project.save()` → đọc file → regex-patch chèn `SegmentRef` sau `</PropertyList>` của leaf (dùng GUID target) → ghi file → `project.open bypassSave=True`.
Cách verify đúng — KHÔNG dùng preview GUI qua Wine (quirk Wine, không phải lỗi data): Generate SoundBank QUA GUI (không CLI — CLI từng cho bank rỗng 32 byte dù log báo thành công; verify size >1MB) → dump `wwiser -d xsl` → diff `CAkMusicRanSeqCntr` field-by-field. Kết quả: khớp byte-cho-byte.
Đã bác bỏ: nghi ngờ ShortID khác gốc gây lỗi game — game resolve theo TÊN (string hash runtime), không hardcode ID số (bằng chứng: RXD mod thêm Event mới vẫn chạy được).

## Fact #24 [1x IN_PROGRESS, 3x NOT_STARTED] — 4 bug nhỏ `music_hangar.bnk`
| Bug | Gốc | Build ra | Trạng thái |
|---|---|---|---|
| MakeUpGain prop | cProps=1, -8.0 | cProps=0 (mất) | IN_PROGRESS — code sửa đã viết + áp dụng qua `sed`, CHƯA build+verify lại |
| DirectParentID/OverrideBusId | ParentID=109552928, OverrideBusId=0 | bị lẫn/sai | NOT_STARTED — prompt sẵn cho Cline |
| Tempo/Meter | 92.0, 3/4 | 120.0, 4/4 (default) | NOT_STARTED — prompt sẵn |
| bIsShuffle | 0 | 1 (đảo ngược) | NOT_STARTED — prompt sẵn |

Quy tắc: KHÔNG đoán tên property WAAPI, mỗi bug fix+verify+commit riêng, tự đọc git log/diff thật.
SwitchContainer: NOT_STARTED (cần giải Fact #21 trước).

## Fact #25 [ASSUMPTION_UNVERIFIED] — Bulk-import 763 dòng mới sau Fact #16
import.txt tăng 4874→5637 sau fix Fact #16, nhưng CHƯA XÁC NHẬN 763 dòng mới đã thực sự bulk-import vào project. Cần kiểm tra trước khi coi Bước 6 hoàn tất.
