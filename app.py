"""GitHub Leaderboard — Streamlit dashboard."""
from datetime import datetime

import streamlit as st

from src.api import (fetch_commits, fetch_contributor_stats, fetch_contributors,
                     fetch_languages, fetch_repo)
from src.doc_health import SIGNAL_DEFS, get_grade, score as doc_score
from src.gamification import compute_xp, get_level, badge_pill_html
from src.metrics import assign_badges, compute_contributor_metrics, is_lazy
from src.sprites import SPRITES, render_sprite
from src.styles import CSS

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Leaderboard ✦",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

DEFAULT_REPO = "ananyashah-cart/Internet-Reliability-Code-Repository"

# Pull token/repo from Streamlit secrets if available (deployed app), else fall
# back to whatever the user types in the sidebar (local dev).
try:
    _SECRET_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    _SECRET_REPO  = st.secrets.get("DEFAULT_REPO", DEFAULT_REPO)
except Exception:
    _SECRET_TOKEN, _SECRET_REPO = "", DEFAULT_REPO

# Auto-connect on first load when secrets are present (no PAT gate for visitors).
if _SECRET_TOKEN and not st.session_state.get("ready"):
    st.session_state["repo"]  = _SECRET_REPO
    st.session_state["token"] = _SECRET_TOKEN
    st.session_state["ready"] = True

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _card(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="stat-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="stat-card">'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-value">{value}</div>'
        f'{sub_html}</div>'
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


def _avatar(login: str, size: int = 36) -> str:
    return (
        f'<img src="https://avatars.githubusercontent.com/u/0?u={login}&s={size*2}" '
        f'style="width:{size}px;height:{size}px;border-radius:50%;'
        f'border:.5px solid rgba(0,0,0,.08)" '
        f'onerror="this.src=\'https://ui-avatars.com/api/?name={login}'
        f'&background=E8E4DF&color=6B6B6B&size={size*2}\'">'
    )


def _time_ago(iso: str) -> str:
    try:
        d = (datetime.utcnow() - datetime.fromisoformat(iso.replace("Z", ""))).days
        return "today" if d == 0 else "yesterday" if d == 1 else f"{d}d ago"
    except Exception:
        return "—"


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### ✦ GitHub Leaderboard")
    st.caption("Gamify your repo maintenance")
    st.divider()

    repo_input = st.text_input(
        "Repository", placeholder="owner/repo",
        value=st.session_state.get("repo", _SECRET_REPO),
    )
    token_input = st.text_input(
        "Personal Access Token", type="password",
        placeholder="github_pat_…",
        value=st.session_state.get("token", ""),
    )

    c1, c2 = st.columns(2)
    if c1.button("Connect →", type="primary", use_container_width=True):
        if repo_input and token_input:
            st.session_state["repo"]    = repo_input
            st.session_state["token"]   = token_input
            st.session_state["ready"]   = True
            st.cache_data.clear()
            st.rerun()

    if c2.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("Cache TTL · 5 min")

# ─────────────────────────────────────────────────────────────────────────────
# AUTH GATE
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.get("ready"):
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            '<div style="text-align:center;padding:5rem 0 2rem">'
            '<div style="font-size:2rem;font-weight:500;margin-bottom:.5rem">'
            'github <span style="color:#EF9F27">leaderboard</span> ✦</div>'
            '<div style="color:#6B6B6B;font-size:13px">'
            'Enter your repo and PAT in the sidebar →</div></div>',
            unsafe_allow_html=True,
        )
    st.stop()

REPO  = st.session_state["repo"]
TOKEN = st.session_state["token"]

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
try:
    with st.spinner("Fetching repo data…"):
        repo_info    = fetch_repo(REPO, TOKEN)
        langs        = fetch_languages(REPO, TOKEN)
        contributors = fetch_contributors(REPO, TOKEN)
        commits      = fetch_commits(REPO, TOKEN)
        raw_stats    = fetch_contributor_stats(REPO, TOKEN)

    with st.spinner("Computing metrics…"):
        metrics_map = compute_contributor_metrics(raw_stats, commits)
        badge_map   = assign_badges(metrics_map)

    with st.spinner("Scoring doc health…"):
        health = doc_score(REPO, TOKEN)

