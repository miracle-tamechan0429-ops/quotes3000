#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok『1000年後の名言』 5枚スライド自動生成エンジン (v6.2 バズ特化・極太高視認性モデル)
- 1080×1920px (2倍オーバーサンプリング 2160×3840 描画 → LANCZOS縮小)
- TikTokフォトモード実機表示（3:4領域 Y=240〜1680）に完全最適化
- 【視認性強化 v6.2】：
  * ヒラギノ明朝 W6 に合成ウェイト（stroke_width=2〜3）＋黒縁取り（stroke_width=8）を加え、
    明朝体の細い横線を「極太シネマ明朝（W8相当）」に強化
  * 1行あたりの文字数を13〜16文字以内に厳選し、全スライドのフォントサイズを約1.35〜1.5倍に大型化
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

COLOR_WHITE = (248, 246, 240, 255)        # 高コントラストなシネマホワイト
COLOR_GRAY_WHITE = (232, 230, 224, 255)   # サブテキストも明るく視認性確保
COLOR_GOLD_TOP = (255, 226, 148, 255)     # ハイライトのブライトゴールド
COLOR_GOLD_MID = (235, 178, 72, 255)      # 力強いアンバーゴールド
COLOR_GOLD_BOT = (192, 128, 34, 255)      # 深みのあるブロンズゴールド
COLOR_GOLD_GLOW = (220, 155, 40, 135)
COLOR_RED = (242, 88, 82, 255)            # 視認性の高い鮮烈なシネマレッド


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
    while size > 32:
        font = load_mincho_font(size, bold=bold)
        max_tw = max(
            ((dummy.textbbox((0, 0), line, font=font, stroke_width=2)[2] - dummy.textbbox((0, 0), line, font=font, stroke_width=2)[0]) // SCALE)
            for line in clean_lines
        )
        if max_tw <= max_width_px:
            return font
        size -= 1
    return load_mincho_font(size, bold=bold)


def generate_procedural_scifi_bg(ep_id: str, slide_num: int) -> Image.Image:
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
    brightness_factor = 0.82 if slide_num == 4 else 0.88
    bg = ImageEnhance.Brightness(bg).enhance(brightness_factor)
    bg = ImageEnhance.Contrast(bg).enhance(1.08)

    # 文字の視認性をさらに高めるため、中央テキスト領域の暗幕コントラストを強化
    overlay = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(OUT_H):
        alpha = 0
        if y < 720:
            progress = 1.0 - (y / 720.0)
            alpha = int((progress ** 1.15) * 165)
        if 520 <= y < 1480:
            dist = abs(y - 980) / 480.0
            max_a = 130 if slide_num == 4 else 110
            mid_a = int(max(0.0, 1.0 - (dist ** 1.5)) * max_a)
            alpha = max(alpha, mid_a)
        elif y >= 1480:
            progress = min(1.0, (y - 1480) / 280.0)
            alpha = int(progress * 180)
        if alpha > 0:
            odraw.line([(0, y), (OUT_W, y)], fill=(6, 8, 10, alpha))

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
    bold_stroke: int = 2,
) -> int:
    """
    明朝体の横線の細さを解消するため、bold_stroke (2px @ 2x) で文字自体を太らせ、
    さらに外側に黒のハード縁取り＋ソフトシャドウを重ねてスマホ画面での視認性を極限まで高める。
    """
    if not text:
        return 0
    draw = ImageDraw.Draw(canvas)
    cx = center_x_px * SCALE
    y = y_px * SCALE

    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=bold_stroke)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = cx - tw // 2

    # 1. 広いソフトドロップシャドウ（背景から文字を浮き上がらせる）
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow_layer)
    sdraw.text(
        (x, y + 4 * SCALE),
        text,
        font=font,
        fill=(0, 0, 0, 220),
        stroke_width=bold_stroke + 6 * SCALE,
        stroke_fill=(0, 0, 0, 220),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=7 * SCALE))
    canvas.alpha_composite(shadow_layer)

    # 2. くっきりした黒の外縁取り（明るい背景の上でも文字が絶対に埋もれない）
    draw.text(
        (x, y),
        text,
        font=font,
        fill=(0, 0, 0, 245),
        stroke_width=bold_stroke + 3 * SCALE,
        stroke_fill=(0, 0, 0, 245),
    )

    # 3. 本体描画（stroke_width=bold_stroke で明朝体の横線・縦線を力強く太らせる）
    if is_full_gold:
        _draw_gold_text(canvas, x, y, text, font, bold_stroke=bold_stroke)
    elif gold_substring and gold_substring in text:
        draw.text((x, y), text, font=font, fill=fill, stroke_width=bold_stroke, stroke_fill=fill)
        pre, match, _ = text.partition(gold_substring)
        gold_x = int(x + draw.textlength(pre, font=font))
        _draw_gold_text(canvas, gold_x, y, match, font, bold_stroke=bold_stroke)
    else:
        draw.text((x, y), text, font=font, fill=fill, stroke_width=bold_stroke, stroke_fill=fill)

    return th // SCALE


