# FILE 03 — RXD GENERALIZATION TEST — Fact #26-#28

## SCOPE
Chứa: tiến độ test pipeline trên nguồn RXD-MODPACK-PROJ-4.1.0.
KHÔNG chứa: build WAAPI cho RXD (chưa tồn tại — xem Fact #30 nếu cần bắt đầu).
Trạng thái nhánh: [IN_PROGRESS] — ưu tiên hiện tại.

Input: `/home/orange_meow/RXD-MODPACK-PROJ-4.1.0-main/src/mod/WwiseSound/`
Output: `/home/orange_meow/RXD-MODPACK-PROJ-4.1.0-main/src/mod/out_wotb_rxd/`

## TIẾN ĐỘ
| Phase | Kết quả | Trạng thái |
|---|---|---|
| 1 (`run_full_carve.py`) | 16645 file carved, 1565 unique ID, RIFF magic OK | DONE |
| 2 (`linker.py`) | Carved 1565 / Manifest 7094 / Orphans 5 | DONE (chênh lệch lớn là bình thường — RXD chỉ mod 1 phần game) |
| wwiser export `.txtp` thủ công | Cần gộp `core/Init.bnk` khi export trực tiếp | DONE (thao tác cần nhớ, không phải bug) |

## Fact #26 [DONE] — Bug hardcode `render_pool`
`generate_txtp.py` dòng 48: biến `render_pool` hardcode `'out_wwise/render_pool'` (path riêng TestProject), bỏ qua `--output`. Fix: `os.path.join(os.path.dirname(out_dir), 'render_pool')`. Verify: chạy OK.

## Fact #27 [DONE] — Bug manifest.json giả định 1-ID-1-ngôn-ngữ
Nghi ngờ ban đầu (dict `crewvoice_langs` hardcode tên thư mục, RXD dùng tên khác `rxd_cn/` không khớp) — SAI, chỉ là triệu chứng.
Root cause thật: `manifest.json` của `linker.py` giả định 1 ID chỉ 1 ngôn ngữ, trong khi RXD có 2970/7164 ID (~41%) hợp lệ dùng chung nhiều ngôn ngữ (audio placeholder qua `UsingReferenceLanguageAsStandIn`) → field `language` chỉ giữ ngôn ngữ ghi sau cùng, mất data.
Fix: field `language` LUÔN LÀ LIST (kể cả 1 ngôn ngữ), đồng nhất cho mọi nguồn mod.
Verify: 26 thư mục × 55 file crewvoice = 1430, 0 trùng tên, 1765 `.txtp` duy nhất. Data GỐC Wargaming cũng có 10 ID trải 22 ngôn ngữ từng bị collapse y hệt → fix tổng quát thật. Git diff manifest trước/sau: 0 ID thêm/mất, orphan=0 cả 2 phía → không regression.

## Fact #28 [DECISION] — Phạm vi tổng quát hoá
"Xong Phase 4" = đủ mục tiêu. KHÔNG cần tổng quát hoá thành tool đa năng cho nhiều bản Wwise khác (WoTB dùng 2019.2 lâu dài, không cấp thiết).

## TRẠNG THÁI HIỆN TẠI
Fact #26+#27 đã đóng, không còn việc treo cụ thể. Bước tiếp theo CHƯA XÁC ĐỊNH — 2 hướng khả dĩ: (a) chạy tiếp Phase 3/4 trên RXD để tự lộ thêm bug, (b) coi nhánh đã đủ, chuyển sang `04-ke-hoach-nhom-chuc-nang.md`.

`[ASSUMPTION_UNVERIFIED]` Chưa xác nhận code fix #26/#27 nằm ở `scripts/` DÙNG CHUNG với TestProject (đúng tinh thần tổng quát hoá) hay 1 bản copy riêng dưới thư mục RXD — nếu là bản copy riêng, fix KHÔNG tự áp dụng khi quay lại TestProject.
