"""GitHub Leaderboard — Streamlit dashboard."""
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from src.api import (fetch_commit_detail, fetch_commits, fetch_contributor_stats,
                     fetch_contributors, fetch_repo, fetch_tree)
from src.doc_health import SIGNAL_DEFS, get_grade, score as doc_score
from src.gamification import compute_xp, get_level, badge_pill_html
from src.languages import LanguageDetector
from src.badges_page import build as build_badges_page
from src.metrics import assign_badges, compute_contributor_metrics
from src.player_grid import build as build_player_grid
from src.sprites import SPRITES, render_sprite
from src.styles import CSS

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Leaderboard ✦",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELP POPUP (top-left floating — opens by default, ✕ to close)
# Rendered via st.html (not st.markdown) so the markup isn't run through the
# markdown sanitizer that mangles <details>/<input>/<label> tags.
# ─────────────────────────────────────────────────────────────────────────────
HELP_HTML = """
<div class="help-popup">
  <input type="checkbox" id="help-toggle" class="help-toggle-input" checked>
  <label for="help-toggle" class="help-toggle-btn" aria-label="Toggle help"></label>
  <div class="help-card">
    <h4>🎮 What is this?</h4>
    <div class="help-tagline">
      A gamified scoreboard for your GitHub repo. We turn the last 30 days of
      commits into player cards, badges, and XP — so maintenance feels like a
      game instead of a chore.
    </div>
    <div class="help-section">
      <div class="help-row">
        <div class="help-icon">🏛️</div>
        <div class="help-text">
          <div class="help-label">Repo tab</div>
          <div class="help-desc">Size, language mix, doc health grade, and a
          live contributor leaderboard.</div>
        </div>
      </div>
      <div class="help-row">
        <div class="help-icon">🎮</div>
        <div class="help-text">
          <div class="help-label">Players tab</div>
          <div class="help-desc">One card per contributor with XP, level,
          badges, and activity sparkline.</div>
        </div>
      </div>
      <div class="help-row">
        <div class="help-icon">📊</div>
        <div class="help-text">
          <div class="help-label">Doc Health (A–D)</div>
          <div class="help-desc">Scored on README presence, subdir coverage,
          comment density, and config docs. 100 pts total.</div>
        </div>
      </div>
      <div class="help-row">
        <div class="help-icon">⚡</div>
        <div class="help-text">
          <div class="help-label">XP &amp; Levels</div>
          <div class="help-desc">Commits + lines + streak + badges = XP.
          Levels run Lurker → Legend.</div>
        </div>
      </div>
      <div class="help-row">
        <div class="help-icon">🏆</div>
        <div class="help-text">
          <div class="help-label">Badges (good &amp; bad)</div>
          <div class="help-desc">13 auto-awarded badges — achievements,
          activity patterns, and cursed ones you don't want. Click any badge
          on a player card to jump to its full explanation, or open the
          <b>🎖 Badges</b> tab.</div>
        </div>
      </div>
    </div>
  </div>
</div>
"""
# Prefer st.html (Streamlit 1.33+) which renders raw HTML untouched. Fall back
# to st.markdown for older versions.
if hasattr(st, "html"):
    st.html(HELP_HTML)
else:
    st.markdown(HELP_HTML, unsafe_allow_html=True)

DEFAULT_REPO = "ananyashah-cart/Internet-Reliability-Code-Repository"

# Token + repo are sourced exclusively from st.secrets. No UI choice.
try:
    _SECRET_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    _SECRET_REPO  = st.secrets.get("DEFAULT_REPO", DEFAULT_REPO)
except Exception:
    _SECRET_TOKEN, _SECRET_REPO = "", DEFAULT_REPO

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
# CONFIG GATE — no UI choice; repo + token come from st.secrets
# ─────────────────────────────────────────────────────────────────────────────
if not _SECRET_TOKEN:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            '<div style="text-align:center;padding:5rem 0 2rem">'
            '<div style="font-size:2rem;font-weight:500;margin-bottom:.5rem">'
            'github <span style="color:#EF9F27">leaderboard</span> ✦</div>'
            '<div style="color:#6B6B6B;font-size:13px">'
            'Add <code>GITHUB_TOKEN</code> to Streamlit secrets to get started.'
            '</div></div>',
            unsafe_allow_html=True,
        )
    st.stop()

REPO  = _SECRET_REPO
TOKEN = _SECRET_TOKEN

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
try:
    with st.spinner("Fetching repo data…"):
        repo_info    = fetch_repo(REPO, TOKEN)
        tree         = fetch_tree(REPO, TOKEN)
        contributors = fetch_contributors(REPO, TOKEN)
        commits      = fetch_commits(REPO, TOKEN)
        raw_stats    = fetch_contributor_stats(REPO, TOKEN)

    langs_ranked = LanguageDetector().rank(tree)

    # Enrich recent commits with full per-commit detail so metrics can compute:
    #   - lines_added/deleted  (when /stats/contributors is empty)
    #   - comment density per contributor  (for the Documentation Dread badge)
    # Capped at ENRICH_LIMIT to stay well under the 5000/hr GitHub PAT limit.
    if commits:
        ENRICH_LIMIT = 80
        with st.spinner(f"Fetching per-commit detail ({min(len(commits), ENRICH_LIMIT)})…"):
            for c in commits[:ENRICH_LIMIT]:
                if "files" not in c:
                    detail = fetch_commit_detail(REPO, c["sha"], TOKEN)
                    if detail:
                        c["stats"] = detail.get("stats", {})
                        c["files"] = detail.get("files", [])

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
tab_repo, tab_players, tab_badges = st.tabs(["🏛  Repo", "🎮  Players", "🎖  Badges"])

