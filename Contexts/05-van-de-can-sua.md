# TỔNG HỢP 04/10 — RXD: đã biết / chưa biết / cần làm

## 0. Đã xác minh (có số liệu)
- Chạy lại RXD khớp bản cũ: Phase 1 16645/1565; Phase 2 manifest 7094, orphan 5; txtp 1765
  (crewvoice 26x55); render_wav 1765/1765. Fix #26/#27 nằm trong scripts/ dùng chung.
- wav_lang: 26 bank crewvoice decode thẳng từ bank (592 stream bản thường, 600 bản _auto) = 15496 file, 0 lỗi.
- Dump wwiser 26 bank -> 964 node, 55 event/bank, cấu trúc GIỐNG HỆT ở cả 26 bank (bỏ SID).
- 8 mẫu event; RTPC nam/nữ đặt trên Random Container (cắt 0.49, bật 0.51), khớp README
  (0-48 nam, 49-51 mute, 52-100 nữ); gup không chia giới; _auto khác bản thường ở RXD_gun_reloaded (đã kiểm chứng ở gup).
- 557/1565 Source ID có audio khác kích thước giữa các ngôn ngữ; pool/ chỉ giữ 1 bản (khớp rxd_us).
- Commit tài liệu 3a753e4. Còn 7 file TestProject sửa dở (Fact #24), chưa commit.

## 1. CHẶN việc dựng Phase 4 cho RXD (phải xong trước)
1. Định nghĩa "xong" chưa rõ. Fact #28 ("xong Phase 4 là đủ") mâu thuẫn với việc Phase 4 đang PAUSED 55-65% và
   INDEX ghi "dừng ở TestProject". Cần chốt: dựng cái gì, bao nhiêu ngôn ngữ, kiểm bằng gì.
2. Fact #31 mới ở mức SIZE. Chưa biết: (a) bao nhiêu SID cùng size nhưng khác nội dung, (b) script nào ghi pool/
   (không phải carve_core.py), (c) manifest.json giả định 1 ID -> 1 audio nên có sai với 557 ID không.
3. wwise_builder.py CHƯA ĐỌC: nguồn audio lấy từ đâu (pool? out_wwise/wav?), có hardcode path TestProject không.
4. Khả thi WAAPI 2019.2 CHƯA BIẾT: tạo Game Parameter, Random Container + RTPC curve (nhiều điểm, nội suy), Event
   với 2 ActionPlay + ActionStop, Layer Container, đặt reference (Fact #23: setReference từng no-op), và giới hạn
   batch (giả định 500, chưa test). Nếu không làm được qua WAAPI thì phải vá .wwu XML (R7), cần ground truth schema.
5. Cách verify chưa chốt. Đề xuất: so cấu trúc (bỏ SID) giữa dump JSON gốc và dump bank phục dựng
   (bank phải Generate qua GUI, CLI từng cho bank rỗng, Fact #23).

## 2. KHÔNG chặn dựng, nhưng cần làm rõ
- "Méo/sai tốc độ" khi nghe wav render: CHƯA tái hiện. Có 559/1430 txtp trộn nguồn khác sample rate
  (24000+48000, 22050+24000, 24000+44100). SUY LUẬN: lớp sample rate thấp phát nhanh khi trộn. Chưa test.
  Chỉ ảnh hưởng nghe thử, vì dựng dùng wav từng SID.
- 8 txtp crewvoice thiếu wav nguồn (chưa biết file nào).
- Lỗi gộp Random (Fact #17) có thật ở RXD: 204 txtp / 298 SID (hits...). wav_sid đã decode riêng các SID này;
  còn phải kiểm tra không trùng 557 ID. Dry-run gần như chắc chắn KHÔNG quét crewvoice (chỉ thư mục gốc txtp).
- 5 orphan của linker, 70 ID JSON bị loại (69 SFX, 0 trong pool), report_dryrun.log: chưa xem.
- Init.bnk không có trong thư mục RXD (wwiser báo thiếu bus): bus/volume routing không tái dựng được. Cần quyết định bỏ qua.
- Hình dạng RTPC: -1.0 tương ứng -96.3 dB là suy từ txtp; âm lượng thật ở hai đầu thanh chưa kiểm chứng trong game.
- Chưa biết: target của ActionStop (ngoài bank), thuộc tính của 2 Random cha (955394631 -> 786263179),
  node nằm trên cùng, "âm dốc" ở QCOMMAND, _auto ở ngôn ngữ khác gup, cách game gắn _auto cho xe.
- Mới phân tích crewvoice. 11 bank khác (WPN, HITS_SFX, MUSIC_*, HANGAR_MUSIC...) chưa dump, nên phạm vi
  Switch/State/Music Hierarchy của RXD chưa biết.

## 3. Tài liệu
- Mâu thuẫn trong file cũ: #28; #17 (1400 SID ảnh hưởng, chỉ decode 1032); #16 (616+3+8=627, nói 763, 147 dòng
  gán "nhiễu regex" không bằng chứng); #25 UNVERIFIED nhưng Bước 6 ghi DONE; #23 (TransitionList UNVERIFIED mà
  "khớp byte-cho-byte"); #14 (20/21 khớp, có 22 Language); #1 vs #4 (Unique 5640 vs 5633).
- File trong Claude project là bản cũ (chỉ đọc), phải tải bản mới trong Contexts/.
- Sửa wording bản mình soạn: Fact #27 chỉ SAI ở con số/nhãn (fix language=list vẫn đúng); câu "phần lớn là SFX"
  mới thấy qua vài ví dụ.

## 4. Kỹ thuật/vệ sinh (rẻ, nên làm)
- Bỏ giá trị mặc định trỏ out_wwise/ (đã thấy ở fix_random_container_render.py; chưa biết render_wav/wwise_builder).
- Carver ghi đè ID khác size mà không log: thêm cảnh báo.
- RUNBOOK.md (các lệnh, phiên bản wwiser/vgmstream, cách giải .dvpl), expected.json cho các số đối chiếu.
- 36 file nháp, .wsettings riêng máy trong git, sao lưu manifest/dump/json/txtp. Không đẩy out_* lên remote công khai.

## 5. CỔNG: đủ thông tin khi tất cả đạt
G0 Chốt mục tiêu: ví dụ "1 ngôn ngữ crewvoice (rxd_it) dựng được, cấu trúc khớp JSON gốc".
G1 Dữ liệu: số SID khác nội dung (hash) đã biết; nguồn audio build chốt (wav_lang cho voice, wav_sid cho SFX sau
   kiểm trùng 557); đã đọc wwise_builder.py.
G2 Công cụ: spike trên project NHÁP (không phải TestProject) tạo được Game Parameter + Random có RTPC curve +
   Event 2 Play + Stop + Layer, readback đúng (R4). Nếu không, có ground truth XML để vá .wwu.
G3 Verify: script so cấu trúc (bỏ SID) giữa 2 dump chạy được.
G4 Repo: tài liệu sửa xong, commit, backup dữ liệu, 7 file Fact #24 xử lý riêng.
