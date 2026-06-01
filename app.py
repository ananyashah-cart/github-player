"""GitHub Leaderboard — Internet Reliability Repo Dashboard."""
from datetime import datetime, timezone

import streamlit as st
import streamlit.components.v1 as components

from src.api import (fetch_commit_detail, fetch_commits, fetch_contributor_stats,
                     fetch_contributors, fetch_repo, fetch_tree, fetch_workflow_runs)
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
    page_title="IR Repo Dashboard ✦",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELP POPUP
# ─────────────────────────────────────────────────────────────────────────────
HELP_HTML = """
<div class="help-popup">
  <input type="checkbox" id="help-toggle" class="help-toggle-input" checked>
  <label for="help-toggle" class="help-toggle-btn" aria-label="Toggle help"></label>
  <div class="help-card">
    <h4>📡 IR Repo Dashboard</h4>
    <div class="help-tagline">
      Live dashboard for the Internet Reliability SQL repo — doc health,
      domain structure, CI status, and gamified contributor leaderboard.
    </div>
    <div class="help-section">
      <div class="help-row">
        <div class="help-icon">🏛️</div>
        <div class="help-text">
          <div class="help-label">Overview tab</div>
          <div class="help-desc">Repo stats, doc health grade, CI status, top contributors.</div>
        </div>
      </div>
      <div class="help-row">
        <div class="help-icon">🗺️</div>
        <div class="help-text">
          <div class="help-label">Repo Map tab</div>
          <div class="help-desc">FTTP / Access / CPE / Tables domain cards with SQL counts,
          GitHub Actions status, and key doc file checks.</div>
        </div>
      </div>
      <div class="help-row">
        <div class="help-icon">🎮</div>
        <div class="help-text">
          <div class="help-label">Players tab</div>
          <div class="help-desc">XP, level, badges, and activity sparkline per contributor.</div>
        </div>
      </div>
      <div class="help-row">
        <div class="help-icon">⚡</div>
        <div class="help-text">
          <div class="help-label">XP &amp; Levels</div>
          <div class="help-desc">Commits + lines + streak + badges = XP. Levels: Lurker → Legend.</div>
        </div>
      </div>
    </div>
  </div>
</div>
"""
if hasattr(st, "html"):
    st.html(HELP_HTML)
else:
    st.markdown(HELP_HTML, unsafe_allow_html=True)

DEFAULT_REPO = "ananyashah-cart/Internet-Reliability-Code-Repository"

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


def _sparkline(weekly: list, w: int = 90, h: int = 26, color: str = "#60A5FA") -> str:
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
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


def _avatar(login: str, size: int = 36) -> str:
    return (
        f'<img src="https://avatars.githubusercontent.com/u/0?u={login}&s={size*2}" '
        f'style="width:{size}px;height:{size}px;border-radius:50%;'
        f'border:1px solid rgba(0,0,0,0.08)" '
        f'onerror="this.src=\'https://ui-avatars.com/api/?name={login}'
        f'&background=E8E4DF&color=6B6B6B&size={size*2}\'">'
    )


def _time_ago(iso: str) -> str:
    try:
        d = (datetime.now(timezone.utc) -
             datetime.fromisoformat(iso.replace("Z", "+00:00"))).days
        return "today" if d == 0 else "yesterday" if d == 1 else f"{d}d ago"
    except Exception:
        return "—"


def _ci_status_html(runs: list) -> str:
    """Render CI workflow status badges."""
    # Map known workflow names to friendly labels
    WORKFLOW_LABELS = {
        "Lint New Files":         ("🔒", "Lint New Files",      "blocks bad commits"),
        "Refresh SQL Index":      ("📇", "SQL Index Refresh",   "runs on every SQL push"),
        "Monthly Cleanup Audit":  ("🧹", "Monthly Cleanup",     "opens issues for violations"),
    }
    if not runs:
        return '<div style="font-size:12px;color:#9CA3AF;padding:8px 0">No workflow runs found yet — push a commit to trigger.</div>'

    badges = ""
    for run in runs:
        name       = run.get("name", "Workflow")
        conclusion = run.get("conclusion") or run.get("status", "unknown")
        updated    = _time_ago(run.get("updated_at", ""))

        dot_cls = {
            "success": "success", "failure": "failure",
            "in_progress": "pending", "queued": "pending",
        }.get(conclusion, "unknown")

        icon, friendly, desc = WORKFLOW_LABELS.get(name, ("⚙️", name, ""))
        status_label = {"success": "Passed", "failure": "Failed",
                        "in_progress": "Running", "queued": "Queued"}.get(conclusion, conclusion.title())

        badges += (
            f'<div class="ci-badge">'
            f'<div class="ci-dot {dot_cls}"></div>'
            f'<div style="flex:1">'
            f'<div class="ci-name">{icon} {friendly}</div>'
            f'<div class="ci-time">{desc}</div>'
            f'</div>'
            f'<div style="text-align:right">'
            f'<div style="font-size:11px;font-weight:600;color:{"#059669" if dot_cls=="success" else "#EF4444" if dot_cls=="failure" else "#D97706"}">'
            f'{status_label}</div>'
            f'<div class="ci-time">{updated}</div>'
            f'</div></div>'
        )
    return f'<div class="ci-strip">{badges}</div>'


