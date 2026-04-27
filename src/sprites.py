"""Pixel sprite SVG generator — 6 characters, 8×12 grid, configurable px size."""

SPRITES = [
    {
        "name": "Blue Knight",
        "pal": {"H": "#3b5bc9", "h": "#4a6fd4", "B": "#5b8dd9", "b": "#3d6bb0",
                "S": "#ffcb8e", "G": "#e6c619", "D": "#192840", ".": None},
        "rows": ["..HHH...", ".HhHHh..", ".HHShH..", ".HHHHH..",
                 "..GGGG..", ".bBBBBb.", "bBBBBBBb", ".bBBBBb.",
                 "..GbbG..", "bB....Bb", "bB....Bb", "DD....DD"],
    },
    {
        "name": "Orange Wizard",
        "pal": {"H": "#d65108", "h": "#f09050", "B": "#f77b35", "b": "#aa3d00",
                "S": "#ffcb8e", "G": "#ffe156", "D": "#2e1500", ".": None},
        "rows": ["...H....", "..HHH...", ".HhHhH..", "HHHHHHHH",
                 "..SSSS..", "..SGSG..", ".BBBBBB.", "bBBBBBBb",
                 ".bBBBBb.", ".BB..BB.", ".Bb..bB.", ".DD..DD."],
    },
    {
        "name": "Green Archer",
        "pal": {"H": "#286b35", "h": "#4ba35a", "B": "#3a8f4a", "b": "#1a4525",
                "S": "#ffcb8e", "G": "#a8d94a", "D": "#0f2e1a", "W": "#6b4226", ".": None},
        "rows": [".HHHHHH.", "HhHHHHhH", ".HSShH..", ".HHHH..W",
                 "..GG...W", ".HBBBBW.", "HBBBBBBW", ".HBBBB..",
                 "..HbbH..", ".HB..BH.", ".HB..BH.", ".DB..BD."],
    },
    {
        "name": "Pink Mage",
        "pal": {"H": "#c9387a", "h": "#e673a8", "B": "#e673a8", "b": "#a01f5c",
                "S": "#ffcb8e", "G": "#9370db", "D": "#3d0025", "W": "#c0a0ff", ".": None},
        "rows": ["..HHH...", ".HhHHh..", ".HSShH..", ".HHHHHG.",
                 "..GGGG..", ".hBBBBh.", "hBBBBBBh", ".hBBBBh.",
                 "..BbbB..", ".hB..Bh.", ".hB..Bh.", ".DD..DD."],
    },
    {
        "name": "Red Warrior",
        "pal": {"H": "#c82020", "h": "#e04040", "B": "#d94040", "b": "#8f0f0f",
                "S": "#ffcb8e", "G": "#c0c0c0", "D": "#2e0000", "W": "#e0e0e0", ".": None},
        "rows": [".HHHHHH.", "HhHHHHhH", ".HSSShH.", ".HHHHH.W",
                 "..GGGG.W", ".bBBBB.W", "bBBBBBBb", ".bBBBBb.",
                 "..bGGb..", ".bB..Bb.", ".bB..Bb.", ".DD..DD."],
    },
    {
        "name": "Teal Rogue",
        "pal": {"H": "#1a7a8f", "h": "#2eaabf", "B": "#2eaabf", "b": "#0f4d5c",
                "S": "#ffcb8e", "G": "#8090a0", "D": "#0a2530", "W": "#d0d0d0", ".": None},
        "rows": [".HHHHHH.", "HhHHHHhH", ".HSShH..", "..HHHH..",
                 ".GGGGGG.", ".bBBBBb.", "bBBBBBBb", ".bBBBBb.",
                 "..bGGb..", "Wb....bW", "Wb....bW", ".DD..DD."],
    },
]


def render_sprite(idx: int, px: int = 4, animate: bool = True) -> str:
    """Return an inline SVG string for sprite `idx` at `px` pixels per cell."""
    s = SPRITES[idx % len(SPRITES)]
    cols = len(s["rows"][0])
    rows = len(s["rows"])
    rects = []
    for r, row in enumerate(s["rows"]):
        for c, ch in enumerate(row):
            color = s["pal"].get(ch)
            if color:
                rects.append(
                    f'<rect x="{c * px}" y="{r * px}" '
                    f'width="{px}" height="{px}" fill="{color}"/>'
                )
    w, h = cols * px, rows * px
    anim_class = "spr-bounce" if animate else ""
    return (
        f'<svg class="sprite-svg {anim_class}" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        + "".join(rects)
        + "</svg>"
    )
