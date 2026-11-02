import os
from PIL import Image, ImageDraw

def optimize():
    assets_dir = os.path.join("frontend", "assets")
    static_dir = os.path.join("frontend", "static")
    os.makedirs(static_dir, exist_ok=True)

    # 1. login_bg.png -> login_bg.jpg
    bg_src = os.path.join(assets_dir, "login_bg.png")
    bg_dst = os.path.join(static_dir, "login_bg.jpg")

    if not os.path.exists(bg_src):
        print(f"Skipping missing source: {bg_src}")
    else:
        with Image.open(bg_src) as img:
            # Resize if width > 1920
            if img.width > 1920:
                h = int(img.height * (1920 / img.width))
                img = img.resize((1920, h), Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Quality 82 first
            quality = 82
            img.save(bg_dst, "JPEG", quality=quality, progressive=True, optimize=True)
            size_kb = os.path.getsize(bg_dst) / 1024
            if size_kb > 450:
                quality = 75
                img.save(bg_dst, "JPEG", quality=quality, progressive=True, optimize=True)
                size_kb = os.path.getsize(bg_dst) / 1024
            
            print(f"Optimized login_bg.jpg: {size_kb:.1f} KB (quality={quality})")

    # 2. logo.png -> logo.png (remove background if opaque corners match)
    logo_src = os.path.join(assets_dir, "logo.png")
    logo_dst = os.path.join(static_dir, "logo.png")

    if not os.path.exists(logo_src):
        print(f"Skipping missing source: {logo_src}")
    else:
        with Image.open(logo_src) as img:
            img = img.convert("RGBA")
            w, h = img.size
            corners = [
                img.getpixel((0, 0)),
                img.getpixel((w - 1, 0)),
                img.getpixel((0, h - 1)),
                img.getpixel((w - 1, h - 1))
            ]

            all_opaque = all(p[3] == 255 for p in corners)
            within_20 = all(
                (max(p[c] for p in corners) - min(p[c] for p in corners) <= 20)
                for c in range(3)
            )

            if all_opaque and within_20:
                for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
                    ImageDraw.floodfill(img, pt, (0, 0, 0, 0), thresh=20)
                
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                
                if img.width > 480:
                    nh = int(img.height * (480 / img.width))
                    img = img.resize((480, nh), Image.Resampling.LANCZOS)
                
                img.save(logo_dst, "PNG", optimize=True)
                size_kb = os.path.getsize(logo_dst) / 1024
                print(f"Optimized logo.png: background removed, {size_kb:.1f} KB (size: {img.size})")
            else:
                if img.width > 480:
                    nh = int(img.height * (480 / img.width))
                    img = img.resize((480, nh), Image.Resampling.LANCZOS)
                img.save(logo_dst, "PNG", optimize=True)
                size_kb = os.path.getsize(logo_dst) / 1024
                print(f"Optimized logo.png: kept as is (corners did not match criteria), {size_kb:.1f} KB")

if __name__ == "__main__":
    optimize()
