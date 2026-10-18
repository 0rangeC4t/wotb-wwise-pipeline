---
name: debug-and-fix
description: Dùng khi script lỗi, kết quả sai số, kiểm tra FAIL, tiếng ra sai, hoặc người dùng báo "nó sai/không chạy/ra số lạ". Cũng dùng khi sắp sửa một bug để tránh đoán mò và vá chồng vá.
---

# debug-and-fix

1. **Tái hiện trước.** Ghi chính xác lệnh gây lỗi và dán output thật. Không tái hiện được thì nói rõ, đừng sửa.
2. **Tối đa 3 giả thuyết**, mỗi cái kèm cách kiểm tra bằng lệnh. Xếp theo khả năng.
3. **In giá trị trung gian** tại ranh giới giữa các bước (sau đọc, sau lọc, sau ghép) để tìm bước đầu tiên bị lệch. Dùng log có nhãn, không dùng `print` rải rác rồi quên xóa.
4. **Mỗi lần chỉ đổi MỘT thứ**, rồi chạy lại cùng lệnh ở bước 1 để so.
5. **Sửa gốc, không vá triệu chứng.** Nếu định thêm `try/except` hay `if` để lỗi biến mất mà chưa hiểu nguyên nhân, DỪNG: đó là lỗi câm (R6).
6. **Rà lại hậu quả (R8):** bug này làm sai kết luận nào trước đó? Liệt kê và kiểm tra lại.
7. **Chạy `./agent_kit/verify.sh`** sau khi sửa.
8. **Giới hạn:** cùng một lỗi sau 3 lần thử thì DỪNG, báo người dùng: đã thử gì, thấy gì, nghi gì. Không thử vòng thứ 4 một cách mù quáng (tốn quota mà không tiến thêm).
9. Có thể đối chiếu bằng công cụ độc lập (`wwiser`, `vgmstream-cli`) để loại trừ khả năng chính parser tự viết đang sai.
