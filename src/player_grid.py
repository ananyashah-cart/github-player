"""Player Cards section, rendered as a single embedded HTML grid.

Streamlit's st.columns wraps each cell in its own div, so cards in adjacent
columns can't share a flex/grid container and won't auto-equalize height.
This module builds the entire player-card section as one HTML string with
CSS Grid — every card in a row is automatically the same height, no
min-height fudging required.
"""
from src.gamification import badge_pill_html, compute_xp, get_level
from src.sprites import render_sprite

RANK_BORDER = {1: "#EF9F27", 2: "#9CA3AF", 3: "#C97E3B"}
RANK_EMOJI  = {1: "🥇", 2: "🥈", 3: "🥉"}
MAX_BADGES  = 4
PER_ROW     = 4
CARD_HEIGHT = 470     # used for iframe height calc
ROW_GAP     = 14


def _avatar(login: str, size: int = 30) -> str:
    return (
        f'<img src="https://avatars.githubusercontent.com/u/0?u={login}&s={size * 2}" '
        f'style="width:{size}px;height:{size}px;border-radius:50%;'
        f'border:.5px solid rgba(0,0,0,0.08)" '
        f'onerror="this.src=\'https://ui-avatars.com/api/?name={login}'
        f'&background=E8E4DF&color=6B6B6B&size={size * 2}\'">'
    )


