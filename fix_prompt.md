Sửa 4 script sau, theo đúng thứ tự. Sau MỖI script, chạy lại test để xác nhận số liệu KHÔNG lệch so với kết quả cũ đã verify. Nếu lệch, dừng lại báo cáo, không tự ý tiếp tục.

## 1. scripts/run_full_carve.py

- `except Exception as e: print(...)` hiện tại chỉ in ra màn hình, không ghi log, không đếm. Sửa: ghi mọi lỗi vào `logs/carve_errors.log` (path, exception), đếm `total_error_count`, in cuối cùng: "Scanned N archives, M failed (see logs/carve_errors.log), carved X files, Y unique IDs".
- Khi ghi `.wem` ra `pool_dir` mà `out_path` đã tồn tại: đọc size file cũ, so với size dữ liệu mới. Nếu KHÁC nhau, ghi cảnh báo vào `logs/carve_collisions.log` (fid, file cũ, file mới, size cũ, size mới) — đây là ID collision thật, cần biết. Nếu CÙNG size, ghi đè bình thường (đã biết an toàn).
- Xóa comment sai về Init.bnk (không liên quan quyết định core/Init.bnk đã chốt).

**Verify sau khi sửa:** chạy lại trên `input/WwiseSound` (bản gốc), xác nhận vẫn ra đúng carved=5915, unique=5633 như cũ. `carve_errors.log` và `carve_collisions.log` phải trống hoặc giải thích được rõ ràng nếu có nội dung.

## 2. scripts/linker.py

- Dòng `parse_txtp_files('out_wwise')` đang hardcode, không theo `--output`/`--input`. Thêm argparse `--txtp-dir` (default `'out_wwise'`), thay hardcode bằng `args.txtp_dir`.

**Verify sau khi sửa:** chạy lại trên bản gốc (mặc định `--txtp-dir out_wwise`), xác nhận vẫn ra đúng manifest=5798, carved=5633, orphans=0 như cũ.

## 3. scripts/generate_txtp.py

- Kiểm tra lệnh gọi `wwiser` hiện tại có đủ cờ `-r` (recursive) và `-gw <pool_dir>` (trỏ đúng thư mục wem) không — đối chiếu với lần chạy thành công trước đó tạo ra 934 `.txtp`. Nếu thiếu, đây là bug: code trên đĩa không khớp kết quả đã verify.
- Sửa cho đủ: `['python3', wwiser_py, '-r', '-g', '-go', out_dir, '-gw', os.path.abspath(pool_dir)] + bnk_files`.
- Thêm argparse `--input` (default `input/WwiseSound`), `--output` (default `out_wwise/txtp`), `--wemdir` (default `pool`).

**Verify sau khi sửa:** chạy lại trên bản gốc, xác nhận vẫn ra đúng 934 file `.txtp` như cũ.

## 4. scripts/dryrun_validate.py

- Comment cờ `-i` ghi sai là "ignore errors" — sửa comment cho đúng (không phải ignore-error, kiểm tra lại nghĩa thật qua `vgmstream-cli --help` nếu cần).
- Logic phát hiện lỗi hiện tại dựa vào text-match `"missing"`/`"cannot open"` trong stdout/stderr — không đáng tin cậy, có rủi ro false-negative nếu vgmstream-cli in thông báo khác. Trước khi sửa, verify bằng tay:
  ```
  vgmstream-cli -m -i out_wwise/txtp/<1_file_biết_chắc_OK>.txtp ; echo "Exit: $?"
  vgmstream-cli -m -i "out_wwise/txtp/play_hng_pl_wind_ghust.txtp" ; echo "Exit: $?"
  ```
  So sánh returncode giữa 2 trường hợp. Nếu returncode phân biệt rõ (VD 0 vs khác 0), sửa logic chính dùng `result.returncode != 0` làm tiêu chí MISSING_SOURCE, giữ text-match chỉ để lấy chi tiết lý do lỗi bổ sung.
- Thêm argparse `--txtp-dir` (default `out_wwise/txtp`), `--report` (default `logs/report_dryrun.log`).

**Verify sau khi sửa:** chạy lại trên bản gốc, xác nhận vẫn ra đúng OK=926, MISSING_SOURCE=8, và danh sách 8 file MISSING_SOURCE giống hệt danh sách cũ (không lệch file nào).

---

Sau khi cả 4 script sửa xong và verify không lệch số trên bản gốc, chạy lại toàn bộ pipeline 1 lần nữa trên modpack (`DP_Modpack_11`) bằng script đã sửa, báo lại đầy đủ: carved/unique/manifest/orphans, và nội dung `carve_errors.log`/`carve_collisions.log` nếu có gì bất thường (vì modpack tổng hợp nhiều nguồn, rủi ro collision cao hơn bản gốc).

Không tự ý thêm tính năng ngoài phạm vi liệt kê ở trên. Chỉ code, báo cáo số liệu, không giải thích dài dòng.
