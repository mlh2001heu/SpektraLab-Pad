#!/usr/bin/env python3
"""SpektraLab Pad 设计稿渲染（v2）。

生成：
  pad-landscape-main.png   横屏主界面（已载入照片）
  pad-portrait.png         竖屏单列布局
  pad-states.png           空态 / 渲染中 / 导出完成

尺寸按 vivo Pad6 Pro 的 1280x837dp 横屏、1.25 px/dp 绘制。
字体用应用自身的 OPPOSans（GB2312 子集，缺空格与部分符号），
因此这里自绘空格，并避免使用 → ＋ ≥ 等缺字字符。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"F:\spektralab")
OUT = ROOT / "docs" / "design"
OUT.mkdir(parents=True, exist_ok=True)

FONT_CJK = str(ROOT / "build" / "pad-apk" / "assets" / "fonts" / "OPPOSans.ttf")
FONT_LAT = str(ROOT / "build" / "pad-apk" / "assets" / "fonts" / "Inter-Regular.ttf")
REF = Path(r"C:\Users\WINDOWS\.dsh\attachments\v1\objects\8a\8a2133d89758f99f81da21fa1d403c56cb9538f75853862375873e2eed0b67c5")

# ---- 设计令牌 -------------------------------------------------------------
PAPER    = (244, 242, 236)
PAPER_HI = (251, 250, 247)
STAGE    = (17, 22, 75)
INK      = (23, 23, 23)
INK_2    = (112, 109, 102)
INK_3    = (150, 146, 138)
LINE     = (224, 220, 211)
TRACK    = (221, 216, 207)
ACCENT   = (180, 155, 122)
NAVY     = (28, 42, 165)
GREEN    = (0, 122, 61)
RED      = (200, 16, 46)
AMBER    = (242, 195, 0)

S = 1.25


def dp(v):
    return int(round(v * S))


def font(size_dp, latin=False):
    return ImageFont.truetype(FONT_LAT if latin else FONT_CJK, dp(size_dp))


def _spaced_parts(d, s, f):
    parts = s.split(" ")
    space = dp(max(2.0, f.size * 0.26))
    widths = [d.textlength(p, font=f) for p in parts]
    return parts, widths, space


def text(d, xy, s, f, fill=INK, anchor="la"):
    """OPPOSans 缺空格字形，按段绘制并手工插入间距。"""
    parts, widths, space = _spaced_parts(d, s, f)
    total = sum(widths) + space * (len(parts) - 1)
    bb = f.getbbox("国A")
    h = bb[3] - bb[1]
    x, y = xy
    if anchor[0] == "r":
        x -= total
    elif anchor[0] == "m":
        x -= total / 2
    if anchor[1] == "m":
        y -= h / 2 + (bb[1] * 0.0)
    elif anchor[1] == "b":
        y -= h
    cx = x
    for i, (p, w) in enumerate(zip(parts, widths)):
        if i:
            cx += space
        d.text((cx, y), p, font=f, fill=fill, anchor="la")
        cx += w


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def chip(d, xy, label, f, bg, fg=(255, 255, 255), padx=8):
    padx = dp(padx)
    x, y = xy
    tw = _spaced_parts(d, label, f)
    bb = f.getbbox("国A")
    h = dp(22)
    w = sum(tw[1]) + tw[2] * (len(tw[0]) - 1)
    rrect(d, (x, y, x + w + padx * 2, y + h), h // 2, fill=bg)
    text(d, (x + padx, y + h / 2), label, f, fg, anchor="lm")
    return x + w + padx * 2


def icon_undo(d, cx, cy, color=INK, flip=False):
    r = dp(9)
    if flip:
        d.arc((cx - r, cy - r, cx + r - dp(3), cy + r), 20, 250, fill=color, width=dp(2))
        d.polygon([(cx + r - dp(3), cy - r - dp(1)), (cx + r - dp(3), cy - r + dp(7)),
                   (cx + r - dp(11), cy - r + dp(3))], fill=color)
    else:
        d.arc((cx - r + dp(3), cy - r, cx + r, cy + r), -70, 160, fill=color, width=dp(2))
        d.polygon([(cx - r + dp(3), cy - r - dp(1)), (cx - r + dp(3), cy - r + dp(7)),
                   (cx - r + dp(11), cy - r + dp(3))], fill=color)


def icon_export(d, cx, cy, color=INK):
    d.line((cx, cy - dp(8), cx, cy + dp(3)), fill=color, width=dp(2))
    d.polygon([(cx - dp(4), cy), (cx + dp(4), cy), (cx, cy + dp(5))], fill=color)
    d.line((cx - dp(7), cy + dp(8), cx + dp(7), cy + dp(8)), fill=color, width=dp(2))


def icon_more(d, cx, cy, color=INK):
    for dx in (-dp(6), 0, dp(6)):
        d.ellipse((cx + dx - dp(1.4), cy - dp(1.4), cx + dx + dp(1.4), cy + dp(1.4)), fill=color)


def photo(size):
    im = Image.open(REF).convert("RGB").crop((258, 96, 790, 505))
    return im.resize(size, Image.LANCZOS)


def round_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=r, fill=255)
    return m


def slider(d, x, y, w, value, label, val_text):
    text(d, (x, y), label, font(13), INK)
    text(d, (x + w, y), val_text, font(13, True), INK_2, anchor="ra")
    ty = y + dp(28)
    rrect(d, (x, ty, x + w, ty + dp(4)), dp(2), fill=TRACK)
    rrect(d, (x, ty, x + int(w * value), ty + dp(4)), dp(2), fill=ACCENT)
    cx = x + int(w * value)
    d.ellipse((cx - dp(9), ty - dp(6), cx + dp(9), ty + dp(12)), fill=(255, 255, 255),
              outline=(206, 200, 189), width=dp(1))
    d.ellipse((cx - dp(2.6), ty, cx + dp(2.6), ty + dp(6)), fill=ACCENT)
    return ty + dp(30)


def section_row(d, x, y, w, title, detail):
    text(d, (x, y), title, font(13), INK)
    text(d, (x + dp(58), y), detail, font(11), INK_2)
    cx, cy = x + w - dp(8), y + dp(8)
    d.line((cx - dp(4), cy - dp(4), cx, cy), fill=INK_3, width=dp(1.6))
    d.line((cx, cy, cx - dp(4), cy + dp(4)), fill=INK_3, width=dp(1.6))
    d.line((x, y + dp(32), x + w, y + dp(32)), fill=LINE, width=1)
    return y + dp(40)


def preset_card(d, x, y, w, h, name, brand, color, kind, iso, selected=False):
    thumb_h = h
    rrect(d, (x, y, x + w, y + thumb_h), dp(10), fill=color)
    d.polygon([(x, y + thumb_h * 0.66), (x + w, y + thumb_h * 0.40),
               (x + w, y + thumb_h), (x, y + thumb_h)],
              fill=tuple(min(255, c + 26) for c in color))
    text(d, (x + dp(9), y + dp(7)), brand, font(8, True), (255, 255, 255))
    text(d, (x + dp(9), y + thumb_h - dp(18)), iso, font(8, True), (255, 255, 255))
    if selected:
        d.rounded_rectangle((x - dp(3), y - dp(3), x + w + dp(3), y + thumb_h + dp(3)),
                            radius=dp(12), outline=NAVY, width=dp(2))
    text(d, (x, y + thumb_h + dp(8)), name, font(12), INK)
    text(d, (x, y + thumb_h + dp(26)), kind, font(10), INK_2)


def top_bar(d, w, title="SpektraLab Pad", version="1.6.0t-pad.1"):
    rrect(d, (0, 0, w, dp(64)), 0, fill=PAPER_HI)
    d.line((0, dp(64), w, dp(64)), fill=LINE, width=1)
    d.ellipse((dp(20), dp(21), dp(42), dp(43)), outline=INK, width=dp(2))
    d.ellipse((dp(27), dp(28), dp(35), dp(36)), fill=INK)
    text(d, (dp(52), dp(21)), title, font(17), INK)
    text(d, (dp(196), dp(38)), version, font(9, True), INK_3)
    icon_undo(d, w - dp(150), dp(32))
    icon_undo(d, w - dp(114), dp(32), flip=True)
    icon_export(d, w - dp(74), dp(32))
    icon_more(d, w - dp(34), dp(32))


def left_column(d, x, y, w):
    text(d, (x, y), "胶片预设", font(15), INK)
    sy = y + dp(32)
    rrect(d, (x, sy, x + w, sy + dp(32)), dp(8), fill=(232, 228, 219))
    rrect(d, (x + dp(3), sy + dp(3), x + w / 2, sy + dp(29)), dp(6), fill=(255, 255, 255))
    text(d, (x + w / 4, sy + dp(16)), "胶片", font(12), INK, anchor="mm")
    text(d, (x + w * 0.75, sy + dp(16)), "相纸", font(12), INK_2, anchor="mm")

    gap = dp(12)
    cw = (w - gap) / 2
    ch = dp(84)
    items = [
        ("CineStill 800T", "CINESTILL", RED, "彩色负片 / 钨丝灯", "800T"),
        ("Portra 400", "KODAK", (186, 132, 70), "彩色负片 / 人像", "400"),
        ("Velvia 100", "FUJIFILM", (28, 140, 74), "彩色反转 / 风光", "100"),
        ("Acros II", "FUJIFILM", (46, 46, 46), "黑白 / 细颗粒", "100"),
        ("HP5 Plus", "ILFORD", (88, 88, 88), "黑白 / 高感", "400"),
        ("Gold 200", "KODAK", AMBER, "彩色负片 / 日常", "200"),
    ]
    cy = sy + dp(46)
    for i, (name, brand, color, kind, iso) in enumerate(items):
        cx = x + (i % 2) * (cw + gap)
        preset_card(d, cx, cy, cw, ch, name, brand, color, kind, iso, selected=(i == 0))
        if i % 2 == 1:
            cy += ch + dp(56)
    text(d, (x, cy - dp(2)), "全部 34 款胶片 / 相纸", font(11), INK_2)


def right_column(d, x, y, w):
    text(d, (x, y), "调整", font(15), INK)
    text(d, (x + w, y + dp(3)), "重置", font(11), INK_2, anchor="ra")
    cy = y + dp(38)
    cy = slider(d, x, cy, w, 0.55, "曝光", "+0.3")
    cy = slider(d, x, cy, w, 0.36, "颗粒", "36")
    cy = slider(d, x, cy, w, 0.28, "光晕", "28")
    cy = slider(d, x, cy, w, 0.12, "眩光", "12")
    cy += dp(10)
    d.line((x, cy, x + w, cy), fill=LINE, width=1)
    cy += dp(12)
    cy = section_row(d, x, cy, w, "冲印", "Endura Premier")
    cy = section_row(d, x, cy, w, "光学", "标准")
    cy = section_row(d, x, cy, w, "尺度", "135 / 36x24 mm")
    cy = section_row(d, x, cy, w, "构图", "未裁切")
    cy = section_row(d, x, cy, w, "边框", "关闭")
    cy += dp(12)
    rrect(d, (x, cy, x + w, cy + dp(48)), dp(10), fill=NAVY)
    text(d, (x + w / 2, cy + dp(24)), "导出 JPEG", font(14), (255, 255, 255), anchor="mm")
    text(d, (x + w / 2, cy + dp(62)), "长边 3400 / 全尺寸可用", font(10), INK_2, anchor="mm")


def stage_fill(img, box, r):
    """画布底色：中心略亮的深蓝渐变，替单纯的平涂。"""
    w = box[2] - box[0]
    h = box[3] - box[1]
    grad = Image.new("RGB", (w, h))
    g = ImageDraw.Draw(grad)
    c_in = (24, 30, 92)
    c_out = STAGE
    for y in range(h):
        t = abs(y / max(1, h - 1) - 0.5) * 2
        col = tuple(int(c_in[i] + (c_out[i] - c_in[i]) * t) for i in range(3))
        g.line((0, y, w, y), fill=col)
    img.paste(grad, (box[0], box[1]), round_mask((w, h), r))


def landscape():
    W, H = dp(1280), dp(837)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    top_bar(d, W)

    pad = dp(20)
    top = dp(64) + pad
    bottom = H - dp(44) - pad
    left_w, right_w, gap = dp(252), dp(300), dp(20)

    left_column(d, pad, top + dp(4), left_w)
    right_column(d, W - pad - right_w, top + dp(4), right_w)

    cx0 = pad + left_w + gap
    cx1 = W - pad - right_w - gap
    cy0, cy1 = top, bottom
    rrect(d, (cx0, cy0, cx1, cy1), dp(14), fill=STAGE)
    stage_fill(img, (cx0, cy0, cx1, cy1), dp(14))

    inner_w = (cx1 - cx0) - dp(24)
    inner_h = (cy1 - cy0) - dp(24)
    iw = min(inner_w, int(inner_h * 1.42))
    ih = int(iw / 1.42)
    ix = cx0 + ((cx1 - cx0) - iw) // 2
    iy = cy0 + ((cy1 - cy0) - ih) // 2
    img.paste(photo((iw, ih)), (ix, iy), round_mask((iw, ih), dp(10)))

    text(d, ((cx0 + cx1) / 2, cy0 + dp(18)), "DSC_2841.JPG / 4700 x 3133", font(9, True),
         (188, 194, 226), anchor="mm")
    text(d, ((cx0 + cx1) / 2, cy1 - dp(16)), "双指缩放 / 拖动移动", font(9), (150, 158, 196), anchor="mm")
    d.rounded_rectangle((ix - dp(1), iy - dp(1), ix + iw + dp(1), iy + ih + dp(1)),
                        radius=dp(11), outline=(90, 98, 150), width=dp(1))
    chip(d, (ix + dp(12), iy + dp(12)), "CineStill 800T / Endura", font(10), (12, 12, 12))
    chip(d, (ix + dp(12), iy + ih - dp(34)), "100%", font(10), (12, 12, 12))
    ey = iy + ih - dp(34)
    ex = ix + iw - dp(12)
    label = "按住看原图"
    parts, widths, space = _spaced_parts(d, label, font(10))
    tw = sum(widths)
    rrect(d, (ex - tw - dp(20), ey, ex, ey + dp(22)), dp(11), fill=(255, 255, 255))
    text(d, (ex - dp(10), ey + dp(11)), label, font(10), INK, anchor="rm")

    sy = H - dp(38)
    d.line((0, sy - dp(6), W, sy - dp(6)), fill=LINE, width=1)
    text(d, (pad, sy), "4700 x 3133 / 15.9 MP", font(10, True), INK_2, anchor="lm")
    text(d, (W / 2, sy), "渲染 1.2 s / 缓存命中", font(10), INK_2, anchor="mm")
    text(d, (W - pad, sy), "本机上限 16.5 MP / 全尺寸可用", font(10), INK_2, anchor="rm")
    return img


def portrait():
    W, H = dp(720), dp(1120)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    top_bar(d, W)

    pad = dp(16)
    cw = W - pad * 2
    ch = int(cw / 1.42)
    cy = dp(64) + pad
    rrect(d, (pad, cy, pad + cw, cy + ch), dp(14), fill=STAGE)
    inner_w, inner_h = cw - dp(24), ch - dp(24)
    iw = min(inner_w, int(inner_h * 1.42))
    ih = int(iw / 1.42)
    ix = pad + (cw - iw) // 2
    iy = cy + (ch - ih) // 2
    img.paste(photo((iw, ih)), (ix, iy), round_mask((iw, ih), dp(10)))
    chip(d, (ix + dp(10), iy + dp(10)), "CineStill 800T / Endura", font(9), (12, 12, 12))

    sy = cy + ch + dp(20)
    text(d, (pad, sy), "调整", font(15), INK)
    sy += dp(34)
    sy = slider(d, pad, sy, cw, 0.55, "曝光", "+0.3")
    sy = slider(d, pad, sy, cw, 0.36, "颗粒", "36")
    sy = slider(d, pad, sy, cw, 0.28, "光晕", "28")
    sy += dp(6)
    sy = section_row(d, pad, sy, cw, "冲印", "Endura Premier")
    sy = section_row(d, pad, sy, cw, "尺度", "135 / 36x24 mm")

    dy = H - dp(216)
    rrect(d, (0, dy, W, H), dp(18), fill=PAPER_HI)
    d.line((0, dy, W, dy), fill=LINE, width=1)
    rrect(d, (W / 2 - dp(20), dy + dp(8), W / 2 + dp(20), dy + dp(12)), dp(2), fill=(206, 202, 193))
    text(d, (pad, dy + dp(24)), "胶片与相纸", font(13), INK)
    x = pad
    for name, brand, color in [("CineStill 800T", "CINESTILL", RED), ("Portra 400", "KODAK", (186, 132, 70)),
                               ("Velvia 100", "FUJIFILM", (28, 140, 74)), ("Acros II", "FUJIFILM", (46, 46, 46))]:
        cw2, ch2 = dp(118), dp(70)
        rrect(d, (x, dy + dp(52), x + cw2, dy + dp(52) + ch2), dp(10), fill=color)
        text(d, (x + dp(8), dy + dp(58)), brand, font(7, True), (255, 255, 255))
        text(d, (x, dy + dp(52) + ch2 + dp(8)), name, font(10), INK)
        x += cw2 + dp(12)
    return img


def states():
    W, H = dp(1280), dp(300)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    panels = [(dp(230), "空态"), (dp(400), "渲染中"), (dp(280), "导出完成")]
    x = dp(20)
    for pw, title in panels:
        rrect(d, (x, dp(16), x + pw, dp(270)), dp(12), fill=PAPER_HI, outline=LINE)
        text(d, (x + dp(16), dp(30)), title, font(12), INK)
        if title == "空态":
            d.rounded_rectangle((x + dp(24), dp(66), x + pw - dp(24), dp(170)), radius=dp(10),
                                outline=(198, 193, 183), width=dp(2))
            text(d, (x + pw / 2, dp(106)), "+ 导入照片", font(14), INK, anchor="mm")
            text(d, (x + pw / 2, dp(132)), "JPEG / RAW 或从相册选择", font(9), INK_2, anchor="mm")
            text(d, (x + pw / 2, dp(198)), "最近：DSC_2841.JPG", font(9), INK_2, anchor="mm")
        elif title == "渲染中":
            text(d, (x + dp(16), dp(58)), "CineStill 800T / Endura Premier", font(10), INK_2)
            bx0, bx1 = x + dp(16), x + pw - dp(16)
            rrect(d, (bx0, dp(86), bx1, dp(96)), dp(5), fill=TRACK)
            rrect(d, (bx0, dp(86), bx0 + int((bx1 - bx0) * 0.62), dp(96)), dp(5), fill=ACCENT)
            text(d, (bx0, dp(108)), "正在渲染 / 62%", font(10), INK)
            text(d, (bx1, dp(108)), "约 0.8 s", font(10), INK_2, anchor="ra")
            for i, s in enumerate(["取负片", "印相", "打包"]):
                dot = (x + dp(20) + i * dp(64), dp(140))
                d.ellipse((dot[0], dot[1], dot[0] + dp(10), dot[1] + dp(10)),
                          fill=GREEN if i < 2 else TRACK)
                text(d, (dot[0] + dp(14), dot[1] + dp(5)), s, font(9), INK_2, anchor="lm")
            text(d, (x + dp(16), dp(190)), "渲染期间可以继续调参，结束后自动刷新", font(9), INK_3)
        else:
            cxm = x + pw / 2
            d.ellipse((cxm - dp(16), dp(56), cxm + dp(16), dp(88)), fill=GREEN)
            d.line((cxm - dp(7), dp(72), cxm - dp(1), dp(78)), fill=(255, 255, 255), width=dp(2))
            d.line((cxm - dp(1), dp(78), cxm + dp(8), dp(66)), fill=(255, 255, 255), width=dp(2))
            text(d, (cxm, dp(112)), "已导出", font(13), INK, anchor="mm")
            text(d, (cxm, dp(136)), "4700 x 3133 / 4.2 MB", font(9), INK_2, anchor="mm")
            text(d, (cxm, dp(160)), "相册 / Pictures / SpektraLab", font(9), INK_2, anchor="mm")
            text(d, (cxm, dp(196)), "打开 / 继续调整", font(10), NAVY, anchor="mm")
        x += pw + dp(18)
    return img


if __name__ == "__main__":
    landscape().save(OUT / "pad-landscape-main.png", optimize=True)
    portrait().save(OUT / "pad-portrait.png", optimize=True)
    states().save(OUT / "pad-states.png", optimize=True)
    print("written:", *(p.name for p in sorted(OUT.glob("pad-*.png"))))
