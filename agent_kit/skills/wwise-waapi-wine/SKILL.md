---
name: wwise-waapi-wine
description: Dùng MỖI KHI làm việc với Wwise 2019.2 qua WAAPI hoặc Wine trong dự án WoTB: khởi động WAAPI server, tạo/sửa object, set property hoặc reference, patch file .wwu, build bank, hoặc khi thấy WAAPI "báo thành công" mà không rõ có thật không.
---

# wwise-waapi-wine

## Khởi động (chạy tay mỗi phiên, không tự chạy nền)
```bash
source agent_kit/env.sh
wine "$WWISE_CONSOLE" waapi-server "$WPROJ" --allow-migration &
```
Chờ vài giây rồi ping bằng `ak.wwise.core.getInfo`. Không ping được thì DỪNG, đừng viết tiếp code dựa trên giả định server đang chạy.

## Quy tắc
- **Đọc lại sau khi set (R4).** Mọi `setProperty`/`setReference`/`create` phải được đọc lại bằng `ak.wwise.core.object.get` và so với giá trị đã set (số thực so với sai số nhỏ). Không khớp thì raise, không im lặng.
- **Không đoán tên (R5).** Tên property/reference lấy từ `ak.wwise.core.object.getPropertyAndReferenceNames` cho đúng loại object. Phiên bản 2019.2 không có một số hàm WAAPI mới; liệt kê hàm có thật bằng `ak.wwise.waapi.getFunctions` (theo hiểu biết của tôi, hãy xác nhận lại trên bản của bạn).
- **Kết quả `None` hay thiếu trường mong đợi = lỗi.** Không coi là thành công.
- **Patch `.wwu` bằng XML (R7):** giữ nguyên thứ tự element đã verify từ project gốc. Sai thứ tự thì Wwise từ chối load.
- **Giới hạn batch chưa kiểm chứng** (giả định 500 object/lần, `[ASSUMPTION_UNVERIFIED]`). Thử với 100/250/500 object giả và đếm lại số object thật trước khi dựa vào con số này.
- Lưu project sau mỗi nhóm, rồi commit riêng từng nhóm.

## Mẫu hàm set-và-kiểm-tra
```python
def set_and_verify(client, obj_id, prop, value, tol=1e-6):
    client.call("ak.wwise.core.object.setProperty",
                {"object": obj_id, "property": prop, "value": value})
    res = client.call("ak.wwise.core.object.get",
                      {"from": {"id": [obj_id]}, "options": {"return": [prop]}})
    if not res or not res.get("return"):
        raise RuntimeError("không đọc lại được %s.%s" % (obj_id, prop))
    got = res["return"][0].get(prop)
    ok = abs(got - value) <= tol if isinstance(value, (int, float)) else got == value
    if not ok:
        raise RuntimeError("set không có hiệu lực: %s.%s mong %r, thực tế %r" % (obj_id, prop, value, got))
```
(Cú pháp trên là mẫu từ hiểu biết chung về WAAPI, chưa chạy với project của bạn: hãy thử trên một object thật trước khi dùng rộng.)
