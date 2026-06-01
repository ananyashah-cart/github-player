"""Global CSS injected into Streamlit via st.markdown."""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, [data-testid="stDecoration"],
[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="stSidebarNav"],
[data-testid="collapsedControl"] { display: none !important; }

/* ── Layout ── */
.block-container {
    padding-top: 0 !important;
    padding-bottom: 1rem !important;
    max-width: 1380px !important;
}
[data-testid="stApp"] { background: #F5F6FA; }
.stMarkdown { margin-bottom: 0 !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
div[data-testid="column"] { padding: 0 6px !important; }
div[data-testid="column"]:first-child { padding-left: 0 !important; }
div[data-testid="column"]:last-child  { padding-right: 0 !important; }

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%);
    border-radius: 0 0 16px 16px;
    padding: 20px 28px 18px;
    margin: -1.5rem -1rem 1.2rem;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 4px 24px rgba(0,0,0,0.18);
}
.hero-left { display: flex; align-items: center; gap: 14px; }
.hero-icon { font-size: 32px; line-height: 1; }
.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: 22px; font-weight: 700;
    color: #FFFFFF; line-height: 1.1;
}
.hero-title span { color: #60A5FA; }
.hero-sub {
    font-size: 11px; color: rgba(255,255,255,0.5);
    margin-top: 3px; font-weight: 400;
}
.hero-right { display: flex; gap: 8px; align-items: center; }
.hero-pill {
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; color: rgba(255,255,255,0.7);
    font-family: 'Inter', sans-serif; font-weight: 500;
}
.hero-pill.live { background: rgba(52,211,153,0.15); border-color: rgba(52,211,153,0.3); color: #34D399; }
.hero-pill.live::before { content: "●  "; font-size: 8px; }

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background: #FFFFFF !important;
    border: 1px solid rgba(0,0,0,0.07) !important;
    border-radius: 10px !important;
    padding: 4px !important; gap: 2px !important;
    width: fit-content !important; margin-bottom: 1rem !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}
[data-baseweb="tab"] {
    background: transparent !important; border-radius: 7px !important;
    font-size: 13px !important; font-weight: 500 !important;
    color: #6B7280 !important; padding: 6px 18px !important;
    border: none !important; transition: all 0.15s !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: #1A1A2E !important; color: #FFFFFF !important;
    box-shadow: 0 1px 6px rgba(26,26,46,0.25) !important;
}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }

/* ── Section label ── */
.section-label {
    font-size: 10.5px; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: #9CA3AF; margin-bottom: 7px; margin-top: 6px;
    display: flex; align-items: center; gap: 6px;
}
.section-label::after {
    content: ""; flex: 1; height: 1px;
    background: rgba(0,0,0,0.06);
}

