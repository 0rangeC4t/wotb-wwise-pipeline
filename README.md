# wotb-wwise-pipeline

Bộ script để **tách âm thanh từ file game World of Tanks Blitz và dựng lại thành project Wwise** (2019.2, điều khiển qua WAAPI, chạy trên Linux bằng Wine).

*English: a hobby toolchain that carves WoTB audio out of `.pck`/`.bnk` archives and rebuilds a Wwise 2019.2 project via WAAPI under Wine. Work in progress.*

> **Trạng thái: đang phát triển, chưa hoàn chỉnh.** Phần tách và đối chiếu dữ liệu đã chạy ổn. Phần dựng lại project Wwise mới làm được một phần (xem bảng dưới).

## Lưu ý về bản quyền

- Repo này **không chứa và không phân phối** file âm thanh hay file gói của game. Âm thanh thuộc về Wargaming.
- Bạn cần tự có file game hợp pháp của mình (thư mục `WwiseSound/`) để chạy.
- Đây là dự án cá nhân, không liên kết với Wargaming hay Audiokinetic.
- Giấy phép cho code của repo: chưa chọn. Công cụ bên thứ ba (như `wwiser`, `vgmstream`) theo giấy phép riêng của chúng.

## Làm được gì, chưa làm được gì

| Phần | Việc | Trạng thái |
|---|---|---|
| Phase 1 | Tách file `.wem` từ `.pck` / `.bnk` | Xong, đã đối chiếu số liệu |
| Phase 2 | Liên kết với `SoundbanksInfo.json`, sinh `manifest.json`, tìm orphan | Xong |
| Phase 3 | Sinh `.txtp` (wwiser) và render ra `.wav` (vgmstream-cli) | Xong |
| Phase 4 | Dựng project Wwise qua WAAPI (`TestProject`, game gốc) | **Một phần:** Game Syncs, `apk.bnk` xong; nhạc hangar đang làm |
| Chưa làm | Tạo object `SoundBank`, ShareSets | Chưa bắt đầu |
| RXD modpack | Chạy thử Phase 1-3 như bài kiểm tra tổng quát hoá | Chưa có project Wwise cho RXD |
| **Không thể** | Soundcaster Sessions, Queries đã lưu | Chỉ tồn tại ở project gốc, mất khi compile |

## Cần gì để chạy

- Linux, Python 3
- `wwiser` (có sẵn trong `tools/wwiser/`) và `vgmstream-cli`
- Phase 4: Wine, Wwise 2019.2.15 và thư viện `waapi-client`
- Dữ liệu game của bạn đặt ở `input/WwiseSound/` (gồm các file `.pck`, `.bnk` và `SoundbanksInfo.json`)

## Cách chạy nhanh (Phase 1-2)

```bash
# Phase 1: tách .wem vào pool/
python3 scripts/run_full_carve.py --input input/WwiseSound --output pool

# Phase 2: sinh manifest.json và báo cáo orphan
python3 scripts/linker.py --input input/WwiseSound --output pool --manifest manifest.json
```

Các script khác (`generate_txtp.py`, `wwise_builder.py`, `build_music_hangar.py`...) xem `--help` của từng file. Phase 4 thao tác trực tiếp trên project Wwise: **hãy sao lưu `wproj/` trước khi chạy** và đừng chạy khi còn thay đổi chưa lưu trong Wwise.

## Cấu trúc thư mục

| Thư mục | Nội dung |
|---|---|
| `core/` | Đọc chỉ mục `.pck` / `.bnk` và cắt file |
| `scripts/` | Các bước của pipeline |
| `tests/` | Test cho phần tách file (cần dữ liệu game nên chỉ chạy được trên máy có `input/`) |
| `Contexts/` | Ghi chú kỹ thuật: các Fact đã kiểm chứng, tiến độ từng nhánh |
| `audit/` | Ghi chú rà soát lỗi (đang tiến hành) |
| `agent_kit/`, `AGENTS.md` | Quy tắc và công cụ kiểm tra cho AI agent làm việc với repo này |
| `archive/` | File kết quả chạy thử cũ, giữ lại để tham khảo |

## Hạn chế đã biết

- Vài script còn ghi cứng đường dẫn máy (ví dụ `reboot_wwise.py`, `test_wwu_edit.py`).
- Một số chỗ trong code có thể bỏ qua lỗi âm thầm; việc rà soát đang làm, tiến độ ghi ở `audit/TIEN-DO.md`.
- Chỉ nhắm tới Wwise 2019.2 (phiên bản của WoTB).
- Âm thanh voice theo ngôn ngữ cần giải mã trực tiếp từ bank: thư mục `pool/` phẳng theo ID không đủ khi cùng ID có audio khác nhau giữa các ngôn ngữ.
- Bản `.wav` render từ `.txtp` cho voice phi hành đoàn có thể bị chồng giọng nam và nữ, chưa nên dùng để nghe hay dựng.

## Về dự án

Dự án làm một mình, có dùng AI agent hỗ trợ viết code. Vì vậy mọi kết quả đều được đối chiếu bằng số liệu và công cụ độc lập (xem `AGENTS.md`). Góp ý và báo lỗi rất được hoan nghênh, nhất là từ người đã làm mod Wwise.
