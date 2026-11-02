#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok『1000年後の名言』 5枚スライド自動生成エンジン (v7 スターウォーズ世界観 × 1枚目超特大タイトル看板型)
- 1080×1920px (2倍オーバーサンプリング 2160×3840 描画 → LANCZOS縮小)
- TikTokフォトモード実機表示（3:4領域 Y=240〜1680）に完全最適化
- 【v7 大刷新ポイント】：
  1. 1枚目のど真ん中に超特大（86px・極太黄金）で『1000年後に / 生まれる名言』の看板ロゴを配置し、
     0.3秒で「何の企画か」が目に飛び込む圧倒的フックを実現！
     その直下に2行（13〜15文字×2行）の刺さる副題だけを添え、読むストレスゼロで2枚目へ誘導。
  2. 2枚目・3枚目をスターウォーズのオープニング・テロップのように「3〜4行の短文・特大58px」に凝縮。
  3. 4枚目は導入文を3枚目へ移し、壮大なスターウォーズ風背景のど真ん中に「超特大72pxの黄金名言」だけを堂々と配置！
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

COLOR_WHITE = (255, 255, 255, 255)        # パキッとした純白シネマホワイト
COLOR_GRAY_WHITE = (240, 238, 232, 255)   # サブテキスト用の高コントラストシルバーホワイト
COLOR_GOLD_TOP = (255, 246, 175, 255)     # シャープなハイライト・シャンパンゴールド
COLOR_GOLD_MID = (255, 200, 62, 255)      # 力強い純金アンバーゴールド
COLOR_GOLD_BOT = (212, 138, 20, 255)      # 引き締まったディープゴールド
COLOR_RED = (255, 88, 78, 255)            # 視認性の高いシネマレッド


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


def fit_uniform_font_to_width(lines: list[str], base_size_px: int, max_width_px: int, bold: bool = True, bold_stroke: int = 1) -> ImageFont.FreeTypeFont:
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    size = base_size_px
    clean_lines = [l for l in lines if l.strip()]
    if not clean_lines:
        return load_mincho_font(base_size_px, bold=bold)
    while size > 32:
        font = load_mincho_font(size, bold=bold)
        max_tw = max(
            ((dummy.textbbox((0, 0), line, font=font, stroke_width=bold_stroke)[2] - dummy.textbbox((0, 0), line, font=font, stroke_width=bold_stroke)[0]) // SCALE)
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
    """
    スターウォーズ風の壮大な背景（夕陽・星雲・古代神殿の光）の色彩を活かしつつ、
    文字が100%くっきり読めるシネマグラデーションを重ねる。
    """
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

    # スターウォーズ風の黄金の夕陽・星雲の豊かな色彩を残す（彩度を落とさない）
    bg = ImageEnhance.Color(bg).enhance(1.04)
    brightness_factor = 0.84 if slide_num == 4 else 0.90
    bg = ImageEnhance.Brightness(bg).enhance(brightness_factor)
    bg = ImageEnhance.Contrast(bg).enhance(1.08)

    overlay = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(OUT_H):
        alpha = 0
        if y < 680:
            progress = 1.0 - (y / 680.0)
            alpha = int((progress ** 1.2) * 145)
        if 520 <= y < 1480:
            dist = abs(y - 960) / 480.0
            max_a = 120 if slide_num in (1, 4) else 105
            mid_a = int(max(0.0, 1.0 - (dist ** 1.4)) * max_a)
            alpha = max(alpha, mid_a)
        elif y >= 1480:
            progress = min(1.0, (y - 1480) / 280.0)
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

    # 1. タイトで引き締まったドロップシャドウ（滲みゼロ・立体感のみ付与）
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

    # 2. パキッとした漆黒のソリッド外縁取り（ブラーなし・エッジ100%くっきり）
    draw.text(
        (x, y),
        text,
        font=font,
        fill=(0, 0, 0, 255),
        stroke_width=bold_stroke + 4 * SCALE,
        stroke_fill=(0, 0, 0, 255),
    )

    # 3. 本体描画（グロー滲みなし・ベクターエッジそのまま）
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
    """pre + match を同一座標 (x, y) から描画し、pre 領域をマスク除外することでカーニングずれと滲みをゼロにする"""
    if not pre:
        _draw_gold_text(canvas, x, y, match, font, bold_stroke=bold_stroke)
        return

    full_sub = pre + match
    mask = Image.new("L", canvas.size, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.text((x, y), full_sub, font=font, fill=255, stroke_width=bold_stroke, stroke_fill=255)

    # pre のグリフ領域を黒(0)で消去して match のみ残す
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
    # 境界の白文字 pre を再描画してくっきり仕上げる
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
    """2倍キャンバスから1080x1920へLANCZOS縮小後、アンシャープマスクで文字エッジをパキッと際立たせる"""
    img = canvas.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS).convert("RGB")
    return img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=115, threshold=2))


