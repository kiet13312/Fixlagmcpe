# FixLagMCPE — BareBright + No Animations

Bộ công cụ tối ưu Minecraft Bedrock/MCPE theo hướng nhẹ, sáng và đơn giản.

## Có gì trong repo?

- `dist/FixLagMCPE_BareBright.mcpack`: Resource Pack nhẹ, gồm 13 texture khối tự vẽ ở 16×16 và icon riêng.
- `tools/strip_animations.py`: tạo bản sao Resource Pack của mod và gỡ các khai báo animation ở `minecraft:client_entity` / `minecraft:attachable`.
- `tools/build_pack.py`: tự dựng lại file `.mcpack` từ mã nguồn texture.

## Cài pack BareBright

1. Tải `dist/FixLagMCPE_BareBright.mcpack` về điện thoại.
2. Mở file bằng Minecraft để import.
3. Vào **Settings → Global Resources → My Packs** hoặc bật trong **Edit World → Resource Packs**.
4. Đặt pack này lên trên các resource pack khác nếu muốn texture của nó được ưu tiên.
5. Trong **Video**, tăng **Brightness** lên 100% để màn hình sáng hơn.

## Tắt animation của một mod

Công cụ cần Resource Pack gốc của mod (file `.mcpack` hoặc thư mục đã giải nén). Trên Termux:

```sh
pkg install git python -y
git clone https://github.com/kiet13312/Fixlagmcpe.git
cd Fixlagmcpe
termux-setup-storage
python tools/strip_animations.py "/sdcard/Download/ten_mod.mcpack" --mcpack
```

Hoặc chạy trên máy tính:

```sh
python tools/strip_animations.py "duong_dan/ResourcePackMod.mcpack" --mcpack
```

Công cụ tạo thư mục `*_NoAnimations` và file `.mcpack` tương ứng, không ghi đè pack gốc. Nếu kết quả đã tồn tại, hãy đổi tên/xóa kết quả cũ hoặc dùng `--output`.

## Tùy chỉnh / build lại pack

Cần Python 3, không cần cài thư viện ngoài:

```sh
python tools/build_pack.py
```

File mới sẽ nằm ở `dist/FixLagMCPE_BareBright.mcpack`.

## Giới hạn cần biết

- Pack BareBright dùng texture 16×16 tối giản cho một số khối phổ biến; đây không phải bản sao texture của Bare Bones.
- Resource Pack thông thường không thể ép gamma/độ sáng màn hình của toàn game. Hãy đặt Brightness trong Minecraft lên 100%.
- Tắt animation có thể giảm tải khi mod có nhiều entity/animation, nhưng không đảm bảo FPS tăng trên mọi máy. Công cụ chỉ bỏ khai báo animation ở client entity và attachable; animation được điều khiển bởi script ngoài, behavior pack hoặc định nghĩa đặc biệt khác có thể còn lại.
- Không có shader, hiệu ứng hậu kỳ, model 3D mới hay behavior script trong pack BareBright.