# When a badge in a player card was clicked it set ?tab=badges#badge-<id> on
# the parent. Streamlit's st.tabs has no programmatic-select API, so we inject
# a 0-height iframe whose script reaches into window.parent.document and clicks
# the Badges tab. Same-origin so this is allowed.
if st.query_params.get("tab") == "badges":
    components.html(
        """
        <script>
        (function () {
            const findAndClick = () => {
                const doc  = window.parent.document;
                const tabs = doc.querySelectorAll('[data-baseweb="tab"]');
                for (const t of tabs) {
                    if (t.innerText && t.innerText.indexOf('Badges') !== -1) {
                        t.click();
                        return true;
                    }
                }
                return false;
            };
            // Streamlit may rerender; retry briefly until the tab is in the DOM.
            let tries = 0;
            const id = setInterval(() => {
                if (findAndClick() || ++tries > 20) clearInterval(id);
            }, 100);
        })();
        </script>
        """,
        height=0,
    )

# ═════════════════════════════════════════════════════════════════════════════
# REPO TAB
# ═════════════════════════════════════════════════════════════════════════════
with tab_repo:

    # ── Repo Stats Strip ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Repo Overview</div>', unsafe_allow_html=True)

    lang_pills = "".join(
        f'<span class="lang-pill">{ls.name}</span>' for ls in langs_ranked[:3]
    )
    primary_lang = langs_ranked[0].name if langs_ranked else "—"
    strip = [
        ("Repo size",    f"{repo_info.get('size',0)/1024:.1f} MB",        ""),
        ("Language",     primary_lang,                                     "by file count"),
        ("Top langs",    lang_pills,                                       ""),
        ("Last pushed",  _time_ago(repo_info.get("pushed_at","")),        ""),
        ("Contributors", str(len(contributors)),                           "total"),
    ]
    strip_cols = st.columns(len(strip))
    for col, (lbl, val, sub) in zip(strip_cols, strip):
        col.markdown(_card(lbl, val, sub), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Doc Health (full-width horizontal card) ──────────────────────────────
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
            f'<span style="font-size:11px;width:175px;flex-shrink:0">{sig_label}</span>'
            f'<div class="signal-bar-bg"><div class="signal-bar" '
            f'style="width:{pct}%;background:{bar_color}"></div></div>'
            f'<span style="font-size:10px;color:#6B6B6B;width:46px;text-align:right">'
            f'{earned}/{max_pts}p</span></div>'
        )

    fix_html = ""
    if health["fix_list"] and total < 85:
        items = "".join(
            f'<div style="font-size:11px;color:#6B6B6B;padding:2px 0">{f}</div>'
            for f in health["fix_list"][:6]
        )
        fix_html = (
            f'<div style="font-size:10px;font-weight:500;text-transform:uppercase;'
            f'letter-spacing:.05em;color:#6B6B6B;margin-bottom:5px">Fix List</div>'
            f'{items}'
        )

    st.markdown(
        f'<div class="doc-card" style="display:grid;'
        f'grid-template-columns:160px 1fr 1fr;gap:24px;align-items:start">'
        # Left: grade
        f'<div style="text-align:center">'
        f'<span class="grade-letter" style="color:{color}">{letter}</span>'
        f'<div style="font-size:12px;color:#6B6B6B;font-weight:500;margin-top:6px">'
        f'{total} / 100</div>'
        f'<div style="font-size:10px;color:#6B6B6B">{label}</div>'
        f'</div>'
        # Middle: signal bars
        f'<div>{signals_html}</div>'
        # Right: fix list
        f'<div>{fix_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Top 4 Contributors (same player_grid component as Players tab) ──────
    st.markdown('<div class="section-label">Top Contributors — Last 30 Days</div>',
                unsafe_allow_html=True)
    repo_top_players = sorted(metrics_map.values(), key=lambda m: -m["total_commits"])[:4]
    if repo_top_players:
        repo_grid_html, repo_grid_height = build_player_grid(repo_top_players, badge_map)
        components.html(repo_grid_html, height=repo_grid_height, scrolling=False)


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
    # Rendered as a single embedded HTML grid via components.html — Streamlit's
    # column wrapper would otherwise prevent CSS Grid from equalizing card
    # heights across siblings.
    st.markdown('<div class="section-label">Player Cards</div>', unsafe_allow_html=True)
    grid_html, grid_height = build_player_grid(players_by_xp, badge_map)
    components.html(grid_html, height=grid_height, scrolling=False)


# ═════════════════════════════════════════════════════════════════════════════
# BADGES TAB
# ═════════════════════════════════════════════════════════════════════════════
with tab_badges:
    badges_html, badges_height = build_badges_page()
    components.html(badges_html, height=badges_height, scrolling=True)


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