DOMAIN_DEFS = [
    {
        "key": "FTTP",
        "cls": "fttp",
        "icon": "📡",
        "name": "FTTP",
        "desc": "Fiber-to-the-Premises analytics — TC, SSB, RC metrics, ONU Pareto, service interruption investigations",
        "tags": ["TC", "SSB", "RC", "Pareto", "ONU", "Optical"],
        "owner": "Ananya Shah",
    },
    {
        "key": "Access",
        "cls": "access",
        "icon": "🔗",
        "name": "Access",
        "desc": "HSD access network — DAA Pareto, RPD vendor (Vecima vs Harmonic), OS upgrades, Speed Master",
        "tags": ["DAA", "RPD", "Speed", "OS Upgrade", "Pareto"],
        "owner": "Ananya Shah",
    },
    {
        "key": "CPE",
        "cls": "cpe",
        "icon": "📦",
        "name": "CPE",
        "desc": "Customer Premises Equipment — modem swaps, CPE Quality reports, competitive speed benchmarking",
        "tags": ["Swaps", "PyAthena", "Benchmarking", "Weekly", "Monthly"],
        "owner": "Ananya Shah",
    },
    {
        "key": "Tables",
        "cls": "tables",
        "icon": "🗄️",
        "name": "Tables",
        "desc": "Data source reference — schema docs, sample queries, first-10-rows for every table used in the repo",
        "tags": ["QOS_INSIGHTS", "IPDR", "Attenuation", "Work Orders"],
        "owner": "Team",
    },
]

KEY_DOCS = [
    ("CLAUDE.md",       "📐", "Canonical rules & SQL patterns"),
    ("ONBOARDING.md",   "🚀", "GitHub + Cursor setup guide"),
    ("Access.md",       "🔑", "Redshift & Athena connection guide"),
    ("README.md",       "🗺️",  "Repo map & contribution rules"),
    (".gitignore",      "🚫", "Blocks binary files from git"),
]

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG GATE
# ─────────────────────────────────────────────────────────────────────────────
if not _SECRET_TOKEN:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            '<div style="text-align:center;padding:5rem 0 2rem">'
            '<div style="font-size:2rem;font-weight:700;margin-bottom:.5rem">'
            '📡 IR <span style="color:#2563EB">Repo</span> Dashboard</div>'
            '<div style="color:#9CA3AF;font-size:13px">'
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
        workflow_runs = fetch_workflow_runs(REPO, TOKEN)

    langs_ranked = LanguageDetector().rank(tree)

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

# ── Domain SQL file counts from the tree ──────────────────────────────────────
def _sql_count(prefix: str) -> int:
    return sum(
        1 for f in tree
        if f["path"].startswith(prefix + "/") and f["path"].lower().endswith(".sql")
    )

domain_counts = {
    "FTTP":   _sql_count("FTTP"),
    "Access": _sql_count("Access"),
    "CPE":    _sql_count("CPE"),
    "Tables": sum(1 for f in tree if f["path"].startswith("Tables/") and f["path"].endswith(".md") and "README" not in f["path"]),
}

# ── Key doc presence check ────────────────────────────────────────────────────
root_filenames = {f["path"].lower() for f in tree if "/" not in f["path"]}

