# Đối chiếu audit đợt 2 (Codex) với code thật
Xác nhận: D2-06 HIGH (docstring cross-check, chỉ trả một tập; builder dùng hàm này), D2-01 MED, D2-03, D2-04.
D2-02 -> HIGH: render_pool có 6957 symlink, TẤT CẢ hỏng (find -xtype l); os.path.exists sai với liên kết hỏng.
D2-07 MED: 756 txtp crewvoice (21 ngôn ngữ x 36) không được quét bởi fix script; builder quét đệ quy -> có thể lệch, chờ xem phần else.
D2-08 LOW (hai bản logic hiện tương đương), D2-05 LOW, D2-09 LOW.
Mới: N1 (TB) symlink/JSON ghi vào input; N3 (thấp) except rộng quanh symlink; N4 (TB) nhận diện bằng tìm chuỗi cả file; N5 (cao) builder ưu tiên danh sách cũ có ngày, chỉ quét lại khi thiếu file; exists() bỏ qua txtp thiếu.
N2 chưa xác nhận: không có voiceover_crew.bnk ở gốc input.
pool/: có test.wav (sai Fact #6), 5641 wem vs mốc 5640.
Chờ: readlink, số wem, số bank voiceover_crew, 2 file danh sách, wwise_builder dòng 100-125.
## Cập nhật sau lần đối chiếu 2
- D2-02 HIGH, đã rõ nguyên nhân: symlink render_pool dùng đường dẫn tuyệt đối /home/orange_meow/wotb-wwise-pipeline/... (readlink) nên hỏng khi project chuyển sang /mnt/d (6957/6957 hỏng).
- N5 HIGH: wwise_builder nạp danh sách bug từ random_bug_files.txt và random_container_bug_list_20260802.txt (file ngày 2 Aug), chỉ quét lại khi không thấy file.
- N6 MED: wwise_builder bỏ qua im lặng mục manifest có friendly_name None và sid không có wav (chờ đếm).
- N2 gỡ: có 21 voiceover_crew.bnk tương ứng 21 thư mục ngôn ngữ, không có bank ở gốc.
- pool/: đã chuyển test.wav ra ../wotb-scratch; còn 5641 wem (mốc cũ 5640, chưa rõ nguyên nhân lệch).
