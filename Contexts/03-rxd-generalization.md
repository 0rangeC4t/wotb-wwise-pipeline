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

## CẬP NHẬT 02/10 (chạy lại từ đầu sau khi xoá do hết dung lượng)
Input: ~/RXD-MODPACK-PROJ-4.1.0-main/src/mod/WwiseSound/ (.bnk đã giải .dvpl, cạnh bản .dvpl)
Output: .../src/mod/out_wotb_rxd/{pool,manifest.json,txtp,render_pool,wav,dump}
Số khớp bản cũ: Phase 1 16645/1565; Phase 2 manifest 7094, orphan 5; txtp 1765 (crewvoice 26x55);
render_wav.py 1765/1765, 2.8G, 0 lỗi. Fix #26/#27 nằm trong scripts/ dùng chung (commit 48f4ef9, bd8f75f).

## Fact #27 [SỬA]
"2970/7164 ID nhiều ngôn ngữ" SAI: 2970 = ID xuất hiện ở >1 entry JSON (phần lớn là SFX dùng chung, language=[]).
ID nhiều ngôn ngữ thật trong manifest = 600. `language` không phải list = 0.
70 ID có trong JSON nhưng không vào manifest: 69 SFX của bank ngoài RXD, 0 trong pool (chưa rõ vì sao linker bỏ).

## Cảnh báo `wav/` crewvoice
`wav/crewvoice/*` (render từ txtp) KHÔNG dùng để nghe/dựng: mỗi event phát cả 2 giọng nam+nữ chồng nhau
(2 ActionPlay), 878/1430 file có sample chạm trần (rxd_it tới 770 sample). "Render 1765/1765, Failed 0" chỉ nói
vgmstream không lỗi. Nguyên nhân tiếng méo/sai tốc độ người dùng nghe: CHƯA xác định
([ASSUMPTION_UNVERIFIED] hai giọng chồng gây rè; chưa có bằng chứng cho sai tốc độ).
`fix_random_container_render.py`: mặc định trỏ out_wwise/ của TestProject (phải truyền đủ 4 tham số),
bỏ qua file có LayerCntr, CHƯA chạy cho RXD.

## Lệnh cần nhớ
wwiser: `python3 tools/wwiser/wwiser.py` (không phải .pyz). Dump: `-d xml -dn <tên> <bnk>` (ghi vào cwd).
Biến $RXD mất khi mở terminal mới. Alias ls=eza --color=always làm hỏng xargs.

## Fact #32 [DONE] — Cấu trúc crewvoice RXD (`voiceover_crew.bnk`)
Mod: README ghi thanh âm lượng NHẠC trong game: 0-48 = nam, 52-100 = nữ, 49-51 = mute. `rxd_gup` không chia giới.
`rxd_xx_auto` = xe autoloader; ở `gup` chỉ khác event RXD_gun_reloaded (13 SID chỉ có ở _auto, 5 chỉ ở bản thường);
[ASSUMPTION_UNVERIFIED] các ngôn ngữ khác giống `gup`.
Dump: dump/<lang>.xml (26 file, 133M), dump/json/<lang>.json. Mỗi bank 964 node, 55 event;
cấu trúc GIỐNG HỆT ở cả 26 bank khi bỏ qua SID.
RTPC: RTPC_ext_settings_volume_master_music (id 244438798), GameParameter, Volume, Additive, dB, đặt trên
Random Container (nam/nữ) hoặc trên Sound (dốc). Y=-1.0 tương ứng -96.3 dB trong txtp
([ASSUMPTION_UNVERIFIED] suy từ txtp, chưa kiểm mã wwiser). Đường cong (X,Y):
 NAM [(0,-1),(0.49,0),(0.491,-1),(1,-1)]  NU [(0,-1),(0.51,-1),(0.511,0),(1,-1)]  DOC [(0,-1),(1,0)]
Mốc 0.49/0.51 khớp README. Âm lượng thực ở 2 đầu thanh CHƯA kiểm chứng trong game.
Event có 2 ActionPlay riêng (nam, nữ) -> "-L2" trong txtp là 2 Play, KHÔNG phải Layer Container.
Layer Container duy nhất của bank: RXD_gun_reloaded (-> 2 Random 5 con/10 con, không RTPC).
8 mẫu (số event): 28 nam+nữ | 10 nam+nữ+Sound DOC | 6 nam+nữ+Random DOC | 3 Random+Stop |
3 Random+Sound DOC+Stop | 2 nam+nữ+Sound DOC+Stop (RXD_AUTO_ON/OFF) | 2 Sound DOC+Stop | 1 Layer (reload).
Sound DOC thứ ba (vd 37824647 ở RXD_ammo_bay_damaged) = âm hỏng thùng đạn/module (người dùng nghe xác nhận).
Cây cha: Random 955394631 -> Random 786263179 -> 2 Random nam/nữ. Chưa rõ: thuộc tính riêng của 2 Random cha;
target của ActionStop (nằm ngoài bank); âm "DOC" trong QCOMMAND.
