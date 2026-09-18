# FILE 04 — KẾ HOẠCH NHÓM CHỨC NĂNG — Fact #29-#30

## SCOPE
Chứa: ý định tổ chức lại công việc theo nhóm âm thanh, CHƯA triển khai.
Trạng thái nhánh: [NOT_STARTED].

## Fact #29 [DECISION] — Cách tổ chức
Build theo nhóm âm thanh chức năng (gunsound, hits, hangar music, GUI...) thay vì theo phase kỹ thuật. Mỗi nhóm: build → verify → commit → dừng.
Dùng 1 project Wwise DUY NHẤT xuyên suốt, chia theo Work Unit (mỗi nhóm = 1 Work Unit riêng). KHÔNG tạo nhiều `.wproj` riêng rồi ghép (rủi ro đụng GUID, khó merge).

## Fact #30 [OPEN_QUESTION] — Nhóm "gunsound" (ứng viên RXD)
Ứng viên: `RXD_WPN_PC.bnk`/`RXD_WPN_NPC.bnk` (11MB mỗi file, tiếng bắn/nạp đạn), `RXD_HITS_SFX_PC/NPC/MISC.bnk` (tiếng va chạm/nổ khi trúng đạn — loại khác).
Câu hỏi chưa trả lời:
1. Làm cho project nào — `TestProject` (Fact #14-#24, PAUSED) hay RXD (file 03, chưa có WAAPI setup)?
2. Gộp `HITS_SFX` vào "gunsound" hay tách riêng?

`[BLOCKED]` Nếu chọn RXD: KHÔNG có sẵn `.wproj`/Language/Game Syncs cho RXD — phải làm lại từ đầu tương đương Fact #19 trước khi build nhóm này. Giới hạn batch WAAPI (file 01, `[ASSUMPTION_UNVERIFIED]`, giả định 500/batch) cũng chưa test — rủi ro cao hơn với bank 11MB nhiều object.