def draw_common_header(canvas: Image.Image, center_x_px: int = 525) -> None:
    font_hdr = load_mincho_font(42, bold=True)
    draw_centered_text_with_shadow(
        canvas, 450, "1000年後に生まれる名言", font_hdr, COLOR_WHITE, center_x_px=center_x_px, bold_stroke=1
    )
    draw = ImageDraw.Draw(canvas)
    line_y = 522 * SCALE
    cx = center_x_px * SCALE
    half_w = 275 * SCALE
    draw.line([(cx - half_w, line_y + 2), (cx + half_w, line_y + 2)], fill=(0, 0, 0, 235), width=4 * SCALE)
    draw.line([(cx - half_w, line_y), (cx + half_w, line_y)], fill=(242, 208, 145, 255), width=3 * SCALE)


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
    font_badge = load_mincho_font(42, bold=True)
    font_cta = load_mincho_font(44, bold=True)

    # =========================================================================
    # Slide 1: 『1000年後に生まれる名言』超特大黄金タイトル看板 ＋ 2行テーマ副題
    # =========================================================================
    c1 = prepare_slide_background(base_bg_path, ep_id, 1)
    draw_centered_text_with_shadow(
        c1, 475, f"【 記録番号：{ep_id} 】", font_badge, COLOR_GRAY_WHITE, center_x_px=cx, bold_stroke=1
    )

    # スターウォーズのタイトルロゴのように、画面中央（Y=560〜865）に超特大黄金タイトルを配置
    draw_gold_rule(c1, 560, half_w_px=370, center_x_px=cx)
    font_hero = load_mincho_font(88, bold=True)
    draw_centered_text_with_shadow(
        c1, 590, "1000年後に", font_hero, COLOR_WHITE, center_x_px=cx, is_full_gold=True, bold_stroke=2
    )
    draw_centered_text_with_shadow(
        c1, 715, "生まれる名言", font_hero, COLOR_WHITE, center_x_px=cx, is_full_gold=True, bold_stroke=2
    )
    draw_gold_rule(c1, 845, half_w_px=370, center_x_px=cx)

    # 直下に0.5秒で読める刺さるテーマ副題（2〜3行・特大58px）
    s1_lines = episode["slide1"].get("cover_hook") or episode["slide1"]["lines"]
    gold_kw1 = episode["slide1"].get("gold_keyword")
    f_s1 = fit_uniform_font_to_width(s1_lines, 58, max_w, bold=True, bold_stroke=1)
    y = 925 if len(s1_lines) <= 2 else 895
    step_y = 108 if len(s1_lines) <= 2 else 94
    for line in s1_lines:
        draw_centered_text_with_shadow(
            c1, y, line, f_s1, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw1, bold_stroke=1
        )
        y += step_y

    sub_hook = episode["slide1"].get("sub_hook")
    if sub_hook:
        f_sub = fit_uniform_font_to_width([sub_hook], 42, max_w, bold=True, bold_stroke=1)
        draw_centered_text_with_shadow(c1, 1185, sub_hook, f_sub, COLOR_GRAY_WHITE, center_x_px=cx, is_full_gold=True, bold_stroke=1)

    draw_centered_text_with_shadow(c1, 1320, "［ スワイプして記録を見る → ］", font_cta, COLOR_RED, center_x_px=cx, bold_stroke=1)
    p1 = out_dir / "01.png"
    img1 = finalize_slide_image(c1)
    img1.save(p1, quality=98)
    saved_paths.append(p1)

    # =========================================================================
    # Slide 2: 未来の記録（短く力強い58px）
    # =========================================================================
    c2 = prepare_slide_background(base_bg_path, ep_id, 2)
    draw_common_header(c2, cx)
    s2_lines = episode["slide2"]["lines"]
    gold_kw2 = episode["slide2"].get("gold_keyword")
    f_s2 = fit_uniform_font_to_width(s2_lines, 58, max_w, bold=True, bold_stroke=1)
    y = 660 if len(s2_lines) <= 4 else 635
    for idx, line in enumerate(s2_lines):
        draw_centered_text_with_shadow(
            c2, y, line, f_s2, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw2, bold_stroke=1
        )
        y += 155 if idx == len(s2_lines) - 2 else 120
    p2 = out_dir / "02.png"
    img2 = finalize_slide_image(c2)
    img2.save(p2, quality=98)
    saved_paths.append(p2)

    # =========================================================================
    # Slide 3: 喪失の理由 ＋ 4枚目の名言へのブリッジ
    # =========================================================================
    c3 = prepare_slide_background(base_bg_path, ep_id, 3)
    draw_common_header(c3, cx)
    s3_lines = episode["slide3"]["lines"]
    gold_kw3 = episode["slide3"].get("gold_keyword")
    f_s3 = fit_uniform_font_to_width(s3_lines, 56, max_w, bold=True, bold_stroke=1)
    y = 640
    for idx, line in enumerate(s3_lines):
        draw_centered_text_with_shadow(
            c3, y, line, f_s3, COLOR_WHITE, center_x_px=cx, gold_substring=gold_kw3, bold_stroke=1
        )
        y += 145 if idx == 0 else 118
    p3 = out_dir / "03.png"
    finalize_slide_image(c3).save(p3, quality=98)
    saved_paths.append(p3)

    # =========================================================================
    # Slide 4: 【主役】1000年後に生まれた黄金の名言（超特大72px）
    # =========================================================================
    c4 = prepare_slide_background(base_bg_path, ep_id, 4)
    draw_common_header(c4, cx)
    y = 600
    s4_intro = episode["slide4"]["intro_lines"]
    f_intro = fit_uniform_font_to_width(s4_intro, 48, max_w, bold=True, bold_stroke=1)
    for line in s4_intro:
        draw_centered_text_with_shadow(c4, y, line, f_intro, COLOR_GRAY_WHITE, center_x_px=cx, bold_stroke=1)
        y += 92

    draw_gold_rule(c4, 925, half_w_px=340, center_x_px=cx)
    y_quote = 965
    s4_quotes = [line.lstrip("　 ").replace("。」", "」") for line in episode["slide4"]["quote_lines"]]
    f_quote = fit_uniform_font_to_width(s4_quotes, 72, 830, bold=True, bold_stroke=2)
    for clean_line in s4_quotes:
        draw_centered_text_with_shadow(
            c4, y_quote, clean_line, f_quote, COLOR_WHITE, center_x_px=cx, is_full_gold=True, bold_stroke=2
        )
        y_quote += 118
    draw_gold_rule(c4, y_quote + 25, half_w_px=340, center_x_px=cx)

    save_note = episode["slide4"].get("save_note", "［ 辛い夜に見返せるよう【保存】してください ］")
    f_save = fit_uniform_font_to_width([save_note], 42, max_w, bold=True, bold_stroke=1)
    draw_centered_text_with_shadow(
        c4, 1325, save_note, f_save, COLOR_WHITE, center_x_px=cx, gold_substring="【保存】", bold_stroke=1
    )

    p4 = out_dir / "04.png"
    img4 = finalize_slide_image(c4)
    img4.save(p4, quality=98)
    saved_paths.append(p4)

    # =========================================================================
    # Slide 5: 保存用お守り ＋ 究極の2択
    # =========================================================================
    c5 = prepare_slide_background(base_bg_path, ep_id, 5)
    draw_common_header(c5, cx)
    badge5 = episode["slide5"].get("badge", "【 今夜のお守り ＆ 究極の2択 】")
    draw_centered_text_with_shadow(c5, 565, badge5, font_badge, COLOR_GRAY_WHITE, center_x_px=cx, bold_stroke=1)
    y = 665
    s5_lines = episode["slide5"]["lines"]
    gold_kw5 = episode["slide5"].get("gold_keyword")
    f_survey = fit_uniform_font_to_width(s5_lines, 52, max_w, bold=True, bold_stroke=1)
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
            bold_stroke=1,
        )
        y += 104
    draw_centered_text_with_shadow(c5, 1360, "［ コメント欄で ① か ② を教えて → ］", font_cta, COLOR_RED, center_x_px=cx, bold_stroke=1)
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

    return saved_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="1000年後の名言 スライド自動生成ツール (v7)")
    parser.add_argument("--id", help="生成する記録番号（例: 010）", default=None)
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
