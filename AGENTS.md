# AGENTS.md — wotb-wwise-pipeline

**Mục tiêu dự án:** dựng lại project Wwise 2019.2 từ các bank đã compile của World of Tanks Blitz
(WAAPI qua Wine, Linux). KHÔNG phục dựng được: Soundcaster Sessions, Queries đã lưu.
**Người dùng đang học lập trình, không đọc được code.** Vì vậy bằng chứng duy nhất được chấp nhận
là **OUTPUT CỦA LỆNH THẬT**, không phải lời bạn nói.

## Bắt đầu mỗi phiên
1. Đọc `Contexts/00-*.md`, rồi đúng MỘT file nhánh liên quan việc được giao (không đọc cả repo).
2. Tóm tắt trạng thái nhánh trong 2-3 câu, rồi **HỎI** người dùng việc cần làm. Không tự bắt tay làm (R1).
3. Môi trường: `source agent_kit/env.sh` (không hardcode đường dẫn trong code).

## Quy tắc cứng
- **R2** Chỉ ghi `[DONE]` khi có bằng chứng (git hash / output lệnh). `[ASSUMPTION_UNVERIFIED]` = CHƯA xác nhận.
- **R3** Không tin báo cáo "thành công" của agent khác — **cũng không tin của chính bạn**. Chỉ tin output lệnh.
- **R4** `setProperty`/`setReference` qua WAAPI có thể IM LẶNG không làm gì → luôn đọc lại (readback) sau khi set.
- **R5** Không đoán tên property/API: hỏi `getPropertyAndReferenceNames` hoặc đọc dữ liệu gốc trước.
- **R6** Lỗi câm là bug nguy hiểm nhất: cấm `except: pass`, `return []`/`continue` thay cho raise. Bất thường phải raise hoặc log.
- **R7** Patch `.wwu`: giữ đúng thứ tự element đã verify từ ground truth.
- **R8** Sửa một bug gốc → rà lại MỌI kết luận phụ thuộc vào dữ liệu bị bug đó ảnh hưởng.
- **R9** Mỗi việc một vòng: build → verify → commit riêng → dừng.
- **R10** CẤM xóa hàng loạt: `rm -rf`, `git clean`, `git reset --hard`, `git push -f`. Muốn dọn file: liệt kê → chờ người dùng duyệt → `git mv` vào `archive/`.
- **R11** Không hardcode đường dẫn hay số lượng (ngôn ngữ, bank, event). Dùng tham số dòng lệnh hoặc đọc dữ liệu thật.
- **R12** KHÔNG sửa `agent_kit/invariants.json`, `agent_kit/silent_baseline.txt`, phần "bằng chứng" trong báo cáo; KHÔNG chạy `--update-baseline`; KHÔNG nới test hay sửa số mốc cho pass.
- **R13** Đọc file trước khi sửa. Không mô tả hay "sửa" code chưa đọc.
- **R14** Mọi con số trong kết luận phải đến từ output lệnh dán nguyên văn. Không chắc thì nói "không chắc".
- **R15** Không thêm thư viện ngoài: chỉ `wwiser`, `vgmstream-cli`, thư viện chuẩn Python, `waapi-client`.
- **R16** DỪNG và báo người dùng khi: cùng một lỗi lặp 3 lần; phải sửa file ngoài phạm vi được giao; kiểm tra FAIL mà chưa hiểu vì sao; yêu cầu mơ hồ.

## Vòng làm việc (bắt buộc)
1. Nhận việc theo mẫu "Việc / Xong khi / Được sửa". Thiếu mục nào thì hỏi.
2. Làm đúng phạm vi. Gặp lỗi → làm theo `agent_kit/skills/debug-and-fix/SKILL.md`.
3. Làm với WAAPI → làm theo `agent_kit/skills/wwise-waapi-wine/SKILL.md`.
4. Xong code → chạy `./agent_kit/verify.sh "tên việc" <nhóm>` và làm theo `agent_kit/skills/verify-and-report/SKILL.md`.
5. Điền báo cáo trong `reports/`. Chỉ báo "xong" khi trạng thái tự động là PASS.
6. Dừng. Chờ người dùng test tay. Chỉ commit khi người dùng bảo (hoặc việc đã được duyệt trước).
(Không phụ thuộc việc công cụ có tự nạp skill: bạn luôn đọc các file SKILL.md trên bằng tay khi tới bước tương ứng.)

## Kiểm tra song song bằng công cụ độc lập
Parser tự viết không được tự kiểm chứng chính nó. Mọi khẳng định về nội dung bank cần đối chiếu bằng công cụ thứ hai:
- Cấu trúc bank: dump bằng `wwiser` (`python3 tools/wwiser/wwiser.py -d xml -dn <tên> <bnk>`), rồi so bằng `roundtrip_diff.py`.
- Âm thanh: `vgmstream-cli` (số stream, thời lượng). "Render 0 lỗi" KHÔNG có nghĩa âm thanh đúng.
- Số liệu: so với các số mốc trong `agent_kit/invariants.json`.

## Tiết kiệm quota
Đọc ít file nhất có thể; không chạy lại việc đã `[DONE]`; mỗi phiên một việc nhỏ; không dán lại toàn bộ file dài vào hội thoại, chỉ trích đoạn cần.

## Mẫu giao việc (người dùng dùng)
```
Việc: <một nhóm/một lát cắt nhỏ>
Xong khi: <điều kiện kiểm tra được bằng lệnh/số>
Được sửa: <danh sách file>   (ngoài danh sách = không đụng)
```