/* ── Stat card ── */
.stat-card {
    background: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 10px; padding: 12px 14px;
    min-height: 72px; font-family: 'Inter', system-ui, sans-serif;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.15s;
}
.stat-card:hover { box-shadow: 0 3px 10px rgba(0,0,0,0.08); }
.stat-label { font-size: 10.5px; color: #9CA3AF; margin-bottom: 4px; font-weight: 500; white-space: nowrap; }
.stat-value { font-size: 20px; font-weight: 600; line-height: 1.1; color: #111827; }
.stat-sub   { font-size: 10px; color: #9CA3AF; margin-top: 2px; }

/* ── Domain cards ── */
.domain-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14px; margin-bottom: 16px;
}
.domain-card {
    background: #FFFFFF; border-radius: 12px;
    padding: 18px 20px; border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    position: relative; overflow: hidden;
    transition: transform 0.15s, box-shadow 0.15s;
    cursor: default;
}
.domain-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
.domain-card::before {
    content: ""; position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
}
.domain-card.fttp::before  { background: linear-gradient(90deg, #2563EB, #60A5FA); }
.domain-card.access::before { background: linear-gradient(90deg, #D97706, #FBBF24); }
.domain-card.cpe::before   { background: linear-gradient(90deg, #059669, #34D399); }
.domain-card.tables::before { background: linear-gradient(90deg, #7C3AED, #A78BFA); }
.domain-card .dc-header {
    display: flex; align-items: flex-start;
    justify-content: space-between; margin-bottom: 10px;
}
.domain-card .dc-icon { font-size: 26px; line-height: 1; }
.domain-card .dc-count {
    font-size: 28px; font-weight: 700; line-height: 1;
    color: #111827;
}
.domain-card .dc-count-lbl {
    font-size: 10px; color: #9CA3AF; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.05em;
    margin-top: 2px; text-align: right;
}
.domain-card .dc-name {
    font-size: 15px; font-weight: 600; color: #111827; margin-bottom: 4px;
}
.domain-card .dc-desc {
    font-size: 11.5px; color: #6B7280; line-height: 1.5;
}
.domain-card.fttp  .dc-count { color: #2563EB; }
.domain-card.access .dc-count { color: #D97706; }
.domain-card.cpe   .dc-count { color: #059669; }
.domain-card.tables .dc-count { color: #7C3AED; }
.domain-card .dc-tags {
    display: flex; flex-wrap: wrap; gap: 4px; margin-top: 10px;
}
.dc-tag {
    font-size: 10px; padding: 2px 8px; border-radius: 4px;
    font-weight: 500;
}
.fttp  .dc-tag { background: #EFF6FF; color: #1D4ED8; }
.access .dc-tag { background: #FFFBEB; color: #92400E; }
.cpe   .dc-tag { background: #ECFDF5; color: #065F46; }
.tables .dc-tag { background: #F5F3FF; color: #5B21B6; }

/* ── CI / Workflow badges ── */
.ci-strip {
    display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 4px;
}
.ci-badge {
    display: flex; align-items: center; gap: 8px;
    background: #FFFFFF; border: 1px solid rgba(0,0,0,0.07);
    border-radius: 8px; padding: 8px 14px;
    font-family: 'Inter', sans-serif; font-size: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    flex: 1; min-width: 200px;
}
.ci-badge .ci-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.ci-badge .ci-dot.success { background: #10B981; box-shadow: 0 0 0 3px rgba(16,185,129,0.15); }
.ci-badge .ci-dot.failure { background: #EF4444; box-shadow: 0 0 0 3px rgba(239,68,68,0.15); }
.ci-badge .ci-dot.pending { background: #F59E0B; box-shadow: 0 0 0 3px rgba(245,158,11,0.15); }
.ci-badge .ci-dot.unknown { background: #9CA3AF; }
.ci-badge .ci-name { font-weight: 500; color: #111827; flex: 1; }
.ci-badge .ci-time { font-size: 10.5px; color: #9CA3AF; white-space: nowrap; }

/* ── Key docs strip ── */
.keydoc-strip {
    display: flex; gap: 8px; flex-wrap: wrap;
}
.keydoc-pill {
    display: flex; align-items: center; gap: 6px;
    background: #FFFFFF; border: 1px solid rgba(0,0,0,0.07);
    border-radius: 7px; padding: 6px 12px;
    font-size: 12px; font-family: 'Inter', sans-serif;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.keydoc-pill .kd-icon { font-size: 14px; }
.keydoc-pill .kd-name { font-weight: 500; color: #374151; }
.keydoc-pill .kd-desc { color: #9CA3AF; font-size: 10.5px; }
.keydoc-pill.present { border-color: rgba(16,185,129,0.25); background: #F0FDF4; }
.keydoc-pill.present .kd-name { color: #065F46; }
.keydoc-pill.missing { border-color: rgba(239,68,68,0.2); background: #FFF5F5; }
.keydoc-pill.missing .kd-name { color: #991B1B; }

/* ── Doc health ── */
.doc-card {
    background: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 12px; padding: 16px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.grade-letter {
    font-size: 64px; font-weight: 700; line-height: 1;
    animation: gradePulse 3s ease-in-out infinite; display: block;
}
@keyframes gradePulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.04)} }
.signal-bar-bg {
    height: 6px; background: #F3F4F6;
    border-radius: 3px; overflow: hidden; flex: 1;
}
.signal-bar { height: 100%; border-radius: 3px; transition: width 0.6s ease; }

/* ── Player cards ── */
.contrib-card {
    background: #FFFFFF; border: 1px solid rgba(0,0,0,0.06);
    border-radius: 10px; padding: 14px;
    font-family: 'Inter', system-ui, sans-serif;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.contrib-card.top { border: 1.5px solid #F59E0B; }

/* ── XP bar ── */
.xp-track {
    height: 7px; background: #F3F4F6;
    border-radius: 4px; overflow: hidden;
}
.xp-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease; }

/* ── Mini stat ── */
.mini-stat {
    background: #F9FAFB; border-radius: 6px;
    padding: 6px 4px; text-align: center;
    border: 1px solid rgba(0,0,0,0.04);
}
.mini-val { font-size: 14px; font-weight: 600; line-height: 1.2; color: #111827; }
.mini-lbl { font-size: 9.5px; color: #9CA3AF; margin-top: 1px; }

/* ── Power badge ── */
.power-badge {
    position: absolute; top: 10px; right: 10px;
    background: #F9FAFB; border: 1px solid rgba(0,0,0,0.07);
    border-radius: 7px; padding: 3px 8px; text-align: center;
}
.power-num { font-size: 14px; font-weight: 600; line-height: 1; color: #111827; }
.power-lbl { font-size: 9px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.04em; }

/* ── Rank chip ── */
.rank-chip {
    display: inline-block; font-size: 10px; font-weight: 500;
    padding: 1px 6px; border-radius: 3px;
    background: #F9FAFB; color: #6B7280;
    border: 1px solid rgba(0,0,0,0.07);
}
.rank-chip.gold { background: #FFFBEB; color: #92400E; border-color: #F59E0B; }

/* ── Sparkline ── */
.spark-label { font-size: 10px; color: #9CA3AF; margin-bottom: 2px; }

/* ── Activity chips ── */
.act-chip {
    display: inline-block;
    background: #F9FAFB; border: 1px solid rgba(0,0,0,0.07);
    border-radius: 5px; padding: 2px 7px;
    font-size: 10.5px; white-space: nowrap;
}

/* ── Lang pill ── */
.lang-pill {
    display: inline-block; font-size: 10px;
    padding: 2px 8px; border-radius: 4px; margin: 1px 1px 0 0;
    background: #EFF6FF; border: 1px solid #BFDBFE; color: #1D4ED8;
    font-weight: 500;
}

/* ── Help popup ── */
.help-popup {
    position: fixed; top: 14px; left: 14px;
    z-index: 10000; font-family: 'Inter', system-ui, sans-serif;
}
.help-popup .help-toggle-input { display: none; }
.help-popup .help-toggle-btn {
    cursor: pointer; background: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.1);
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 600; color: #6B7280;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1); user-select: none;
    transition: all 0.15s;
}
.help-popup .help-toggle-btn::before { content: "?"; }
.help-popup .help-toggle-btn:hover { background: #1A1A2E; color: white; border-color: #1A1A2E; }
.help-popup .help-toggle-input:checked ~ .help-toggle-btn { background: #1A1A2E; color: white; border-color: #1A1A2E; }
.help-popup .help-toggle-input:checked ~ .help-toggle-btn::before { content: "✕"; font-size: 13px; }
.help-popup .help-card { display: none; }
.help-popup .help-toggle-input:checked ~ .help-card { display: block; }
.help-card {
    background: #FFFFFF; border: 1px solid rgba(0,0,0,0.1);
    border-radius: 12px; padding: 16px 18px; width: 340px;
    margin-top: 8px; box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    font-size: 12px; line-height: 1.55; color: #1A1A1A;
}
.help-card h4 { font-size: 14px; font-weight: 600; margin: 0 0 8px 0; }
.help-card .help-row {
    display: flex; align-items: flex-start; gap: 8px;
    padding: 6px 0; border-top: 1px dashed rgba(0,0,0,0.06);
}
.help-card .help-row:first-of-type { border-top: none; }
.help-card .help-icon { font-size: 18px; width: 22px; flex-shrink: 0; line-height: 1.3; }
.help-card .help-text { flex: 1; }
.help-card .help-label { font-weight: 600; color: #111827; font-size: 12px; }
.help-card .help-desc { color: #6B7280; font-size: 11px; }
.help-card .help-tagline {
    font-size: 11px; color: #6B7280; margin-bottom: 10px;
    padding-bottom: 8px; border-bottom: 1px solid rgba(0,0,0,0.07);
}

/* ── Shame card ── */
.shame-card {
    background: #FFFFFF; border: 1px solid rgba(0,0,0,0.06);
    border-radius: 10px; padding: 12px 14px;
    font-family: 'Inter', system-ui, sans-serif;
}

/* ── Sprite ── */
.sprite-svg { image-rendering: pixelated; image-rendering: crisp-edges; }
.spr-bounce { animation: spriteBounce 0.55s ease-in-out infinite; }
@keyframes spriteBounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }

/* ── Wandering sprites ── */
.wanderer-bar {
    position: fixed; bottom: 0; left: 0; width: 100%;
    height: 54px; pointer-events: none; z-index: 9999; overflow: hidden;
}
.wanderer {
    position: absolute; bottom: 4px;
    display: flex; flex-direction: column; align-items: center; gap: 1px;
}
.wanderer-name {
    font-size: 9px; font-weight: 500; color: #6B7280;
    background: white; border: 1px solid rgba(0,0,0,0.07);
    border-radius: 3px; padding: 0 4px; white-space: nowrap;
    font-family: 'Inter', system-ui, sans-serif;
}
.w-right { animation: goRight var(--dur,14s) var(--delay,0s) linear infinite; }
.w-left  { animation: goLeft  var(--dur,14s) var(--delay,0s) linear infinite; }
@keyframes goRight {
    from { transform: translateX(-80px) scaleX(1); }
    to   { transform: translateX(calc(100vw + 80px)) scaleX(1); }
}
@keyframes goLeft {
    from { transform: translateX(calc(100vw + 80px)) scaleX(-1); }
    to   { transform: translateX(-80px) scaleX(-1); }
}
"""
