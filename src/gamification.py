"""XP formula, level tiers, and badge definitions."""
import math
from typing import Any

XP_LEVELS = [
    {"min": 0,     "title": "Lurker",      "color": "#9CA3AF", "emoji": "😴"},
    {"min": 100,   "title": "Newcomer",    "color": "#27500A", "emoji": "🌱"},
    {"min": 300,   "title": "Contributor", "color": "#0C447C", "emoji": "🔧"},
    {"min": 700,   "title": "Regular",     "color": "#633806", "emoji": "⚒️"},
    {"min": 1400,  "title": "Veteran",     "color": "#3C3489", "emoji": "🛡️"},
    {"min": 2500,  "title": "Senior Dev",  "color": "#72243E", "emoji": "🗡️"},
    {"min": 4500,  "title": "Lead",        "color": "#7F77DD", "emoji": "⚔️"},
    {"min": 8000,  "title": "Principal",   "color": "#EF9F27", "emoji": "🏰"},
    {"min": 15000, "title": "Architect",   "color": "#d65108", "emoji": "🔮"},
    {"min": 30000, "title": "Legend",      "color": "#c82020", "emoji": "👑"},
]

BADGE_DEFS = [
    # ── Achievement badges ──
    {"id": "commit_king",    "label": "Commit King",         "icon": "👑", "tier": "legendary"},
    {"id": "line_lord",      "label": "Line Lord",            "icon": "📝", "tier": "epic"},
    {"id": "on_streak",      "label": "On Streak",            "icon": "⚡", "tier": "legendary"},
    {"id": "delete_demon",   "label": "Delete Demon",         "icon": "🔥", "tier": "rare"},
    {"id": "speed_runner",   "label": "Speed Runner",         "icon": "💨", "tier": "common"},
    # ── Activity badges ──
    {"id": "night_owl",      "label": "Night Owl",            "icon": "🦉", "tier": "epic"},
    {"id": "early_bird",     "label": "Early Riser",          "icon": "🐦", "tier": "rare"},
    {"id": "workaholic",     "label": "Workaholic",           "icon": "🪦", "tier": "common"},
    {"id": "ai_whisperer",   "label": "AI Whisperer",         "icon": "🤖", "tier": "epic"},
    {"id": "sober_royalty",  "label": "Sober Royalty",        "icon": "🍻", "tier": "rare"},
    # ── Cursed badges (bad) ──
    {"id": "silent_night",   "label": "Silent Night",         "icon": "🌙", "tier": "cursed"},
    {"id": "doc_dread",      "label": "Documentation Dread",  "icon": "📵", "tier": "cursed"},
    {"id": "lazy_commit",    "label": "Lazy Commit",          "icon": "😬", "tier": "cursed"},
]

TIER_STYLES = {
    "legendary": ("background:#EEEDFE;color:#3C3489",),
    "epic":      ("background:#E6F1FB;color:#0C447C",),
    "rare":      ("background:#FAEEDA;color:#633806",),
    "common":    ("background:#EAF3DE;color:#27500A",),
    "cursed":    ("background:#FBEAF0;color:#72243E",),
}


def compute_xp(m: dict, badge_count: int) -> int:
    return int(
        m.get("total_commits", 0) * 15
        + m.get("lines_added", 0) / 50
        + m.get("lines_deleted", 0) / 150
        + m.get("streak", 0) * 12
        + badge_count * 80
        + m.get("early_commits", 0) * 6
        + m.get("night_commits", 0) * 4
        + m.get("friday_commits", 0) * 3
    )


def get_level(xp: int) -> dict[str, Any]:
    level, idx = XP_LEVELS[0], 0
    for i, tier in enumerate(XP_LEVELS):
        if xp >= tier["min"]:
            level, idx = tier, i
        else:
            break
    nxt = XP_LEVELS[idx + 1] if idx + 1 < len(XP_LEVELS) else None
    progress = int(((xp - level["min"]) / (nxt["min"] - level["min"])) * 100) if nxt else 100
    return {**level, "num": idx + 1, "progress": progress,
            "next_xp": nxt["min"] if nxt else None, "xp": xp}


def badge_pill_html(badge: dict) -> str:
    style = TIER_STYLES.get(badge["tier"], ("",))[0]
    return (
        f'<span style="{style};display:inline-flex;align-items:center;gap:4px;'
        f'font-size:11px;font-weight:500;padding:3px 9px;border-radius:20px;white-space:nowrap">'
        f'{badge["icon"]} {badge["label"]}</span>'
    )