# ─────────────────────────────────────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────────────────────────────────────
total_sql = sum(domain_counts[d] for d in ["FTTP", "Access", "CPE"])
last_push = _time_ago(repo_info.get("pushed_at", ""))
st.markdown(
    f'<div class="hero-banner">'
    f'<div class="hero-left">'
    f'<div class="hero-icon">📡</div>'
    f'<div>'
    f'<div class="hero-title">Internet Reliability <span>SQL Repo</span></div>'
    f'<div class="hero-sub">Charter FTTP · Access · CPE — {total_sql} queries across 3 domains</div>'
    f'</div></div>'
    f'<div class="hero-right">'
    f'<span class="hero-pill live">Last push {last_push}</span>'
    f'<span class="hero-pill">{len(contributors)} contributors</span>'
    f'<span class="hero-pill">{len(workflow_runs)} CI workflows</span>'
    f'</div></div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_repo, tab_map, tab_players, tab_badges = st.tabs([
    "🏛  Overview", "🗺  Repo Map", "🎮  Players", "🎖  Badges"
])

if st.query_params.get("tab") == "badges":
    components.html(
        """<script>
        (function () {
            const findAndClick = () => {
                const tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
                for (const t of tabs) {
                    if (t.innerText && t.innerText.indexOf('Badges') !== -1) { t.click(); return true; }
                }
                return false;
            };
            let tries = 0;
            const id = setInterval(() => { if (findAndClick() || ++tries > 20) clearInterval(id); }, 100);
        })();
        </script>""",
        height=0,
    )

