"""Regenerate the FIPA protocol diagrams of the E01 paper with larger text.

Same structure as the original draw.io SVGs (UML frame with tab, two agent
boxes, dashed lifelines, activation bars, open arrowheads, slanted branch for
`agree`), but with a narrower canvas and 14 px text so that, placed at half the
text width of the paper, the text renders at roughly 8 pt.
"""
import sys
from pathlib import Path
from PIL import ImageFont
import cairosvg

REG = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheros-regular.otf"
ITA = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheros-italic.otf"

F = 14            # font size (px)
LH = 17           # line height (px)
W = 380           # canvas width (px)
CX1, CX2 = 80, W - 80   # lifeline x of initiator and participant
AW = 16           # activation bar width
BW, BH = 136, 46  # agent box
SLANT = 40        # horizontal run of the slanted branch
FAMILY = "Helvetica, Arial, sans-serif"

f_reg = ImageFont.truetype(REG, F)
f_ita = ImageFont.truetype(ITA, F)


def width(runs):
    """runs: list of (text, italic)."""
    return sum((f_ita if it else f_reg).getlength(t) for t, it in runs)


def text(runs, x, y, anchor="middle"):
    """Emit a text line; position computed here so no renderer anchoring is needed."""
    w = width(runs)
    x0 = x - w / 2 if anchor == "middle" else x
    spans = "".join(
        f'<tspan{" font-style=\"italic\"" if it else ""}>{t}</tspan>' for t, it in runs
    )
    return (f'<text x="{x0:.2f}" y="{y:.2f}" fill="#000000" font-family="{FAMILY}" '
            f'font-size="{F}px" xml:space="preserve">{spans}</text>'), (x0, x0 + w)


def line(x1, y1, x2, y2, dash=False):
    d = ' stroke-dasharray="3 3"' if dash else ""
    return (f'<path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="#000000" '
            f'stroke-miterlimit="10"{d}/>')


def arrow(x_from, x_to, y):
    """Horizontal message with an open arrowhead at x_to."""
    s = 1 if x_to > x_from else -1
    tip = x_to - s * 1
    head = (f'<path d="M {tip - s*7} {y + 3.5} L {tip} {y} L {tip - s*7} {y - 3.5}" '
            f'fill="none" stroke="#000000" stroke-miterlimit="10"/>')
    return line(x_from, y, tip, y) + head


def rect(x, y, w, h):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#ffffff" '
            f'stroke="#000000"/>')


def build(spec):
    out_bg, out_fg, labels = [], [], []
    slant_segments = []

    # Tab with protocol name and type, on two lines.
    l1 = [("Protocol: ", False), (spec["name"], True)]
    l2 = [("Type: " + spec["type"], False)]
    tw = max(width(l1), width(l2)) + 24
    th = 46
    out_fg.append(f'<path d="M 0 0 L {tw:.1f} 0 L {tw:.1f} {th - 12} L {tw - 10:.1f} {th} '
                  f'L 0 {th} Z" fill="#ffffff" stroke="#000000" stroke-miterlimit="10"/>')
    out_fg.append(text(l1, 12, 20, "start")[0])
    out_fg.append(text(l2, 12, 37, "start")[0])

    # Agent boxes.
    by = th + 18
    for cx, (agent, role) in ((CX1, spec["initiator"]), (CX2, spec["participant"])):
        out_fg.append(rect(cx - BW / 2, by, BW, BH))
        out_fg.append(text([(agent, True), (" Agent", False)], cx, by + 20)[0])
        out_fg.append(text([(f"({role})", False)], cx, by + 37)[0])
        labels.append(("agent-box", cx - BW / 2, cx + BW / 2))
    life_top = by + BH

    # Message ys.
    y_req = life_top + 40
    msgs = spec["replies"]
    ys = []
    y = y_req
    prev_lines = spec.get("request_reserve", len(spec["request"][1]))
    for m in msgs:
        n = prev_lines
        gap = 46 if n == 0 else 50 + LH * (n - 1)
        y += gap
        ys.append(y)
        prev_lines = len(m["content"]) if m is not msgs[-1] else len(m["content"])
    y_last = ys[-1]
    final_lines = spec.get("final_reserve", len(msgs[-1]["content"]))
    H = max(y_last + 26 + 14, y_last + 18 + LH * (final_lines - 1) + 14)

    # Outer frame (without the tab edges).
    out_bg.append(f'<path d="M {tw:.1f} 0 L {W} 0 L {W} {H} L 0 {H} L 0 {th}" '
                  f'fill="none" stroke="#000000" stroke-miterlimit="10"/>')

    # Lifelines.
    out_bg.append(line(CX1, life_top, CX1, H - 10, dash=True))
    out_bg.append(line(CX2, life_top, CX2, y_req, dash=True))
    out_bg.append(line(CX2, y_last, CX2, H - 10, dash=True))

    # Activation bars.
    out_fg.append(rect(CX1 - AW / 2, y_req - 26, AW, 26))
    out_fg.append(rect(CX2 - AW / 2, y_req, AW, y_last - y_req))
    for yy in ys:
        out_fg.append(rect(CX1 - AW / 2, yy, AW, 26))

    a_left, a_right = CX1 + AW / 2, CX2 - AW / 2

    # Request.
    perf, content = spec["request"]
    out_fg.append(arrow(a_left, a_right, y_req))
    mid = (a_left + a_right) / 2
    out_fg.append(text([(perf, False)], mid, y_req - 6)[0])
    labels.append(("perf", *text([(perf, False)], mid, y_req - 6)[1]))
    shift = spec.get("request_shift", 0)
    for i, c in enumerate(content):
        t, span = text([(c, False)], mid + shift, y_req + 18 + LH * i)
        out_fg.append(t)
        labels.append((f"content:{c}", *span, y_req + 18 + LH * i))

    # Replies.
    prev_y = None
    for m, yy in zip(msgs, ys):
        if m.get("slant"):
            ys0 = prev_y if prev_y is not None else y_req + 10
            x_end = a_right - SLANT
            out_fg.append(line(a_right, ys0, x_end, yy))
            slant_segments.append((a_right, ys0, x_end, yy))
            out_fg.append(arrow(x_end, a_left, yy))
            m_mid = (a_left + x_end) / 2
        else:
            out_fg.append(arrow(a_right, a_left, yy))
            m_mid = mid
        out_fg.append(text([(m["perf"], False)], m_mid, yy - 6)[0])
        for i, c in enumerate(m["content"]):
            t, span = text([(c, False)], m_mid, yy + 18 + LH * i)
            out_fg.append(t)
            labels.append((f"content:{c}", *span, yy + 18 + LH * i))
        prev_y = yy

    # Sanity checks: labels inside the arrow span and clear of slanted branches.
    problems = []
    for lab in labels:
        if lab[0].startswith("content"):
            name, x0, x1, base = lab
            if x0 < a_left + 4 or x1 > a_right - 4:
                problems.append(f"{name} outside arrow span ({x0:.0f}-{x1:.0f})")
            for (sx0, sy0, sx1, sy1) in slant_segments:
                for yy_ in (base - 10, base + 3):
                    if sy0 <= yy_ <= sy1:
                        xs = sx0 + (sx1 - sx0) * (yy_ - sy0) / (sy1 - sy0)
                        if x1 > xs - 4:
                            problems.append(f"{name} touches slanted branch")
    if tw > W - 20:
        problems.append("tab too wide")

    svg = (f"<?xml version='1.0' encoding='UTF-8'?>\n"
           f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
           f'width="{W + 1}px" height="{H + 1}px" viewBox="0 0 {W + 1} {H + 1}">\n'
           f'<g transform="translate(0.5,0.5)">\n'
           + "\n".join(out_bg) + "\n" + "\n".join(out_fg) +
           "\n</g>\n</svg>\n")
    return svg, problems, (W + 1, H + 1)


