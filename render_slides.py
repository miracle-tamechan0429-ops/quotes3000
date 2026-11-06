#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok『1000年後の名言』 5枚スライド自動生成エンジン (v8 脱テンプレ・1枚目ダイレクトSF衝撃フック×極限短文型)
- 1080×1920px (2倍オーバーサンプリング 2160×3840 描画 → LANCZOS縮小 + UnsharpMask)
- 【v8 再生数V字回復のための抜本改革】：
  1. 1枚目中央の毎回同じ『1000年後に生まれる名言』固定看板を廃止（既視感による0.2秒スワイプ離脱を根絶）。
     代わりに1枚目中央に「その話固有の衝撃的なSF異常設定（3行・特大70px）」をダイレクトに配置！
  2. アルゴリズム減点＆業者感の原因になっていた赤文字CTA（［スワイプして記録を見る→］［保存してください］［コメント欄で教えて→］）
     および毎回90%台の作られたパーセンテージ数字を完全撤廃。
  3. 2枚目・3枚目を「3〜4行の超短文（62px）」に削ぎ落とし、3枚目で結論をネタバレせず4枚目の名言へ引っ張る構成に刷新。
  4. 5枚目も詰め込み箇条書きを廃止し、余韻のある問いかけ＋①②のシンプルな2択のみに洗練。
