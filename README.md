# FixLagMCPE — BareBright Lite v2

Bộ tối ưu Minecraft Bedrock/MCPE gồm Resource Pack và Behavior Pack. Mã nguồn build và công cụ tối ưu pack mod nằm trong repo.

## Tính năng bản v2

- Texture khối tự vẽ 16×16, màu sáng hơn và có hoa văn pixel nhỏ.
- Texture mây pixel đơn giản.
- Không dùng shader, custom geometry hoặc Script API.
- Tắt flipbook animation được đăng ký trong Resource Pack.
- 6 âm thanh OGG tự tạo cho đào/đặt đá, đất và gỗ; remap các nhóm block phổ biến.
- Fog tùy chỉnh kéo dài tầm nhìn khi ở trong nước/lava; Behavior Pack áp dụng fog một lần cho mỗi người chơi.
- Behavior Pack không chạy vòng lặp lệnh nặng sau khi đã gắn tag người chơi.

## Tự build Resource Pack + Behavior Pack

Cần Python 3, Pillow, NumPy và FFmpeg có hỗ trợ libvorbis.

```sh
pip install pillow numpy
python tools/build_addon.py
```

Script tạo:
- `dist/FixLagMCPE_BareBright_v2.mcaddon` — gói cài cả hai pack.
- `dist/FixLagMCPE_BareBright_Lite.mcpack` — Resource Pack.
- `dist/FixLagMCPE_Lite_Behavior.mcpack` — Behavior Pack.
- `dist/FixLagMCPE_texture_preview.png` — ảnh xem trước texture.

## Cài đặt

1. Mở file `.mcaddon` bằng Minecraft để import.
2. Trong Edit World, bật **FixLagMCPE | BareBright Lite** ở Resource Packs.
3. Bật **FixLagMCPE | Lite Behavior** ở Behavior Packs.
4. Nếu fog không tự áp dụng, bật Cheats/Commands rồi chạy `/function apply_fog`.
5. Khôi phục fog mặc định bằng `/function remove_fog`.

## Tối ưu Resource Pack của mod khác

```sh
python tools/optimize_mod_pack.py "/sdcard/Download/mod_resource.mcpack" --mcpack
```

Công cụ tạo bản sao, xóa khai báo animation client entity/attachable, xóa thư mục animation không còn tham chiếu, làm rỗng flipbook list, giảm ảnh PNG lớn xuống tối đa 128 px và tăng nhẹ độ sáng ảnh trong `textures/blocks`. Thêm `--remove-particles` để xóa particle folder (có thể làm mất hiệu ứng đặc biệt).

## Giới hạn kỹ thuật

- Resource Pack không thể ép FPS, render distance, độ sáng màn hình hoặc sức mạnh GPU. Tinh chỉnh Video Settings trong game để cân bằng FPS.
- Fog nước/lava được giảm rất mạnh nhưng không biến nước thành kính trong suốt; hiệu quả tùy phiên bản Bedrock.
- Âm thanh custom áp dụng cho các nhóm block phổ biến được remap. Block mod có âm thanh riêng có thể vẫn dùng âm thanh của mod.
- Không thể xóa tất cả tác nhân lag của một mod nếu chưa có file gốc; công cụ tối ưu trên chỉ xử lý phần Resource Pack, không sửa behavior script.
- Texture mây phụ thuộc cách phiên bản game render texture môi trường; không thay đổi màu bầu trời theo biome/thời gian.

## Công cụ

- `tools/build_addon.py`: tạo hai pack và gói `.mcaddon`.
- `tools/optimize_mod_pack.py`: tối ưu Resource Pack của mod khác.
- `tools/strip_animations.py`: tiện ích gỡ khai báo animation client entity/attachable.
