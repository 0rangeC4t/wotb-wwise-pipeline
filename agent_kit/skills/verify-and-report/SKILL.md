---
name: verify-and-report
description: Chạy SAU MỖI LẦN viết hoặc sửa code trong dự án pipeline WoTB/Wwise, trước khi nói "xong" và trước khi commit. Chạy kiểm tra số mốc, quét lỗi câm/hardcode, so cấu trúc với bank gốc, rồi sinh báo cáo có bằng chứng thật. Dùng ngay khi vừa chạy script, build bank, sửa bug, hoặc người dùng hỏi "xong chưa / có đúng không / báo cáo".
---

# verify-and-report

Mục tiêu: người dùng không đọc được code, nên họ cần **bằng chứng do script sinh**, không phải lời tóm tắt của bạn.

## Các bước
1. Chạy: `./agent_kit/verify.sh "tên việc" <nhóm>` (nhóm = `TestProject`, `RXD`... theo `invariants.json`).
   Nó tự chạy `check_invariants.py` (số mốc) và `scan_silent_failures.py` (lỗi câm, hardcode), rồi ghi `reports/<ngày>_<tên>.md`.
2. Nếu việc có sinh bank mới: dump bank gốc và bank mới bằng `wwiser`, rồi chạy thêm
   `python3 agent_kit/skills/verify-and-report/scripts/make_report.py --title "..." --group <nhóm> --roundtrip <gốc.xml> <mới.xml> [--allow agent_kit/allow_roundtrip.json]`.
   Danh sách chỗ được phép lệch (`allow_roundtrip.json`) do NGƯỜI DÙNG viết.
3. Mở báo cáo. **Không sửa phần "Bằng chứng do script sinh".** Chỉ điền các mục `TODO`:
   - **Đã làm:** 1-3 dòng.
   - **CHƯA kiểm chứng được:** bắt buộc có nội dung thật. Ghi những gì bạn không chắc, chưa chạy, hoặc suy đoán. Ghi "không có" là vi phạm.
   - **Bạn tự test thế này:** 3-5 bước cụ thể kèm kết quả mong đợi (ví dụ "mở Wwise → Work Unit X → thấy N object", "nghe file Y → chỉ có một giọng").
4. Trạng thái tự động **FAIL** thì KHÔNG được báo hoàn thành. Chuyển sang `debug-and-fix`.
5. Người dùng có thể kiểm tra báo cáo không bị sửa: `make_report.py --verify reports/<file>.md`.

## Điều cấm (agent hay mắc)
- Cấm sửa số mốc, baseline hay test cho pass. Test FAIL thì ghi FAIL.
- Cấm tóm tắt thay cho output lệnh. Số liệu phải dán nguyên văn.
- Cấm nói "đã verify" khi chưa chạy `verify.sh` trong phiên này.
- "Render 0 lỗi" hay "chạy xong không crash" **không phải** bằng chứng đúng. Cần so với bank gốc hoặc số mốc.

## Cách đọc kết quả
- `check_invariants`: mỗi dòng PASS/FAIL/SKIP. Còn `TODO` hoặc không chạy check nào cũng tính FAIL (cố ý, để không bỏ sót âm thầm).
- `scan_silent_failures`: chỉ phát hiện MỚI so với baseline mới làm FAIL. Loại: bare-except, swallowed-exception, empty-return-in-if, hardcoded-path.
- `roundtrip_diff`: so số lần xuất hiện từng đường dẫn thẻ XML giữa hai dump. Cách này thô: nó không thấy lỗi nằm trong giá trị (ví dụ điểm RTPC). Nếu việc liên quan giá trị, hãy nêu rõ trong mục "CHƯA kiểm chứng được".