def _draw_gold_text(
    canvas: Image.Image,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    bold_stroke: int = 2,
) -> None:
    glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)
    gdraw.text(
        (x, y),
        text,
        font=font,
        fill=COLOR_GOLD_GLOW,
        stroke_width=bold_stroke + 2 * SCALE,
        stroke_fill=COLOR_GOLD_GLOW,
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=9 * SCALE))
    canvas.alpha_composite(glow_layer)

    mask = Image.new("L", canvas.size, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.text((x, y), text, font=font, fill=255, stroke_width=bold_stroke, stroke_fill=255)
    bbox = mdraw.textbbox((x, y), text, font=font, stroke_width=bold_stroke)
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
        gpx.line([(bbox[0] - 8, py), (bbox[2] + 8, py)], fill=(r, g, b, 255))

    canvas.paste(grad, (0, 0), mask)


def draw_common_header(canvas: Image.Image, center_x_px: int = 525) -> None:
    font_hdr = load_mincho_font(42, bold=True)
    draw_centered_text_with_shadow(
        canvas, 450, "1000年後に生まれる名言", font_hdr, COLOR_WHITE, center_x_px=center_x_px, bold_stroke=2
    )
    draw = ImageDraw.Draw(canvas)
    line_y = 522 * SCALE
    cx = center_x_px * SCALE
    half_w = 275 * SCALE
    draw.line([(cx - half_w, line_y + 2), (cx + half_w, line_y + 2)], fill=(0, 0, 0, 210), width=4 * SCALE)
    draw.line([(cx - half_w, line_y), (cx + half_w, line_y)], fill=(230, 205, 165, 240), width=3 * SCALE)


def render_episode(episode: dict, out_dir: Path, base_bg_path: Path | None = None, check_guide_path: Path | None = None) -> list[Path]:
    ep_id = episode["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []

    cx = 525
    max_w = 870  # 横幅を870pxまで広く使い、フォントサイズを最大限大きく保つ
    font_badge = load_mincho_font(44, bold=True)
    font_cta = load_mincho_font(44, bold=True)

    # --- Slide 1: Cover Poster (特大68px・極太シネマ明朝) ---
    c1 = prepare_slide_background(base_bg_path, ep_id, 1)
    draw_common_header(c1, cx)
    draw_centered_text_with_shadow(c1, 565, f"【 記録番号：{ep_id} 】", font_badge, COLOR_GRAY_WHITE, center_x_px=cx, bold_stroke=2)

    y = 695
    gold_kw1 = episode["slide1"].get("gold_keyword")
    s1_lines = episode["slide1"]["lines"]
    f_s1 = fit_uniform_font_to_width(s1_lines, 68, max_w, bold=True)
    for line in s1_lines:
        draw_centered_text_with_shadow(
            c1, y, line, f_s1, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw1, bold_stroke=3
        )
        y += 108

    sub_hook = episode["slide1"].get("sub_hook")
    if sub_hook:
        f_sub = fit_uniform_font_to_width([sub_hook], 44, max_w, bold=True)
        draw_centered_text_with_shadow(c1, 1175, sub_hook, f_sub, COLOR_GRAY_WHITE, center_x_px=cx, is_full_gold=True, bold_stroke=2)

    draw_centered_text_with_shadow(c1, 1320, "［ スワイプして記録を見る → ］", font_cta, COLOR_RED, center_x_px=cx, bold_stroke=2)
    p1 = out_dir / "01.png"
    img1 = c1.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB")
    img1.save(p1, quality=98)
    saved_paths.append(p1)

    # --- Slide 2: Shocking Number & Premise (特大56px・極太シネマ明朝) ---
    c2 = prepare_slide_background(base_bg_path, ep_id, 2)
    draw_common_header(c2, cx)
    y = 635
    s2_lines = episode["slide2"]["lines"]
    gold_kw2 = episode["slide2"].get("gold_keyword")
    f_s2 = fit_uniform_font_to_width(s2_lines, 56, max_w, bold=True)
    for idx, line in enumerate(s2_lines):
        draw_centered_text_with_shadow(
            c2, y, line, f_s2, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw2, bold_stroke=2
        )
        y += 155 if idx == len(s2_lines) - 2 else 118
    p2 = out_dir / "02.png"
    img2 = c2.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB")
    img2.save(p2, quality=98)
    saved_paths.append(p2)

    # --- Slide 3: Emotional Mechanism (特大56px・極太シネマ明朝) ---
    c3 = prepare_slide_background(base_bg_path, ep_id, 3)
    draw_common_header(c3, cx)
    y = 635
    s3_lines = episode["slide3"]["lines"]
    gold_kw3 = episode["slide3"].get("gold_keyword")
    f_s3 = fit_uniform_font_to_width(s3_lines, 56, max_w, bold=True)
    for idx, line in enumerate(s3_lines):
        draw_centered_text_with_shadow(
            c3, y, line, f_s3, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw3, bold_stroke=2
        )
        y += 150 if idx == 0 else 118
    p3 = out_dir / "03.png"
    c3.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB").save(p3, quality=98)
    saved_paths.append(p3)

    # --- Slide 4: Climax Golden Quote + Save Trigger (導入50px ＋ 黄金名言70px ＋ 保存誘導42px) ---
    c4 = prepare_slide_background(base_bg_path, ep_id, 4)
    draw_common_header(c4, cx)
    y = 600
    s4_intro = episode["slide4"]["intro_lines"]
    f_intro = fit_uniform_font_to_width(s4_intro, 50, max_w, bold=True)
    for line in s4_intro:
        draw_centered_text_with_shadow(c4, y, line, f_intro, COLOR_GRAY_WHITE, center_x_px=cx, bold_stroke=2)
        y += 94

    y_quote = 975
    s4_quotes = [line.lstrip("　 ").replace("。」", "」") for line in episode["slide4"]["quote_lines"]]
    f_quote = fit_uniform_font_to_width(s4_quotes, 70, 820, bold=True)
    for clean_line in s4_quotes:
        draw_centered_text_with_shadow(
            c4, y_quote, clean_line, f_quote, COLOR_WHITE, center_x_px=cx, is_full_gold=True, bold_stroke=3
        )
        y_quote += 116

    save_note = episode["slide4"].get("save_note", "［ 辛い夜に見返せるよう【保存】してください ］")
    f_save = fit_uniform_font_to_width([save_note], 42, max_w, bold=True)
    draw_centered_text_with_shadow(
        c4, 1320, save_note, f_save, COLOR_WHITE, center_x_px=cx, gold_substring="【保存】", bold_stroke=2
    )

    p4 = out_dir / "04.png"
    img4 = c4.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB")
    img4.save(p4, quality=98)
    saved_paths.append(p4)

    # --- Slide 5: Saveable Prescription + 2-Choice Debate (特大52px・極太シネマ明朝) ---
    c5 = prepare_slide_background(base_bg_path, ep_id, 5)
    draw_common_header(c5, cx)
    badge5 = episode["slide5"].get("badge", "【 今夜のお守り ＆ 究極の2択 】")
    draw_centered_text_with_shadow(c5, 565, badge5, font_badge, COLOR_GRAY_WHITE, center_x_px=cx, bold_stroke=2)
    y = 665
    s5_lines = episode["slide5"]["lines"]
    gold_kw5 = episode["slide5"].get("gold_keyword")
    f_survey = fit_uniform_font_to_width(s5_lines, 52, max_w, bold=True)
    for line in s5_lines:
        if not line.strip():
            y += 38
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
            bold_stroke=2,
        )
        y += 104
    draw_centered_text_with_shadow(c5, 1360, "［ コメント欄で ① か ② を教えて → ］", font_cta, COLOR_RED, center_x_px=cx, bold_stroke=2)
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
    parser = argparse.ArgumentParser(description="1000年後の名言 スライド自動生成ツール (v6.2)")
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