except Exception as exc:
    st.error(f"GitHub API error: {exc}")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_repo, tab_players = st.tabs(["🏛  Repo", "🎮  Players"])

# ═════════════════════════════════════════════════════════════════════════════
# REPO TAB
# ═════════════════════════════════════════════════════════════════════════════
with tab_repo:

    # ── Repo Stats Strip ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Repo Overview</div>', unsafe_allow_html=True)

    lang_pills = "".join(
        f'<span class="lang-pill">{l}</span>'
        for l, _ in sorted(langs.items(), key=lambda x: -x[1])[:3]
    )
    strip = [
        ("Repo size",    f"{repo_info.get('size',0)/1024:.1f} MB",        ""),
        ("Language",     repo_info.get("language") or "—",                ""),
        ("Top langs",    lang_pills,                                       ""),
        ("Last pushed",  _time_ago(repo_info.get("pushed_at","")),        ""),
        ("Contributors", str(len(contributors)),                           "total"),
    ]
    strip_cols = st.columns(len(strip))
    for col, (lbl, val, sub) in zip(strip_cols, strip):
        col.markdown(_card(lbl, val, sub), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Doc Health  |  Leaderboard ────────────────────────────────────────────
    left, right = st.columns([1, 2], gap="medium")

    with left:
        st.markdown('<div class="section-label">Doc Health</div>', unsafe_allow_html=True)
        total   = health["total"]
        letter, color, label = get_grade(total)

        signals_html = ""
        for sig_id, icon, sig_label, max_pts in SIGNAL_DEFS:
            earned = health["scores"].get(sig_id, 0)
            pct    = round(earned / max_pts * 100)
            bar_color = "#4ade80" if pct >= 80 else "#fbbf24" if pct >= 50 else "#f87171"
            signals_html += (
                f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">'
                f'<span style="width:16px;text-align:center;font-size:13px">{icon}</span>'
                f'<span style="font-size:11px;width:145px;flex-shrink:0">{sig_label}</span>'
                f'<div class="signal-bar-bg"><div class="signal-bar" '
                f'style="width:{pct}%;background:{bar_color}"></div></div>'
                f'<span style="font-size:10px;color:#6B6B6B;width:42px;text-align:right">'
                f'{earned}/{max_pts}p</span></div>'
            )

        fix_html = ""
        if health["fix_list"] and total < 85:
            items = "".join(
                f'<div style="font-size:11px;color:#6B6B6B;padding:2px 0">{f}</div>'
                for f in health["fix_list"]
            )
            fix_html = (
                f'<div style="margin-top:10px;padding-top:10px;'
                f'border-top:.5px solid rgba(0,0,0,.08)">'
                f'<div style="font-size:10px;font-weight:500;text-transform:uppercase;'
                f'letter-spacing:.05em;color:#6B6B6B;margin-bottom:5px">Fix List</div>'
                f'{items}</div>'
            )

        st.markdown(
            f'<div class="doc-card">'
            f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:12px">'
            f'<div style="text-align:center">'
            f'<span class="grade-letter" style="color:{color}">{letter}</span>'
            f'<div style="font-size:12px;color:#6B6B6B;font-weight:500">{total} / 100</div>'
            f'<div style="font-size:10px;color:#6B6B6B">{label}</div>'
            f'</div></div>'
            f'{signals_html}{fix_html}</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="section-label">Contributor Leaderboard — Last 30 Days</div>',
                    unsafe_allow_html=True)

        sorted_contribs = sorted(metrics_map.values(), key=lambda m: -m["total_commits"])
        card_cols = st.columns(max(min(len(sorted_contribs), 4), 1))

        for i, (col, m) in enumerate(zip(card_cols, sorted_contribs[:4])):
            rank = i + 1
            rank_str = {1: "🥇 #1", 2: "🥈 #2", 3: "🥉 #3"}.get(rank, f"#{rank}")
            badges_html = " ".join(badge_pill_html(b) for b in (badge_map.get(m["login"]) or []))
            top_cls  = "top" if rank == 1 else ""
            gold_cls = "gold" if rank == 1 else ""
            badges_row = (
                f'<div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:6px">{badges_html}</div>'
                if badges_html else ""
            )
            spark = _sparkline(m.get("weekly_commits", []))

            col.markdown(
                f'<div class="contrib-card {top_cls}">'
                f'<div style="display:flex;justify-content:center;height:46px;'
                f'align-items:flex-end;margin-bottom:8px">{render_sprite(i)}</div>'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
                f'{_avatar(m["login"], 28)}'
                f'<div><div style="font-size:13px;font-weight:500">'
                f'<a href="https://github.com/{m["login"]}" target="_blank" '
                f'style="color:#1A1A1A;text-decoration:none">{m["login"]}</a></div>'
                f'<span class="rank-chip {gold_cls}">{rank_str}</span></div></div>'
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:8px">'
                f'<div><div style="font-size:10px;color:#6B6B6B">Commits</div>'
                f'<div style="font-size:15px;font-weight:500">{m["total_commits"]}</div></div>'
                f'<div><div style="font-size:10px;color:#6B6B6B">Lines +</div>'
                f'<div style="font-size:15px;font-weight:500">+{m["lines_added"]:,}</div></div>'
                f'<div><div style="font-size:10px;color:#6B6B6B">Lines −</div>'
                f'<div style="font-size:15px;font-weight:500">-{m["lines_deleted"]:,}</div></div>'
                f'<div><div style="font-size:10px;color:#6B6B6B">Streak</div>'
                f'<div style="font-size:15px;font-weight:500">{m["streak"]}d</div></div>'
                f'</div>'
                f'{badges_row}{spark}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Hall of Shame ─────────────────────────────────────────────────────────
    lazy_counts: dict = {l: 0 for l in metrics_map}
    for c in commits:
        login = (c.get("author") or {}).get("login", "")
        msg   = (c.get("commit") or {}).get("message", "")
        if login in lazy_counts and is_lazy(msg):
            lazy_counts[login] += 1

    lazy_top = sorted(
        [(l, v) for l, v in lazy_counts.items() if v > 0], key=lambda x: -x[1]
    )
    fri_devs = sorted(
        [m for m in metrics_map.values() if m["friday_commits"] >= 3],
        key=lambda m: -m["friday_commits"],
    )

    shame_cards = []
    if lazy_top:
        name, count = lazy_top[0]
        shame_cards.append(
            f'<div class="shame-card"><div style="font-size:18px;margin-bottom:4px">😬</div>'
            f'<div style="font-size:10px;font-weight:500;text-transform:uppercase;'
            f'letter-spacing:.04em;color:#6B6B6B;margin-bottom:3px">Lazy Commit Award</div>'
            f'<div style="font-size:13px;font-weight:500">{name}</div>'
            f'<div style="font-size:11px;color:#6B6B6B;margin-top:3px;line-height:1.5">'
            f'{count} commits like "fix" or "wip". Future you is already suffering.</div></div>'
        )
    for m in fri_devs[:2]:
        shame_cards.append(
            f'<div class="shame-card"><div style="font-size:18px;margin-bottom:4px">💀</div>'
            f'<div style="font-size:10px;font-weight:500;text-transform:uppercase;'
            f'letter-spacing:.04em;color:#6B6B6B;margin-bottom:3px">Friday Deployer</div>'
            f'<div style="font-size:13px;font-weight:500">{m["login"]}</div>'
            f'<div style="font-size:11px;color:#6B6B6B;margin-top:3px;line-height:1.5">'
            f'{m["friday_commits"]} pushes on a Friday. Production is just a vibe.</div></div>'
        )

    if shame_cards:
        st.markdown('<div class="section-label">Hall of Shame</div>', unsafe_allow_html=True)
        shame_cols = st.columns(len(shame_cards))
        for col, html in zip(shame_cols, shame_cards):
            col.markdown(html, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PLAYERS TAB
# ═════════════════════════════════════════════════════════════════════════════
with tab_players:

    players_by_xp = sorted(
        metrics_map.values(),
        key=lambda m: -compute_xp(m, len(badge_map.get(m["login"], []))),
    )

    if not players_by_xp:
        st.info("No contributor data found for the last 30 days.")
        st.stop()

    # ── Player Stats Strip ────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Player Stats</div>', unsafe_allow_html=True)

    total_xp     = sum(compute_xp(m, len(badge_map.get(m["login"], []))) for m in players_by_xp)
    top_m        = players_by_xp[0]
    top_level    = get_level(compute_xp(top_m, len(badge_map.get(top_m["login"], []))))
    top_streak   = max(players_by_xp, key=lambda m: m["streak"])
    top_night    = max(players_by_xp, key=lambda m: m["night_commits"])
    top_early    = max(players_by_xp, key=lambda m: m["early_commits"])
    total_commits = sum(m["total_commits"] for m in players_by_xp)
    total_lines   = sum(m["lines_added"]   for m in players_by_xp)

    p_cols8 = st.columns(8)
    p_strip = [
        ("Team XP",        f"{total_xp:,}",                   "total earned"),
        ("Top Level",      str(top_level["num"]),              top_level["title"]),
        ("Active Players", str(len(players_by_xp)),            "last 30 days"),
        ("Team Commits",   f"{total_commits:,}",               "last 30 days"),
        ("Lines Written",  f"+{total_lines:,}",                "last 30 days"),
        ("Longest Streak", f"{top_streak['streak']}d",         top_streak["login"]),
        ("Night Shift",    top_night["login"],                  f"{top_night['night_commits']} late commits"),
        ("Early Riser",    top_early["login"],                  f"{top_early['early_commits']} before 10am"),
    ]
    for col, (lbl, val, sub) in zip(p_cols8, p_strip):
        col.markdown(_card(lbl, val, sub), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Player Cards ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Player Cards</div>', unsafe_allow_html=True)

    n = min(len(players_by_xp), 4)
    p_card_cols = st.columns(n)

    RANK_CLASS = {1: "g1", 2: "g2", 3: "g3"}
    RANK_EMOJI = {1: "🥇", 2: "🥈", 3: "🥉"}

    for i, (col, m) in enumerate(zip(p_card_cols, players_by_xp[:4])):
        xp     = compute_xp(m, len(badge_map.get(m["login"], [])))
        lvl    = get_level(xp)
        badges = badge_map.get(m["login"], [])
        rank   = i + 1
        power  = round(xp / 10)

        act_parts = []
        if m["night_commits"]:  act_parts.append(f'<span class="act-chip">🦉 {m["night_commits"]} night</span>')
        if m["early_commits"]:  act_parts.append(f'<span class="act-chip">🐦 {m["early_commits"]} early</span>')
        if m["friday_commits"]: act_parts.append(f'<span class="act-chip">😈 {m["friday_commits"]} fri</span>')
        act_html    = " ".join(act_parts)
        badges_html = " ".join(badge_pill_html(b) for b in badges)

        col.markdown(
            f'<div class="player-card {RANK_CLASS.get(rank, "")}">'

            # Power score (top-right absolute)
            f'<div class="power-badge">'
            f'<div class="power-num">{power}</div>'
            f'<div class="power-lbl">power</div></div>'

            # Sprite
            f'<div style="display:flex;justify-content:center;height:60px;'
            f'align-items:flex-end;margin-bottom:10px">'
            f'{render_sprite(i, px=5)}</div>'

            # Identity
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">'
            f'{_avatar(m["login"], 34)}'
            f'<div><div style="font-size:13px;font-weight:500">'
            f'<a href="https://github.com/{m["login"]}" target="_blank" '
            f'style="color:#1A1A1A;text-decoration:none">{m["login"]}</a></div>'
            f'<div style="font-size:11px;color:#6B6B6B">'
            f'{RANK_EMOJI.get(rank, f"#{rank}")} · {lvl["emoji"]} {lvl["title"]}</div>'
            f'</div></div>'

            # Level badge
            f'<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;'
            f'background:#FAF8F5;border-radius:7px;border:.5px solid {lvl["color"]}33;'
            f'margin-bottom:10px">'
            f'<div style="font-size:22px;font-weight:500;color:{lvl["color"]}">LVL {lvl["num"]}</div>'
            f'<div><div style="font-size:12px;font-weight:500;color:{lvl["color"]}">'
            f'{lvl["emoji"]} {lvl["title"]}</div>'
            f'<div style="font-size:10px;color:#6B6B6B">⚡ {xp:,} XP</div></div></div>'

            # XP bar
            f'<div style="margin-bottom:10px">'
            f'<div style="display:flex;justify-content:space-between;'
            f'font-size:10px;color:#6B6B6B;margin-bottom:3px">'
            f'<span>Level {lvl["num"]}</span>'
            f'<span>{lvl["progress"]}% → Level {lvl["num"] + 1}</span></div>'
            f'<div class="xp-track">'
            f'<div class="xp-fill" style="width:{lvl["progress"]}%;background:{lvl["color"]}"></div>'
            f'</div></div>'

            # Mini stats
            f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:8px">'
            f'<div class="mini-stat"><div class="mini-val">{m["total_commits"]}</div><div class="mini-lbl">Commits</div></div>'
            f'<div class="mini-stat"><div class="mini-val">+{m["lines_added"]:,}</div><div class="mini-lbl">Lines +</div></div>'
            f'<div class="mini-stat"><div class="mini-val">-{m["lines_deleted"]:,}</div><div class="mini-lbl">Lines −</div></div>'
            f'<div class="mini-stat"><div class="mini-val">{m["streak"]}d</div><div class="mini-lbl">Streak</div></div>'
            f'</div>'

            # Activity chips
            + (f'<div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:7px">{act_html}</div>' if act_html else "")

            # Badges
            + (f'<div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:7px">{badges_html}</div>' if badges_html else "")

            # Sparkline
            + _sparkline(m.get("weekly_commits", []))

            + "</div>",
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# WANDERING CONTRIBUTOR SPRITES (fixed bottom)
# ─────────────────────────────────────────────────────────────────────────────
players_ranked = sorted(metrics_map.values(), key=lambda m: -m["total_commits"])

WANDER_SLOTS = [
    ("13s", "0s",  "right"),
    ("19s", "5s",  "left"),
    ("15s", "10s", "right"),
    ("21s", "3s",  "left"),
    ("11s", "7s",  "right"),
]

wanderers = ""
for idx, (dur, delay, direction) in enumerate(WANDER_SLOTS):
    if not players_ranked:
        break
    player  = players_ranked[idx % len(players_ranked)]
    sprite  = render_sprite(idx % len(SPRITES), px=4, animate=False)
    cls     = "w-right" if direction == "right" else "w-left"
    wanderers += (
        f'<div class="wanderer {cls}" style="--dur:{dur};--delay:{delay}">'
        f'{sprite}'
        f'<div class="wanderer-name">{player["login"]}</div>'
        f'</div>'
    )

st.markdown(f'<div class="wanderer-bar">{wanderers}</div>', unsafe_allow_html=True)