"""

import argparse
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

WORKSPACE_DIR = Path(__file__).resolve().parent
FONT_TTC_PATH = "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"
FONT_TTC_ALT = "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"

OUT_W, OUT_H = 1080, 1920
SCALE = 2
W, H = OUT_W * SCALE, OUT_H * SCALE

COLOR_WHITE = (255, 255, 255, 255)
COLOR_GRAY_WHITE = (236, 234, 228, 255)
COLOR_GOLD_TOP = (255, 246, 175, 255)
COLOR_GOLD_MID = (255, 200, 62, 255)
COLOR_GOLD_BOT = (212, 138, 20, 255)


def load_mincho_font(size_px: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    idx = 2 if bold else 0
    for path in (FONT_TTC_PATH, FONT_TTC_ALT):
        if os.path.exists(path):
            return ImageFont.truetype(path, size_px * SCALE, index=idx)
    raise FileNotFoundError("ヒラギノ明朝 ProN.ttc が見つかりません")


def optical_offset_px(text: str, font: ImageFont.FreeTypeFont) -> int:
    """行頭の『「』や行末の『。』『」』による全角空白の視覚的ズレを補正する"""
    if not text:
        return 0
    sample_px = (font.size // SCALE) // 2
    offset = 0
    if text[0] in ("「", "『", "（", "【", "［"):
        offset -= int(sample_px * 0.42)
    if text[-1] in ("」", "』", "）", "】", "］", "。", "、"):
        offset += int(sample_px * 0.42)
    return offset


def fit_uniform_font_to_width(
    lines: list[str], base_size_px: int, max_width_px: int, bold: bool = True, bold_stroke: int = 1
) -> ImageFont.FreeTypeFont:
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    size = base_size_px
    clean_lines = [l for l in lines if l.strip()]
    if not clean_lines:
        return load_mincho_font(base_size_px, bold=bold)
    while size > 32:
        font = load_mincho_font(size, bold=bold)
        max_tw = max(
            (
                (
                    dummy.textbbox((0, 0), line, font=font, stroke_width=bold_stroke)[2]
                    - dummy.textbbox((0, 0), line, font=font, stroke_width=bold_stroke)[0]
                )
                // SCALE
            )
            for line in clean_lines
        )
        if max_tw <= max_width_px:
            return font
        size -= 1
    return load_mincho_font(size, bold=bold)


def generate_procedural_scifi_bg(ep_id: str, slide_num: int) -> Image.Image:
    img = Image.new("RGB", (OUT_W, OUT_H), (12, 15, 20))
    glow = Image.new("RGB", (OUT_W, OUT_H), (0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    angle_offsets = {1: 0, 2: 60, 3: -50, 4: 0, 5: 25}
    cx = OUT_W // 2 + angle_offsets.get(slide_num, 0)
    cy = int(OUT_H * 0.35)
    max_r = 720
    for r in range(max_r, 0, -8):
        ratio = 1.0 - (r / max_r)
        val_r = int(58 * (ratio ** 1.5))
        val_g = int(46 * (ratio ** 1.5))
        val_b = int(38 * (ratio ** 1.4))
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
            2: (0.04, 0.02, 1.00, 0.98),
            3: (0.00, 0.02, 0.96, 0.98),
            4: (0.05, 0.03, 0.95, 0.93),
            5: (0.00, 0.00, 1.00, 1.00),
        }
        x0, y0, x1, y1 = crops.get(slide_num, (0.0, 0.0, 1.0, 1.0))
        cropped = src.crop((int(OUT_W * x0), int(OUT_H * y0), int(OUT_W * x1), int(OUT_H * y1)))
        bg = cropped.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)
    else:
        bg = generate_procedural_scifi_bg(ep_id, slide_num)

    bg = ImageEnhance.Color(bg).enhance(1.05)
    brightness_factor = 0.82 if slide_num == 4 else 0.88
    bg = ImageEnhance.Brightness(bg).enhance(brightness_factor)
    bg = ImageEnhance.Contrast(bg).enhance(1.08)

    overlay = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(OUT_H):
        alpha = 0
        if y < 650:
            progress = 1.0 - (y / 650.0)
            alpha = int((progress ** 1.2) * 140)
        if 500 <= y < 1450:
            dist = abs(y - 940) / 480.0
            max_a = 125 if slide_num in (1, 4) else 110
            mid_a = int(max(0.0, 1.0 - (dist ** 1.4)) * max_a)
            alpha = max(alpha, mid_a)
        elif y >= 1450:
            progress = min(1.0, (y - 1450) / 300.0)
            alpha = int(progress * 175)
        if alpha > 0:
            odraw.line([(0, y), (OUT_W, y)], fill=(6, 8, 12, alpha))

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
    bold_stroke: int = 1,
) -> int:
    if not text:
        return 0
    draw = ImageDraw.Draw(canvas)
    opt_dx = optical_offset_px(text, font)
    cx = (center_x_px + opt_dx) * SCALE
    y = y_px * SCALE

    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=bold_stroke)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = cx - tw // 2

    # 1. タイトで引き締まったドロップシャドウ（滲みゼロ）
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow_layer)
    sdraw.text(
        (x + 3 * SCALE, y + 4 * SCALE),
        text,
        font=font,
        fill=(0, 0, 0, 220),
        stroke_width=bold_stroke + 3 * SCALE,
        stroke_fill=(0, 0, 0, 220),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=1.5 * SCALE))
    canvas.alpha_composite(shadow_layer)

    # 2. 漆黒のソリッド外縁取り
    draw.text(
        (x, y),
        text,
        font=font,
        fill=(0, 0, 0, 255),
        stroke_width=bold_stroke + 4 * SCALE,
        stroke_fill=(0, 0, 0, 255),
    )

    # 3. 本体描画
    if is_full_gold:
        _draw_gold_text(canvas, x, y, text, font, bold_stroke=bold_stroke)
    elif gold_substring and gold_substring in text:
        draw.text((x, y), text, font=font, fill=fill, stroke_width=bold_stroke, stroke_fill=fill)
        pre, match, _ = text.partition(gold_substring)
        _draw_gold_substring(canvas, x, y, pre, match, font, fill=fill, bold_stroke=bold_stroke)
    else:
        draw.text((x, y), text, font=font, fill=fill, stroke_width=bold_stroke, stroke_fill=fill)

    return th // SCALE


def _draw_gold_substring(
    canvas: Image.Image,
    x: int,
    y: int,
    pre: str,
    match: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    bold_stroke: int = 1,
) -> None:
    if not pre:
        _draw_gold_text(canvas, x, y, match, font, bold_stroke=bold_stroke)
        return

    full_sub = pre + match
    mask = Image.new("L", canvas.size, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.text((x, y), full_sub, font=font, fill=255, stroke_width=bold_stroke, stroke_fill=255)
    mdraw.text((x, y), pre, font=font, fill=0, stroke_width=bold_stroke + 1, stroke_fill=0)

    bbox = mdraw.textbbox((x, y), full_sub, font=font, stroke_width=bold_stroke)
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
    draw = ImageDraw.Draw(canvas)
    draw.text((x, y), pre, font=font, fill=fill, stroke_width=bold_stroke, stroke_fill=fill)


def _draw_gold_text(
    canvas: Image.Image,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    bold_stroke: int = 1,
) -> None:
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


def finalize_slide_image(canvas: Image.Image) -> Image.Image:
    img = canvas.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB")
    return img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=115, threshold=2))


def draw_common_header(canvas: Image.Image, ep_id: str, center_x_px: int = 525) -> None:
    font_hdr = load_mincho_font(38, bold=True)
    draw_centered_text_with_shadow(
        canvas, 465, f"1000年後に生まれる名言 ── 記録 {ep_id}", font_hdr, COLOR_GRAY_WHITE, center_x_px=center_x_px, bold_stroke=1
    )
    draw = ImageDraw.Draw(canvas)
    line_y = 532 * SCALE
    cx = center_x_px * SCALE
    half_w = 310 * SCALE
    draw.line([(cx - half_w, line_y + 2), (cx + half_w, line_y + 2)], fill=(0, 0, 0, 235), width=4 * SCALE)
    draw.line([(cx - half_w, line_y), (cx + half_w, line_y)], fill=(242, 208, 145, 255), width=2 * SCALE)


def draw_gold_rule(canvas: Image.Image, y_px: int, half_w_px: int = 360, center_x_px: int = 525) -> None:
    draw = ImageDraw.Draw(canvas)
    ly = y_px * SCALE
    cx = center_x_px * SCALE
    hw = half_w_px * SCALE
    draw.line([(cx - hw, ly + 3), (cx + hw, ly + 3)], fill=(0, 0, 0, 240), width=5 * SCALE)
    draw.line([(cx - hw, ly), (cx + hw, ly)], fill=(248, 210, 125, 255), width=3 * SCALE)


def render_episode(episode: dict, out_dir: Path, base_bg_path: Path | None = None, check_guide_path: Path | None = None) -> list[Path]:
    ep_id = episode["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []

    cx = 525
    max_w = 870

    # =========================================================================
    # Slide 1: 既視感ゼロ！その話固有の「SF衝撃フック（3〜4行・超特大72px）」をど真ん中に配置
    # =========================================================================
    c1 = prepare_slide_background(base_bg_path, ep_id, 1)
    font_top = load_mincho_font(40, bold=True)
    draw_centered_text_with_shadow(
        c1, 495, f"【 記録番号：{ep_id} 】", font_top, COLOR_GRAY_WHITE, center_x_px=cx, bold_stroke=1
    )

    s1_lines = episode["slide1"]["lines"]
    gold_kw1 = episode["slide1"].get("gold_keyword")
    f_s1 = fit_uniform_font_to_width(s1_lines, 72, max_w, bold=True, bold_stroke=2)

    total_lines = len(s1_lines)
    step_y = 132 if total_lines <= 3 else 116
    start_y = 700 if total_lines <= 3 else 650

    draw_gold_rule(c1, start_y - 55, half_w_px=370, center_x_px=cx)
    y = start_y
    for line in s1_lines:
        draw_centered_text_with_shadow(
            c1, y, line, f_s1, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw1, bold_stroke=2
        )
        y += step_y
    draw_gold_rule(c1, y + 20, half_w_px=370, center_x_px=cx)

    font_brand = load_mincho_font(40, bold=True)
    draw_centered_text_with_shadow(
        c1, y + 85, "── 1000年後に生まれる名言 ──", font_brand, COLOR_GRAY_WHITE, center_x_px=cx, is_full_gold=True, bold_stroke=1
    )

    p1 = out_dir / "01.png"
    finalize_slide_image(c1).save(p1, quality=98)
    saved_paths.append(p1)

    # =========================================================================
    # Slide 2: 西暦3000年の異常設定（3〜4行・特大62px・1秒で読める）
    # =========================================================================
    c2 = prepare_slide_background(base_bg_path, ep_id, 2)
    draw_common_header(c2, ep_id, cx)
    s2_lines = episode["slide2"]["lines"]
    gold_kw2 = episode["slide2"].get("gold_keyword")
    f_s2 = fit_uniform_font_to_width(s2_lines, 62, max_w, bold=True, bold_stroke=1)
    y = 700 if len(s2_lines) <= 3 else 660
    step2 = 140 if len(s2_lines) <= 3 else 126
    for line in s2_lines:
        draw_centered_text_with_shadow(
            c2, y, line, f_s2, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw2, bold_stroke=1
        )
        y += step2
    p2 = out_dir / "02.png"
    finalize_slide_image(c2).save(p2, quality=98)
    saved_paths.append(p2)

    # =========================================================================
    # Slide 3: 逆転の異変（ネタバレせず4枚目の名言へ引き込む3〜4行・特大62px）
    # =========================================================================
    c3 = prepare_slide_background(base_bg_path, ep_id, 3)
    draw_common_header(c3, ep_id, cx)
    s3_lines = episode["slide3"]["lines"]
    gold_kw3 = episode["slide3"].get("gold_keyword")
    f_s3 = fit_uniform_font_to_width(s3_lines, 62, max_w, bold=True, bold_stroke=1)
    y = 700 if len(s3_lines) <= 3 else 660
    step3 = 140 if len(s3_lines) <= 3 else 126
    for line in s3_lines:
        draw_centered_text_with_shadow(
            c3, y, line, f_s3, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw3, bold_stroke=1
        )
        y += step3
    p3 = out_dir / "03.png"
    finalize_slide_image(c3).save(p3, quality=98)
    saved_paths.append(p3)

    # =========================================================================
    # Slide 4: 【主役】1000年後に生まれた黄金の名言（超特大74px・宣伝文字ゼロの聖域）
    # =========================================================================
    c4 = prepare_slide_background(base_bg_path, ep_id, 4)
    draw_common_header(c4, ep_id, cx)
    s4_intro = episode["slide4"]["intro_lines"]
    f_intro = fit_uniform_font_to_width(s4_intro, 48, max_w, bold=True, bold_stroke=1)
    y = 640 if len(s4_intro) <= 2 else 610
    for line in s4_intro:
        draw_centered_text_with_shadow(c4, y, line, f_intro, COLOR_GRAY_WHITE, center_x_px=cx, bold_stroke=1)
        y += 92

    rule_top_y = max(865, y + 35)
    draw_gold_rule(c4, rule_top_y, half_w_px=360, center_x_px=cx)
    y_quote = rule_top_y + 45
    s4_quotes = [line.lstrip("　 ").replace("。」", "」") for line in episode["slide4"]["quote_lines"]]
    f_quote = fit_uniform_font_to_width(s4_quotes, 74, 850, bold=True, bold_stroke=2)
    for clean_line in s4_quotes:
        draw_centered_text_with_shadow(
            c4, y_quote, clean_line, f_quote, COLOR_WHITE, center_x_px=cx, is_full_gold=True, bold_stroke=2
        )
        y_quote += 124
    draw_gold_rule(c4, y_quote + 28, half_w_px=360, center_x_px=cx)

    p4 = out_dir / "04.png"
    finalize_slide_image(c4).save(p4, quality=98)
    saved_paths.append(p4)

    # =========================================================================
    # Slide 5: 静かな問いかけ ＆ 究極の2択（業者感ゼロ・4〜5行のみ）
    # =========================================================================
    c5 = prepare_slide_background(base_bg_path, ep_id, 5)
    draw_common_header(c5, ep_id, cx)
    font_badge = load_mincho_font(42, bold=True)
    draw_centered_text_with_shadow(
        c5, 585, "【 西暦3000年・究極の選択 】", font_badge, COLOR_GRAY_WHITE, center_x_px=cx, bold_stroke=1
    )
    y = 695
    s5_lines = episode["slide5"]["lines"]
    f_survey = fit_uniform_font_to_width(s5_lines, 56, max_w, bold=True, bold_stroke=1)
    for line in s5_lines:
        if not line.strip():
            y += 42
            continue
        is_choice = line.startswith("①") or line.startswith("②")
        draw_centered_text_with_shadow(
            c5,
            y,
            line,
            f_survey,
            COLOR_WHITE,
            center_x_px=cx,
            is_full_gold=is_choice,
            bold_stroke=1,
        )
        y += 116
    p5 = out_dir / "05.png"
    finalize_slide_image(c5).save(p5, quality=98)
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
        im_rgb.save(public_dir / f"0{i}_v8.jpg", format="JPEG", quality=96, subsampling=0)

    return saved_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="1000年後の名言 スライド自動生成ツール (v8)")
    parser.add_argument("--id", help="生成する記録番号（例: 018）", default=None)
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