def _sparkline(weekly: list, w: int = 90, h: int = 26) -> str:
    vals = [x["c"] for x in (weekly or [])]
    if len(vals) < 2:
        return ""
    mx = max(vals) or 1
    pad = 2
    pts = " ".join(
        f'{pad + (i / (len(vals) - 1)) * (w - 2 * pad):.1f},'
        f'{h - pad - (v / mx) * (h - 2 * pad):.1f}'
        for i, v in enumerate(vals)
    )
    return (
        f'<div class="spark-label">Activity (30d)</div>'
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{pts}" fill="none" stroke="#7F77DD" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


def _card_html(m: dict, rank: int, badges: list, sprite_idx: int) -> str:
    xp     = compute_xp(m, len(badges))
    lvl    = get_level(xp)
    power  = round(xp / 10)
    border = RANK_BORDER.get(rank, "")

    act_parts = []
    if m["night_commits"]:  act_parts.append(f'<span class="act-chip">🦉 {m["night_commits"]} night</span>')
    if m["early_commits"]:  act_parts.append(f'<span class="act-chip">🐦 {m["early_commits"]} early</span>')
    if m["friday_commits"]: act_parts.append(f'<span class="act-chip">😈 {m["friday_commits"]} fri</span>')
    act_html = " ".join(act_parts)

    shown = badges[:MAX_BADGES]
    extra = len(badges) - MAX_BADGES
    badges_html = " ".join(badge_pill_html(b) for b in shown)
    if extra > 0:
        badges_html += (
            f'<span style="font-size:9.5px;color:#6B6B6B;'
            f'padding:1px 6px;align-self:center">+{extra}</span>'
        )

    border_css = f"border:1.5px solid {border};" if border else "border:0.5px solid rgba(0,0,0,0.08);"
    rank_label = RANK_EMOJI.get(rank, f"#{rank}")

    return (
        f'<div class="player-card" style="{border_css}">'
        f'<div class="power-badge">'
        f'<div class="power-num">{power}</div>'
        f'<div class="power-lbl">power</div></div>'

        f'<div class="pc-sprite">{render_sprite(sprite_idx, px=5)}</div>'

        f'<div class="pc-identity">'
        f'{_avatar(m["login"], 30)}'
        f'<div><div class="pc-name">'
        f'<a href="https://github.com/{m["login"]}" target="_blank">{m["login"]}</a></div>'
        f'<div class="pc-sub">{rank_label} · {lvl["emoji"]} {lvl["title"]}</div>'
        f'</div></div>'

        f'<div class="pc-level" style="border:.5px solid {lvl["color"]}33">'
        f'<div class="pc-lvl-num" style="color:{lvl["color"]}">LVL {lvl["num"]}</div>'
        f'<div><div class="pc-lvl-title" style="color:{lvl["color"]}">'
        f'{lvl["emoji"]} {lvl["title"]}</div>'
        f'<div class="pc-xp-total">⚡ {xp:,} XP</div></div></div>'

        f'<div class="pc-xp">'
        f'<div class="pc-xp-row">'
        f'<span>Level {lvl["num"]}</span>'
        f'<span>{lvl["progress"]}% → Level {lvl["num"] + 1}</span></div>'
        f'<div class="xp-track">'
        f'<div class="xp-fill" style="width:{lvl["progress"]}%;background:{lvl["color"]}"></div>'
        f'</div></div>'

        f'<div class="pc-mini">'
        f'<div class="mini-stat"><div class="mini-val">{m["total_commits"]}</div><div class="mini-lbl">Commits</div></div>'
        f'<div class="mini-stat"><div class="mini-val">+{m["lines_added"]:,}</div><div class="mini-lbl">Lines +</div></div>'
        f'<div class="mini-stat"><div class="mini-val">-{m["lines_deleted"]:,}</div><div class="mini-lbl">Lines −</div></div>'
        f'<div class="mini-stat"><div class="mini-val">{m["streak"]}d</div><div class="mini-lbl">Streak</div></div>'
        f'</div>'

        + (f'<div class="pc-chips">{act_html}</div>' if act_html else "")
        + (f'<div class="pc-chips">{badges_html}</div>' if badges_html else "")

        + '<div class="spacer"></div>'
        + _sparkline(m.get("weekly_commits", []))
        + "</div>"
    )


# Inline CSS for the iframe (it doesn't inherit page styles).
_GRID_CSS = """
* { box-sizing: border-box; }
body { margin: 0; padding: 0; background: #FAF8F5;
       font-family: 'Inter', system-ui, sans-serif; color: #1A1A1A; }
.player-grid {
    display: grid;
    grid-template-columns: repeat(""" + str(PER_ROW) + """, 1fr);
    gap: """ + str(ROW_GAP) + """px;
    align-items: stretch;          /* every card in a row = same height */
}
.player-card {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 13px;
    position: relative;
    display: flex; flex-direction: column;
    min-height: """ + str(CARD_HEIGHT) + """px;
}
.player-card .spacer { flex: 1; min-height: 4px; }

.power-badge {
    position: absolute; top: 10px; right: 10px;
    background: #FAF8F5; border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 6px; padding: 3px 7px; text-align: center;
}
.power-num { font-size: 14px; font-weight: 500; line-height: 1; }
.power-lbl { font-size: 9px; color: #6B6B6B; text-transform: uppercase; letter-spacing: 0.04em; }

.pc-sprite   { display:flex; justify-content:center; height:50px;
               align-items:flex-end; margin-bottom:7px; }
.pc-identity { display:flex; align-items:center; gap:7px; margin-bottom:8px; }
.pc-name     { font-size:12.5px; font-weight:500; line-height:1.2; }
.pc-name a   { color: #1A1A1A; text-decoration: none; }
.pc-sub      { font-size:10.5px; color:#6B6B6B; }

.pc-level    { display:flex; align-items:center; gap:7px;
               padding:6px 9px; background:#FAF8F5;
               border-radius:7px; margin-bottom:8px; }
.pc-lvl-num  { font-size:19px; font-weight:500; line-height:1; }
.pc-lvl-title{ font-size:11.5px; font-weight:500; line-height:1.2; }
.pc-xp-total { font-size:10px; color:#6B6B6B; }

.pc-xp       { margin-bottom:8px; }
.pc-xp-row   { display:flex; justify-content:space-between;
               font-size:10px; color:#6B6B6B; margin-bottom:3px; }
.xp-track {
    height: 7px; background: #FAF8F5;
    border-radius: 4px; overflow: hidden;
    border: 0.5px solid rgba(0,0,0,0.06);
}
.xp-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease; }

.pc-mini { display:grid; grid-template-columns:repeat(4,1fr);
           gap:4px; margin-bottom:7px; }
.mini-stat {
    background: #FAF8F5; border-radius: 5px;
    padding: 5px 4px; text-align: center;
}
.mini-val { font-size: 13px; font-weight: 500; line-height: 1.2; }
.mini-lbl { font-size: 9px; color: #6B6B6B; }

.pc-chips { display:flex; flex-wrap:wrap; gap:3px; margin-bottom:6px; }
.act-chip {
    display: inline-block;
    background: #FAF8F5; border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 4px; padding: 1px 6px;
    font-size: 10px; white-space: nowrap;
}

.sprite-svg { image-rendering: pixelated; image-rendering: crisp-edges; }
.spr-bounce { animation: spriteBounce 0.55s ease-in-out infinite; }
@keyframes spriteBounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }

.spark-label { font-size: 10px; color: #6B6B6B; margin-bottom: 2px; }
"""


def build(players: list, badge_map: dict) -> tuple[str, int]:
    """Return (full_html, iframe_height_px) for embedding via components.html."""
    cards = "".join(
        _card_html(m, rank=i + 1, badges=badge_map.get(m["login"], []), sprite_idx=i)
        for i, m in enumerate(players)
    )
    html = (
        f'<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{_GRID_CSS}</style></head><body>'
        f'<div class="player-grid">{cards}</div>'
        f'</body></html>'
    )
    rows = (len(players) + PER_ROW - 1) // PER_ROW
    height = rows * CARD_HEIGHT + (rows - 1) * ROW_GAP + 20   # 20px padding
    return html, height