# ═════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ═════════════════════════════════════════════════════════════════════════════
with tab_repo:

    # ── Repo Stats Strip ─────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Repo Stats</div>', unsafe_allow_html=True)

    lang_pills = "".join(f'<span class="lang-pill">{ls.name}</span>' for ls in langs_ranked[:3])
    strip = [
        ("Total SQL files",  str(total_sql),                             "FTTP + Access + CPE"),
        ("Repo size",        f"{repo_info.get('size', 0)/1024:.1f} MB",  ""),
        ("Top language",     langs_ranked[0].name if langs_ranked else "—", "by file count"),
        ("Last pushed",      last_push,                                  ""),
        ("Contributors",     str(len(contributors)),                     "total"),
        ("Open issues",      str(repo_info.get("open_issues_count", 0)), "incl. CI audit issues"),
    ]
    cols = st.columns(len(strip))
    for col, (lbl, val, sub) in zip(cols, strip):
        col.markdown(_card(lbl, val, sub), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    doc_col, ci_col = st.columns([1, 1])

    # ── Doc Health ────────────────────────────────────────────────────────────
    with doc_col:
        st.markdown('<div class="section-label">Doc Health</div>', unsafe_allow_html=True)
        total   = health["total"]
        letter, color, label = get_grade(total)

        signals_html = ""
        for sig_id, icon, sig_label, max_pts in SIGNAL_DEFS:
            earned    = health["scores"].get(sig_id, 0)
            pct       = round(earned / max_pts * 100)
            bar_color = "#10B981" if pct >= 80 else "#F59E0B" if pct >= 50 else "#EF4444"
            signals_html += (
                f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:7px">'
                f'<span style="width:16px;text-align:center;font-size:13px">{icon}</span>'
                f'<span style="font-size:11px;width:200px;flex-shrink:0;color:#374151">{sig_label}</span>'
                f'<div class="signal-bar-bg"><div class="signal-bar" '
                f'style="width:{pct}%;background:{bar_color}"></div></div>'
                f'<span style="font-size:10px;color:#9CA3AF;width:46px;text-align:right">'
                f'{earned}/{max_pts}</span></div>'
            )

        fix_html = ""
        if health["fix_list"] and total < 90:
            items = "".join(
                f'<div style="font-size:11px;color:#6B7280;padding:2px 0">{f}</div>'
                for f in health["fix_list"][:5]
            )
            fix_html = (
                f'<div style="font-size:10px;font-weight:600;text-transform:uppercase;'
                f'letter-spacing:.06em;color:#9CA3AF;margin:10px 0 5px">Fix list</div>{items}'
            )

        st.markdown(
            f'<div class="doc-card" style="display:grid;grid-template-columns:130px 1fr;gap:20px;align-items:start">'
            f'<div style="text-align:center;padding-top:8px">'
            f'<span class="grade-letter" style="color:{color}">{letter}</span>'
            f'<div style="font-size:13px;color:#6B7280;font-weight:600;margin-top:6px">{total} / 100</div>'
            f'<div style="font-size:10px;color:#9CA3AF">{label}</div>'
            f'</div>'
            f'<div>{signals_html}{fix_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── CI Status ──────────────────────────────────────────────────────────────
    with ci_col:
        st.markdown('<div class="section-label">GitHub Actions</div>', unsafe_allow_html=True)
        st.markdown(_ci_status_html(workflow_runs), unsafe_allow_html=True)

        st.markdown('<div style="margin-top:12px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Key Docs</div>', unsafe_allow_html=True)

        pills_html = ""
        for fname, icon, desc in KEY_DOCS:
            present = fname.lower() in root_filenames
            cls = "present" if present else "missing"
            check = "✓" if present else "✗"
            pills_html += (
                f'<div class="keydoc-pill {cls}">'
                f'<span class="kd-icon">{icon}</span>'
                f'<span class="kd-name">{check} {fname}</span>'
                f'<span class="kd-desc">{desc}</span>'
                f'</div>'
            )
        st.markdown(f'<div class="keydoc-strip">{pills_html}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Top Contributors ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Top Contributors — Last 30 Days</div>', unsafe_allow_html=True)
    repo_top = sorted(metrics_map.values(), key=lambda m: -m["total_commits"])[:4]
    if repo_top:
        grid_html, grid_height = build_player_grid(repo_top, badge_map)
        components.html(grid_html, height=grid_height, scrolling=False)


# ═════════════════════════════════════════════════════════════════════════════
# REPO MAP TAB
# ═════════════════════════════════════════════════════════════════════════════
with tab_map:

    st.markdown('<div class="section-label">Domain Map</div>', unsafe_allow_html=True)

    # ── 4 domain cards in a 2×2 grid ─────────────────────────────────────────
    domain_cards_html = '<div class="domain-grid">'
    for d in DOMAIN_DEFS:
        key   = d["key"]
        count = domain_counts.get(key, 0)
        unit  = "queries" if key != "Tables" else "tables"
        tags  = "".join(f'<span class="dc-tag">{t}</span>' for t in d["tags"])

        domain_cards_html += (
            f'<div class="domain-card {d["cls"]}">'
            f'<div class="dc-header">'
            f'<div class="dc-icon">{d["icon"]}</div>'
            f'<div style="text-align:right">'
            f'<div class="dc-count">{count}</div>'
            f'<div class="dc-count-lbl">{unit}</div>'
            f'</div></div>'
            f'<div class="dc-name">{d["name"]}</div>'
            f'<div class="dc-desc">{d["desc"]}</div>'
            f'<div class="dc-tags">{tags}</div>'
            f'<div style="font-size:10px;color:#9CA3AF;margin-top:8px">Owner: {d["owner"]}</div>'
            f'</div>'
        )
    domain_cards_html += "</div>"
    st.markdown(domain_cards_html, unsafe_allow_html=True)

    ci_col2, docs_col2 = st.columns([1, 1])

    with ci_col2:
        st.markdown('<div class="section-label">GitHub Actions Status</div>', unsafe_allow_html=True)
        st.markdown(_ci_status_html(workflow_runs), unsafe_allow_html=True)

        st.markdown(
            '<div style="font-size:11px;color:#9CA3AF;margin-top:8px;padding:8px 12px;'
            'background:#F9FAFB;border-radius:7px;border:1px solid rgba(0,0,0,0.05)">'
            '💡 Run the cleanup audit anytime: GitHub → Actions tab → Monthly Cleanup Audit → Run workflow'
            '</div>',
            unsafe_allow_html=True,
        )

    with docs_col2:
        st.markdown('<div class="section-label">Repo Governance Files</div>', unsafe_allow_html=True)

        GOV_FILES = [
            (".github/workflows/lint-commits.yml",     "🔒", "Blocks commits missing .sql extension or doc header"),
            (".github/workflows/repo-index.yml",       "📇", "Auto-regenerates REPO_INDEX.md on every SQL push"),
            (".github/workflows/cleanup-audit.yml",    "🧹", "Monthly issue: missing extensions, binary files, vague commits"),
            ("CLAUDE.md",                               "📐", "Canonical SQL patterns, doc header standard, contribution rules"),
            ("ONBOARDING.md",                           "🚀", "Step-by-step GitHub + Cursor setup for new team members"),
            ("Access.md",                               "🔑", "Redshift & Athena login, connection steps, common auth errors"),
        ]
        pills = ""
        for fpath, icon, desc in GOV_FILES:
            fname  = fpath.split("/")[-1]
            present = any(f["path"] == fpath or f["path"].lower() == fname.lower() for f in tree)
            cls    = "present" if present else "missing"
            check  = "✓" if present else "✗"
            pills += (
                f'<div class="keydoc-pill {cls}" style="margin-bottom:5px;display:flex">'
                f'<span class="kd-icon">{icon}</span>'
                f'<div><div class="kd-name">{check} {fname}</div>'
                f'<div class="kd-desc">{desc}</div></div>'
                f'</div>'
            )
        st.markdown(f'<div>{pills}</div>', unsafe_allow_html=True)

    # ── Tables directory ───────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Tables Directory</div>', unsafe_allow_html=True)

    TABLE_DEFS = [
        ("QOS_INSIGHTS_DAILY",                  "Redshift",  "FTTP + CPE",    "#EFF6FF", "#1D4ED8"),
        ("hsd_qos_insights_enc",                "Athena",    "CPE notebooks", "#F5F3FF", "#5B21B6"),
        ("modem_hr_ipdr_topology",              "Athena",    "FTTP + Access", "#ECFDF5", "#065F46"),
        ("hsd_scope_onu_light_attenuation_daily","Redshift", "FTTP Pareto",   "#FFF7ED", "#92400E"),
        ("iq_completed_work_orders",            "Redshift",  "CPE Swaps",     "#ECFDF5", "#065F46"),
        ("iq_issue_categorization",             "Redshift*", "Access DAA",    "#FFF7ED", "#92400E"),
    ]
    tbl_cols = st.columns(3)
    for i, (tname, env, used_in, bg, fg) in enumerate(TABLE_DEFS):
        with tbl_cols[i % 3]:
            st.markdown(
                f'<div style="background:{bg};border-radius:9px;padding:12px 14px;'
                f'margin-bottom:10px;border:1px solid {fg}22">'
                f'<div style="font-size:11.5px;font-weight:600;color:{fg};'
                f'font-family:monospace;margin-bottom:5px">{tname}</div>'
                f'<div style="display:flex;gap:6px;align-items:center">'
                f'<span style="font-size:10px;background:{fg}18;color:{fg};'
                f'padding:1px 7px;border-radius:4px;font-weight:500">{env}</span>'
                f'<span style="font-size:10px;color:#6B7280">{used_in}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )


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

    st.markdown('<div class="section-label">Player Stats</div>', unsafe_allow_html=True)

    total_xp      = sum(compute_xp(m, len(badge_map.get(m["login"], []))) for m in players_by_xp)
    top_m         = players_by_xp[0]
    top_level     = get_level(compute_xp(top_m, len(badge_map.get(top_m["login"], []))))
    top_streak    = max(players_by_xp, key=lambda m: m["streak"])
    top_night     = max(players_by_xp, key=lambda m: m["night_commits"])
    top_early     = max(players_by_xp, key=lambda m: m["early_commits"])
    total_commits = sum(m["total_commits"] for m in players_by_xp)
    total_lines   = sum(m["lines_added"]   for m in players_by_xp)

    p_cols8 = st.columns(8)
    p_strip = [
        ("Team XP",        f"{total_xp:,}",               "total earned"),
        ("Top Level",      str(top_level["num"]),           top_level["title"]),
        ("Active Players", str(len(players_by_xp)),         "last 30 days"),
        ("Team Commits",   f"{total_commits:,}",            "last 30 days"),
        ("Lines Written",  f"+{total_lines:,}",             "last 30 days"),
        ("Longest Streak", f"{top_streak['streak']}d",      top_streak["login"]),
        ("Night Shift",    top_night["login"],               f"{top_night['night_commits']} late"),
        ("Early Riser",    top_early["login"],               f"{top_early['early_commits']} before 10am"),
    ]
    for col, (lbl, val, sub) in zip(p_cols8, p_strip):
        col.markdown(_card(lbl, val, sub), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
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
# WANDERING SPRITES
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
    player = players_ranked[idx % len(players_ranked)]
    sprite = render_sprite(idx % len(SPRITES), px=4, animate=False)
    cls    = "w-right" if direction == "right" else "w-left"
    wanderers += (
        f'<div class="wanderer {cls}" style="--dur:{dur};--delay:{delay}">'
        f'{sprite}'
        f'<div class="wanderer-name">{player["login"]}</div>'
        f'</div>'
    )

st.markdown(f'<div class="wanderer-bar">{wanderers}</div>', unsafe_allow_html=True)