REQ, QRY = "FIPA-Request", "FIPA-Query"
AGREE = {"perf": "agree", "content": [], "slant": True}

SPECS = {
    "consulta_de_descenso_en": dict(
        name="Alighting Query", type=QRY,
        initiator=("Bus", "Initiator"), participant=("Passenger", "Participant"),
        request=("query-if", ["(approach query |", "end-of-route query)"]),
        replies=[AGREE, {"perf": "inform-t/f : inform",
                         "content": ["(alighting = true | false)"]}]),
    "diagrama_solicitud_de_descenso_en": dict(
        name="Alighting Request", type=REQ,
        initiator=("Bus", "Initiator"), participant=("Passenger", "Participant"),
        request=("request", ["(alighting request)"]),
        replies=[AGREE, {"perf": "inform-done : inform",
                         "content": ["(alighting confirmation)"]}]),
    "notificacion_de_llegada_en": dict(
        name="Arrival Notification", type=REQ,
        initiator=("Bus", "Initiator"), participant=("Stop", "Participant"),
        request=("request", ["(arrival notice)"]),
        replies=[AGREE, {"perf": "inform-done : inform",
                         "content": ["(passengers notified)"]}]),
    "aviso_de_embarque_en": dict(
        name="Boarding Notice", type=REQ,
        initiator=("Stop", "Initiator"), participant=("Passenger", "Participant"),
        request=("request", ["(bus arrival notice)"]),
        replies=[AGREE, {"perf": "inform-done : inform",
                         "content": ["(receipt confirmation)"]}]),
    "solicitud_de_embarque_en": dict(
        name="Boarding Request", type=REQ,
        initiator=("Passenger", "Initiator"), participant=("Bus", "Participant"),
        request=("request", ["(boarding request)"]),
        replies=[{"perf": "refuse", "content": ["(reasons for refusal)"]},
                 {"perf": "agree", "content": [], "slant": True},
                 {"perf": "inform-done : inform", "content": ["(welcome)"]}]),
    "actualizacion_recuento_en": dict(
        name="Count Update", type=REQ,
        initiator=("Bus", "Initiator"), participant=("Stop", "Participant"),
        request=("request", ["(update content)"]),
        replies=[AGREE, {"perf": "inform-done : inform",
                         "content": ["(content updated)"]}]),
    "consulta_llegada_en": dict(
        name="Post-Arrival Query", type=QRY,
        initiator=("Bus", "Initiator"), participant=("Stop", "Participant"),
        request=("query-ref", ["(stop arrival query)"]),
        replies=[AGREE, {"perf": "inform-result : inform",
                         "content": ["(boarding/alighting", "information)"]}]),
}

# Same vertical layout for every request-agree-inform diagram, so that the
# two diagrams of each figure have the same height.
for k, s in SPECS.items():
    if len(s["replies"]) == 2:
        s["request_reserve"] = 2
        s["final_reserve"] = 2

if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    ok = True
    for name, spec in SPECS.items():
        svg, problems, size = build(spec)
        (out / f"{name}.svg").write_text(svg)
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=str(out / f"{name}.pdf"))
        print(f"{name:38s} {size[0]}x{size[1]}  {'OK' if not problems else problems}")
        ok &= not problems
    sys.exit(0 if ok else 1)
