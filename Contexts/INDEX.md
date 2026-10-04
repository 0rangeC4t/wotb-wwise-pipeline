# INDEX — TRA CỨU NHANH TOÀN BỘ FACT (không bắt buộc dán mỗi phiên)

| Fact | Tên ngắn | Trạng thái | File |
|---|---|---|---|
| #1 | Cấu trúc `.pck` (AKPK), Data Index offset 52 | DONE | 01 |
| #2 | Cấu trúc `.bnk` (DIDX), field order NGƯỢC AKPK | DONE | 01 |
| #3 | BKHD version 135 = Wwise 2019.2.15.7667 | DONE | 01 |
| #4 | 2 nguồn SoundbanksInfo.json, dùng bản gốc | DONE | 01 |
| #5 | `gup` = Language chính hãng, không phải mod | DONE | 01 |
| #6 | Naming convention, kiến trúc `render_pool/` | DONE | 01 |
| #7 | Music Hierarchy chỉ ở 2 bank | DONE | 01 |
| #8 | Wine khả dụng toàn pipeline | DONE | 01 |
| #9 | Trùng ID giữa bank = shared asset hợp lệ | DONE | 01 |
| #10 | Dry-run 934/934 — sửa kết luận sai trước đó | DONE | 01 |
| #11 | Modpack orphan cao là đặc tính, không phải bug | DONE | 01 |
| #12 | Bug copy `.bnk` sai path crewvoice | DONE | 01 |
| #13 | Regex bắt nhầm comment — vô hại hiện tại | DONE (theo dõi) | 01 |
| #14 | 4 bug `wwise_builder.py` | DONE | 02 |
| #15 | `gamesync_map.json` extraction | DONE | 02 |
| #16 | Gap 616→763 dòng import.txt | DONE | 02 |
| #17 | Random Container render collision | DONE | 02 |
| #18 | Lệnh khởi động WAAPI server | DONE (từng doc lag) | 02 |
| #19 | Game Syncs tạo qua WAAPI | DONE | 02 |
| #20 | Script tạo object `SoundBank` | NOT_STARTED | 02 |
| #21 | SwitchContainer báo "0 arguments" | ASSUMPTION_UNVERIFIED | 02 |
| #22 | `apk.bnk` hoàn tất | DONE | 02 |
| #23 | Music Playlist tree — schema SegmentRef | DONE | 02 |
| #24 | 4 bug nhỏ `music_hangar.bnk` | 1x IN_PROGRESS, 3x NOT_STARTED | 02 |
| #25 | Bulk-import 763 dòng mới | ASSUMPTION_UNVERIFIED | 02 |
| #26 | Bug hardcode `render_pool` (RXD) | DONE | 03 |
| #27 | Bug manifest.json 1-ID-1-ngôn-ngữ (RXD) | DONE | 03 |
| #28 | Phạm vi tổng quát hoá — dừng ở TestProject | DECISION | 03 |
| #29 | Tổ chức theo Work Unit/nhóm chức năng | DECISION | 04 |
| #30 | Ứng viên "gunsound" + câu hỏi mở | OPEN_QUESTION | 04 |
| #31 | Va chạm Source ID giữa ngôn ngữ RXD (557 ID); sửa #6, #9 | DONE | 01 |
| #32 | Cấu trúc crewvoice RXD: nam/nữ qua RTPC âm lượng nhạc, 8 mẫu event | DONE | 03 |
