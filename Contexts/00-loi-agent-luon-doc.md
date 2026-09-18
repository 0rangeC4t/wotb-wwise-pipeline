# FILE 00 — LÕI (đọc TRƯỚC mọi file khác, MỌI phiên)

## SCOPE
Chứa: quy tắc vận hành cho agent (R1-R9), giới hạn vật lý nguồn dữ liệu, môi trường/lệnh khởi động, cách dùng bộ file.
KHÔNG chứa: chi tiết kỹ thuật từng nhánh (→ 01-04), danh sách Fact cụ thể (→ `INDEX.md`).

## R1-R9 — QUY TẮC BẮT BUỘC
- R1. Đọc xong bộ file được dán → tóm tắt lại trạng thái nhánh trong 2-3 câu → HỎI người dùng muốn làm gì tiếp. KHÔNG tự suy diễn rồi bắt tay làm luôn.
- R2. Chỉ tin dòng có tag `[DONE]` kèm bằng chứng cụ thể (git hash / lệnh grep / diff). Tag `[ASSUMPTION_UNVERIFIED]` = CHƯA xác nhận, không phải "gần đúng".
- R3. KHÔNG tin agent khác (Cline/Copilot/Antigravity) tự báo "thành công" — verify bằng `git log`/đọc file thật.
- R4. `setProperty`/`setReference` qua WAAPI có thể SILENTLY NO-OP — luôn readback verify sau khi set.
- R5. KHÔNG đoán tên property/API WAAPI theo docs SDK chung — verify qua `getPropertyAndReferenceNames` trước.
- R6. Lỗi im lặng (`return []`/`continue` thay vì raise) là bug nguy hiểm nhất trong dự án (đã xảy ra ≥3 lần độc lập). Không tin số liệu đẹp mà không tự hỏi "có phần nào bị bỏ qua âm thầm?".
- R7. Patch XML `.wwu` trực tiếp: giữ đúng thứ tự element đã verify từ ground truth — sai thứ tự khiến Wwise từ chối load.
- R8. Sửa 1 bug gốc → rà soát lại MỌI kết luận trước đó dựa trên dữ liệu bị bug đó ảnh hưởng.
- R9. Tách việc theo ranh giới tự nhiên (Work Unit/nhóm/bug riêng) — build → verify → commit riêng từng việc.

## GIỚI HẠN VẬT LÝ NGUỒN DỮ LIỆU
| Thành phần | Trạng thái |
|---|---|
| Audio asset | [DONE] đầy đủ |
| Event / GameSync | [DONE] cho TestProject, qua HIRC+JSON |
| SoundBank object | [NOT_STARTED] — biết mapping, chưa có script (Fact #20) |
| ShareSets | [NOT_STARTED] — chưa có kế hoạch cụ thể |
| Soundcaster Sessions | [IMPOSSIBLE] chỉ tồn tại ở `.wproj` gốc, mất khi compile |
| Queries đã lưu | [IMPOSSIBLE] cùng lý do |

"Phục dựng 100%" = 100% phần phục dựng được từ compiled bank, KHÔNG gồm 2 dòng `[IMPOSSIBLE]`.

## MÔI TRƯỜNG
- `WINEPREFIX=$HOME/.wwise_wine`, Wwise 2019.2.15.7667.
- Khởi động WAAPI server (chạy tay mỗi phiên, không tự chạy nền):
```bash
WINEPREFIX=$HOME/.wwise_wine wine "/home/orange_meow/.wwise_wine/drive_c/Audiokinetic/Wwise_2019.2.15.7667/Authoring/x64/Release/bin/WwiseConsole.exe" waapi-server "/mnt/data/wotb-wwise-pipeline/wproj/TestProject/TestProject.wproj" --allow-migration &
```
Đổi path `.wproj` nếu làm project khác.
- Quota agent: Cline (Gemini free, rate-limit 20 req/ngày), Antigravity (free tier ít, khoá ~167h/7 ngày khi hết — Flash Low/Medium cho việc dễ, Sonnet/Opus việc khó), Copilot (agent mode — verify git log, không tin báo cáo).
- Dọn script scratch vào `archive/` sau mỗi lần agent làm việc.

## CÁCH DÙNG BỘ FILE
| File | Dùng khi | Trạng thái nhánh |
|---|---|---|
| `01-nen-tang-on-dinh.md` | Việc carve/.pck/.bnk/manifest, câu hỏi format chung | [DONE], hiếm đổi |
| `02-testproject-phase4.md` | Việc trên `TestProject`, hoặc tra kỹ thuật build WAAPI chi tiết | [PAUSED] |
| `03-rxd-generalization.md` | Việc trên RXD mod | [IN_PROGRESS] — ưu tiên hiện tại |
| `04-ke-hoach-nhom-chuc-nang.md` | Kế hoạch tổ chức theo nhóm âm thanh | [NOT_STARTED] |
| `INDEX.md` | Cần xem tổng % tiến độ toàn dự án, không cần chi tiết | Tham khảo, không bắt buộc mỗi phiên |

Thường `00` + 1 file nhánh là đủ. Ngoại lệ: bắt đầu `04` thật → dán thêm `02` (vay kỹ thuật build WAAPI).

## RỦI RO CHƯA GIẢI ĐƯỢC CỦA CÁCH TÁCH FILE
- Không file nào có timestamp "cập nhật lần cuối" → 1 file có thể lag so với thực tế mà không ai biết cho tới khi phát hiện mâu thuẫn (đã xảy ra thật — xem Fact #18 trong `02`). Nếu nghi ngờ 1 dòng đã cũ, hỏi lại người dùng, đừng mặc định đúng.
