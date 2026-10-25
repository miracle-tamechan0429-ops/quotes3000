#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok『1000年後の名言』 5枚スライド自動生成エンジン (v6 バズ特化型)
- 1080×1920px (2倍オーバーサンプリング 2160×3840 描画 → LANCZOS縮小で極限まで鮮明な明朝体)
- TikTokフォトモード実機表示（3:4領域 Y=240〜1680）に完全最適化
- v6 バズ特化マーケティング構造：
  * 1枚目：0.8秒で自分ごと化させる「現代の痛み・逆説フック」＋ 下部サブフック（西暦3000年の実験データ予告）
  * 2枚目：具体的な「数字・異常な実験結果」を金文字強調で提示し、3枚目へ強制スワイプ誘導
  * 3枚目：現代の視聴者の日常と重ね合わせた人間心理の核心解明
  * 4枚目：導入3行 ＋ 特大黄金名言 ＋ 下部「保存（ブックマーク）誘導マイクロコピー」
  * 5枚目：保存率を高める「夜のお守り処方箋」＋ コメント欄の議論を誘発する「① vs ② 究極の2択」
"""

import argparse
import json
import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

WORKSPACE_DIR = Path(__file__).resolve().parent
FONT_TTC_PATH = "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"
FONT_TTC_ALT = "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"

OUT_W, OUT_H = 1080, 1920
SCALE = 2
W, H = OUT_W * SCALE, OUT_H * SCALE

COLOR_WHITE = (242, 239, 233, 255)        # 重厚なウォームアイボリー白
COLOR_GRAY_WHITE = (214, 212, 206, 255)   # 落ち着いた銀灰白
COLOR_GOLD_TOP = (248, 212, 128, 255)     # ハイライトのアンティークゴールド
COLOR_GOLD_MID = (218, 162, 62, 255)      # 重厚なアンバーゴールド
COLOR_GOLD_BOT = (172, 112, 28, 255)      # 深みのあるブロンズゴールド
COLOR_GOLD_GLOW = (210, 145, 35, 110)
COLOR_RED = (224, 78, 72, 255)            # 視線を奪う深紅


def load_mincho_font(size_px: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    idx = 2 if bold else 0
    for path in (FONT_TTC_PATH, FONT_TTC_ALT):
        if os.path.exists(path):
            return ImageFont.truetype(path, size_px * SCALE, index=idx)
    raise FileNotFoundError("ヒラギノ明朝 ProN.ttc が見つかりません")


def fit_uniform_font_to_width(lines: list[str], base_size_px: int, max_width_px: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    size = base_size_px
    clean_lines = [l for l in lines if l.strip()]
    if not clean_lines:
        return load_mincho_font(base_size_px, bold=bold)
    while size > 26:
        font = load_mincho_font(size, bold=bold)
        max_tw = max(((dummy.textbbox((0, 0), line, font=font)[2] - dummy.textbbox((0, 0), line, font=font)[0]) // SCALE) for line in clean_lines)
        if max_tw <= max_width_px:
            return font
        size -= 1
    return load_mincho_font(size, bold=bold)


def generate_procedural_scifi_bg(ep_id: str, slide_num: int) -> Image.Image:
    rng = random.Random(f"{ep_id}_{slide_num}")
    img = Image.new("RGB", (OUT_W, OUT_H), (12, 15, 18))
    glow = Image.new("RGB", (OUT_W, OUT_H), (0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    angle_offsets = {1: 0, 2: 60, 3: -50, 4: 0, 5: 25}
    cx = OUT_W // 2 + angle_offsets.get(slide_num, 0)
    cy = int(OUT_H * 0.30)
    max_r = 720
    for r in range(max_r, 0, -8):
        ratio = 1.0 - (r / max_r)
        val_r = int(42 * (ratio ** 1.6))
        val_g = int(50 * (ratio ** 1.5))
        val_b = int(56 * (ratio ** 1.4))
        gdraw.ellipse((cx - r, cy - int(r * 1.2), cx + r, cy + int(r * 1.2)), fill=(val_r, val_g, val_b))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=18))
    return Image.blend(img, glow, 0.9)


def prepare_slide_background(base_bg_path: Path | None, ep_id: str, slide_num: int) -> Image.Image:
    if base_bg_path and base_bg_path.exists():
        src = Image.open(base_bg_path).convert("RGB")
        sw, sh = src.size
        target_aspect = OUT_W / OUT_H
        if sw / sh > target_aspect:
            new_w = int(sh * target_aspect)
            left = (sw - new_w) // 2
            src = src.crop((left, 0, left + new_w, sh))
        else:
            new_h = int(sw / target_aspect)
            top = (sh - new_h) // 2
            src = src.crop((0, top, sw, top + new_h))

        src = src.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)
        crops = {
            1: (0.00, 0.00, 1.00, 1.00),
            2: (0.05, 0.02, 1.00, 0.97),
            3: (0.00, 0.03, 0.95, 0.98),
            4: (0.06, 0.04, 1.00, 0.92),
            5: (0.00, 0.00, 1.00, 1.00),
        }
        x0, y0, x1, y1 = crops.get(slide_num, (0.0, 0.0, 1.0, 1.0))
        cropped = src.crop((int(OUT_W * x0), int(OUT_H * y0), int(OUT_W * x1), int(OUT_H * y1)))
        bg = cropped.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)
    else:
        bg = generate_procedural_scifi_bg(ep_id, slide_num)

    bg = ImageEnhance.Color(bg).enhance(0.75)
    brightness_factor = 0.86 if slide_num == 4 else 0.94
    bg = ImageEnhance.Brightness(bg).enhance(brightness_factor)
    bg = ImageEnhance.Contrast(bg).enhance(1.08)

    overlay = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(OUT_H):
        alpha = 0
        if y < 720:
            progress = 1.0 - (y / 720.0)
            alpha = int((progress ** 1.15) * 150)
        if 560 <= y < 1460:
            dist = abs(y - 980) / 460.0
            max_a = 105 if slide_num == 4 else 82
            mid_a = int(max(0.0, 1.0 - (dist ** 1.5)) * max_a)
            alpha = max(alpha, mid_a)
        elif y >= 1460:
            progress = min(1.0, (y - 1460) / 300.0)
            alpha = int(progress * 170)
        if alpha > 0:
            odraw.line([(0, y), (OUT_W, y)], fill=(8, 10, 12, alpha))

    bg_rgba = Image.alpha_composite(bg.convert("RGBA"), overlay)
    return bg_rgba.resize((W, H), Image.Resampling.LANCZOS)


def draw_centered_text_with_shadow(
    canvas: Image.Image,
    y_px: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    center_x_px: int = 525,
    gold_substring: str | None = None,
    is_full_gold: bool = False,
) -> int:
    if not text:
        return 0
    draw = ImageDraw.Draw(canvas)
    cx = center_x_px * SCALE
    y = y_px * SCALE

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = cx - tw // 2

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow_layer)
    for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4), (0, 6)]:
        sdraw.text((x + dx * SCALE, y + dy * SCALE), text, font=font, fill=(0, 0, 0, 190))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=6 * SCALE))
    canvas.alpha_composite(shadow_layer)

    for dx, dy in [(-1, 1), (1, 1), (0, 2)]:
        draw.text((x + dx * SCALE, y + dy * SCALE), text, font=font, fill=(0, 0, 0, 215))

    if is_full_gold:
        _draw_gold_text(canvas, x, y, text, font)
    elif gold_substring and gold_substring in text:
        pre, match, post = text.partition(gold_substring)
        cur_x = x
        if pre:
            draw.text((cur_x, y), pre, font=font, fill=fill)
            cur_x += draw.textlength(pre, font=font)
        _draw_gold_text(canvas, int(cur_x), y, match, font)
        cur_x += draw.textlength(match, font=font)
        if post:
            draw.text((int(cur_x), y), post, font=font, fill=fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)

    return th // SCALE


def _draw_gold_text(canvas: Image.Image, x: int, y: int, text: str, font: ImageFont.FreeTypeFont) -> None:
    glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)
    gdraw.text((x, y), text, font=font, fill=COLOR_GOLD_GLOW)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=9 * SCALE))
    canvas.alpha_composite(glow_layer)

    mask = Image.new("L", canvas.size, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.text((x, y), text, font=font, fill=255)
    bbox = mdraw.textbbox((x, y), text, font=font)
    y0, y1 = max(0, bbox[1]), min(canvas.size[1], bbox[3] + 1)

    grad = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gpx = ImageDraw.Draw(grad)
    span = max(1, y1 - y0)
    for py in range(y0, y1):
        t = (py - y0) / span
        if t < 0.5:
            u = t * 2.0
            r = int(COLOR_GOLD_TOP[0] * (1 - u) + COLOR_GOLD_MID[0] * u)
            g = int(COLOR_GOLD_TOP[1] * (1 - u) + COLOR_GOLD_MID[1] * u)
            b = int(COLOR_GOLD_TOP[2] * (1 - u) + COLOR_GOLD_MID[2] * u)
        else:
            u = (t - 0.5) * 2.0
            r = int(COLOR_GOLD_MID[0] * (1 - u) + COLOR_GOLD_BOT[0] * u)
            g = int(COLOR_GOLD_MID[1] * (1 - u) + COLOR_GOLD_BOT[1] * u)
            b = int(COLOR_GOLD_MID[2] * (1 - u) + COLOR_GOLD_BOT[2] * u)
        gpx.line([(bbox[0] - 6, py), (bbox[2] + 6, py)], fill=(r, g, b, 255))

    canvas.paste(grad, (0, 0), mask)


def draw_common_header(canvas: Image.Image, center_x_px: int = 525) -> None:
    font_hdr = load_mincho_font(38, bold=True)
    draw_centered_text_with_shadow(canvas, 455, "1000年後に生まれる名言", font_hdr, COLOR_WHITE, center_x_px=center_x_px)
    draw = ImageDraw.Draw(canvas)
    line_y = 522 * SCALE
    cx = center_x_px * SCALE
    half_w = 260 * SCALE
    draw.line([(cx - half_w, line_y + 2), (cx + half_w, line_y + 2)], fill=(0, 0, 0, 190), width=3 * SCALE)
    draw.line([(cx - half_w, line_y), (cx + half_w, line_y)], fill=(215, 195, 160, 220), width=2 * SCALE)


def render_episode(episode: dict, out_dir: Path, base_bg_path: Path | None = None, check_guide_path: Path | None = None) -> list[Path]:
    ep_id = episode["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []

    cx = 525
    max_w = 820
    font_badge = load_mincho_font(40, bold=True)
    font_sub = load_mincho_font(36, bold=True)
    font_cta = load_mincho_font(38, bold=True)

    # --- Slide 1: Cover Poster (0.8秒で自分ごと化させる現代フック ＋ 西暦3000年の実験データ予告) ---
    c1 = prepare_slide_background(base_bg_path, ep_id, 1)
    draw_common_header(c1, cx)
    draw_centered_text_with_shadow(c1, 575, f"【 記録番号：{ep_id} 】", font_badge, COLOR_GRAY_WHITE, center_x_px=cx)

    y = 720
    gold_kw1 = episode["slide1"].get("gold_keyword")
    s1_lines = episode["slide1"]["lines"]
    f_s1 = fit_uniform_font_to_width(s1_lines, 60, max_w, bold=True)
    for line in s1_lines:
        draw_centered_text_with_shadow(c1, y, line, f_s1, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw1)
        y += 96

    sub_hook = episode["slide1"].get("sub_hook")
    if sub_hook:
        f_sub = fit_uniform_font_to_width([sub_hook], 38, max_w, bold=True)
        draw_centered_text_with_shadow(c1, 1155, sub_hook, f_sub, COLOR_GRAY_WHITE, center_x_px=cx, is_full_gold=True)

    draw_centered_text_with_shadow(c1, 1295, "［ スワイプして記録を見る → ］", font_cta, COLOR_RED, center_x_px=cx)
    p1 = out_dir / "01.png"
    img1 = c1.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB")
    img1.save(p1, quality=98)
    saved_paths.append(p1)

    # --- Slide 2: Shocking Number & Premise (具体的な数字と逆説で引き込む) ---
    c2 = prepare_slide_background(base_bg_path, ep_id, 2)
    draw_common_header(c2, cx)
    y = 665
    s2_lines = episode["slide2"]["lines"]
    gold_kw2 = episode["slide2"].get("gold_keyword")
    f_s2 = fit_uniform_font_to_width(s2_lines, 46, max_w, bold=True)
    for idx, line in enumerate(s2_lines):
        draw_centered_text_with_shadow(c2, y, line, f_s2, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw2)
        y += 172 if idx == len(s2_lines) - 2 else 118
    p2 = out_dir / "02.png"
    img2 = c2.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB")
    img2.save(p2, quality=98)
    saved_paths.append(p2)

    # --- Slide 3: Emotional Mechanism (現代の日常と重なる喪失のメカニズム) ---
    c3 = prepare_slide_background(base_bg_path, ep_id, 3)
    draw_common_header(c3, cx)
    y = 665
    s3_lines = episode["slide3"]["lines"]
    gold_kw3 = episode["slide3"].get("gold_keyword")
    f_s3 = fit_uniform_font_to_width(s3_lines, 46, max_w, bold=True)
    for idx, line in enumerate(s3_lines):
        draw_centered_text_with_shadow(c3, y, line, f_s3, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw3)
        y += 165 if idx == 0 else 118
    p3 = out_dir / "03.png"
    c3.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB").save(p3, quality=98)
    saved_paths.append(p3)

    # --- Slide 4: Climax Golden Quote + Save Trigger ---
    c4 = prepare_slide_background(base_bg_path, ep_id, 4)
    draw_common_header(c4, cx)
    y = 610
    s4_intro = episode["slide4"]["intro_lines"]
    f_intro = fit_uniform_font_to_width(s4_intro, 44, max_w, bold=True)
    for line in s4_intro:
        draw_centered_text_with_shadow(c4, y, line, f_intro, COLOR_GRAY_WHITE, center_x_px=cx)
        y += 84

    y_quote = 985
    s4_quotes = [line.lstrip("　 ").replace("。」", "」") for line in episode["slide4"]["quote_lines"]]
    f_quote = fit_uniform_font_to_width(s4_quotes, 64, 790, bold=True)
    for clean_line in s4_quotes:
        draw_centered_text_with_shadow(c4, y_quote, clean_line, f_quote, COLOR_WHITE, center_x_px=cx, is_full_gold=True)
        y_quote += 108

    save_note = episode["slide4"].get("save_note", "［ 心が折れそうな夜に見返せるよう【保存】してください ］")
    f_save = fit_uniform_font_to_width([save_note], 34, max_w, bold=True)
    draw_centered_text_with_shadow(c4, 1320, save_note, f_save, COLOR_GRAY_WHITE, center_x_px=cx)

    p4 = out_dir / "04.png"
    img4 = c4.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB")
    img4.save(p4, quality=98)
    saved_paths.append(p4)

    # --- Slide 5: Saveable Prescription + 2-Choice Debate ---
    c5 = prepare_slide_background(base_bg_path, ep_id, 5)
    draw_common_header(c5, cx)
    badge5 = episode["slide5"].get("badge", "【 今夜のお守りメモ ＆ 究極の2択 】")
    draw_centered_text_with_shadow(c5, 570, badge5, font_badge, COLOR_GRAY_WHITE, center_x_px=cx)
    y = 675
    s5_lines = episode["slide5"]["lines"]
    gold_kw5 = episode["slide5"].get("gold_keyword")
    f_survey = fit_uniform_font_to_width(s5_lines, 42, max_w, bold=True)
    for line in s5_lines:
        if not line.strip():
            y += 45
            continue
        is_choice = line.startswith("①") or line.startswith("②")
        draw_centered_text_with_shadow(
            c5,
            y,
            line,
            f_survey,
            COLOR_WHITE,
            center_x_px=cx,
            gold_substring=gold_kw5,
            is_full_gold=is_choice,
        )
        y += 96
    draw_centered_text_with_shadow(c5, 1365, "［ コメント欄で①か②を教えてください → ］", font_cta, COLOR_RED, center_x_px=cx)
    p5 = out_dir / "05.png"
    c5.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB").save(p5, quality=98)
    saved_paths.append(p5)

    tk = episode.get("tiktok", {})
    meta_txt = (
        f"■ タイトル\n{tk.get('title', '')}\n\n"
        f"■ キャプション（説明文）\n{tk.get('caption', '')}\n\n"
        f"■ 1コメ目（固定コメント・意識調査）\n{tk.get('comment', '')}\n"
    )
    (out_dir / "caption_and_comment.txt").write_text(meta_txt, encoding="utf-8")

    public_dir = WORKSPACE_DIR / "docs" / "posts" / ep_id
    public_dir.mkdir(parents=True, exist_ok=True)
    for i, png_path in enumerate(saved_paths, start=1):
        im_rgb = Image.open(png_path).convert("RGB")
        jpg_path = out_dir / f"0{i}.jpg"
        im_rgb.save(jpg_path, format="JPEG", quality=96, subsampling=0)
        im_rgb.save(public_dir / f"0{i}.jpg", format="JPEG", quality=96, subsampling=0)
        im_rgb.save(public_dir / f"0{i}_v5.jpg", format="JPEG", quality=96, subsampling=0)

    return saved_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="1000年後の名言 スライド自動生成ツール (v6)")
    parser.add_argument("--id", help="生成する記録番号（例: 008）", default=None)
    parser.add_argument("--all", action="store_true", help="全エピソードを再生成")
    parser.add_argument("--guide", help="ガイド画像パスを重ねた確認画像も出力", default=None)
    args = parser.parse_args()

    episodes_file = WORKSPACE_DIR / "episodes.json"
    episodes = json.loads(episodes_file.read_text(encoding="utf-8"))
    guide_path = Path(args.guide) if args.guide else None

    for ep in episodes:
        ep_id = ep["id"]
        if args.id and ep_id != args.id:
            continue
        if not args.id and not args.all and ep.get("status") == "published":
            continue

        bg_candidate = WORKSPACE_DIR / "backgrounds" / f"{ep_id}_bg.png"
        out_dir = WORKSPACE_DIR / "posts" / f"{ep_id}_{ep['theme']}"
        render_episode(ep, out_dir, bg_candidate if bg_candidate.exists() else None, guide_path)
        print(f"[OK] 【記録番号：{ep_id}】（{ep['theme']}） -> {out_dir}")


if __name__ == "__main__":
    main()
