# agent_kit — bộ quy tắc và kiểm tra cho dự án wotb-wwise-pipeline

## Có gì
- `../AGENTS.md` (đặt ở gốc repo): quy tắc luôn được đọc, ngắn.
- `skills/verify-and-report/`: sau mỗi lần sửa code → chạy kiểm tra + sinh báo cáo có bằng chứng. Gồm 4 script: `check_invariants.py`, `scan_silent_failures.py`, `roundtrip_diff.py`, `make_report.py`.
- `skills/wwise-waapi-wine/`: quy trình làm việc với WAAPI qua Wine (readback, không đoán tên).
- `skills/debug-and-fix/`: quy trình debug, giới hạn 3 lần thử.
- `verify.sh`, `env.sh.example`, `invariants.example.json`.

## Cài (làm một lần)
1. `git commit` mọi thứ hiện có để có điểm quay lại.
2. Giải nén vào gốc repo: `AGENTS.md` ở gốc, thư mục `agent_kit/` ở gốc.
3. Nếu thư mục ghi chú không tên `Contexts/`, sửa đường dẫn trong `AGENTS.md`.
4. `cp agent_kit/env.sh.example agent_kit/env.sh` và sửa cho đúng máy.
5. `cp agent_kit/invariants.example.json agent_kit/invariants.json`, điền các TODO (đường dẫn thật; số bạn đã tự xác nhận), rồi commit.
6. `python3 agent_kit/skills/verify-and-report/scripts/scan_silent_failures.py --update-baseline`, xem kết quả, rồi commit. Code cũ không bị phạt, chỉ phát hiện MỚI mới FAIL.
7. Nếu công cụ agent của bạn tự nạp skill, chép `agent_kit/skills/*` vào thư mục skill của công cụ (xem tài liệu của nó). Nếu không, không sao: `AGENTS.md` đã trỏ thẳng tới từng SKILL.md.
8. Thêm `*_out.txt` vào `.gitignore`. Nên commit cả thư mục `reports/`.

## Dùng hằng ngày
Giao việc theo mẫu 3 dòng (Việc / Xong khi / Được sửa). Agent làm, chạy `./agent_kit/verify.sh`, điền báo cáo. Bạn mở báo cáo, làm theo mục "Bạn tự test thế này". Muốn chắc báo cáo không bị chỉnh: `make_report.py --verify reports/<file>.md`.

## Nói thẳng về giới hạn
- Tôi KHÔNG thể hứa "70% mỗi lần chạy". Bộ này giảm xác suất lỗi câm và báo cáo ảo bằng kiểm tra tự động, nhưng tỉ lệ thành công thật còn phụ thuộc agent và độ lớn của việc. Hãy đo: ghi 5 phiên đầu xem bao nhiêu phiên có báo cáo PASS **và** bạn test tay đạt. Dưới 50% thì chia việc nhỏ hơn.
- Các script đã được chạy thử trên dữ liệu **giả**, chưa chạy trên repo thật của bạn. Lần đầu có thể phải chỉnh đường dẫn.
- `scan_silent_failures` là kiểm tra theo mẫu (heuristic): bắt được các kiểu phổ biến, không bắt được mọi lỗi câm.
- `roundtrip_diff` chỉ so cấu trúc (đếm đường dẫn thẻ XML). Không thay được việc nghe và mở project kiểm tra.
- Cần Python 3.8 trở lên, chỉ dùng thư viện chuẩn.
