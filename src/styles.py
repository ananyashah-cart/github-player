"""Global CSS injected into Streamlit via st.markdown."""

CSS = """
/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, [data-testid="stDecoration"],
[data-testid="stHeader"] { display: none !important; }

/* ── Layout ── */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 1340px !important;
}
[data-testid="stApp"]         { background: #FAF8F5; }
section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 0.5px solid rgba(0,0,0,0.08) !important;
}

/* ── Sidebar inputs ── */
[data-testid="stSidebar"] label {
    font-size: 11px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: #6B6B6B !important;
}
[data-testid="stSidebar"] input {
    border: 0.5px solid rgba(0,0,0,0.1) !important;
    border-radius: 6px !important;
    background: #FAF8F5 !important;
    font-size: 13px !important;
}

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background: #FFFFFF !important;
    border: 0.5px solid rgba(0,0,0,0.08) !important;
    border-radius: 8px !important;
    padding: 4px !important;
    gap: 2px !important;
    width: fit-content !important;
    margin-bottom: 1rem !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 5px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #6B6B6B !important;
    padding: 6px 18px !important;
    border: none !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: #FAF8F5 !important;
    color: #1A1A1A !important;
}
[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] { display: none !important; }

/* ── Remove column gap ── */
div[data-testid="column"] { padding: 0 5px !important; }
div[data-testid="column"]:first-child { padding-left: 0 !important; }
div[data-testid="column"]:last-child  { padding-right: 0 !important; }
.stMarkdown { margin-bottom: 0 !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }

/* ── Stat card ── */
.stat-card {
    background: #FFFFFF;
    border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 8px;
    padding: 10px 13px;
    min-height: 70px;
    font-family: 'Inter', system-ui, sans-serif;
}
.stat-label  { font-size: 11px; color: #6B6B6B; margin-bottom: 3px; white-space: nowrap; }
.stat-value  { font-size: 19px; font-weight: 500; line-height: 1.2; }
.stat-sub    { font-size: 10px; color: #6B6B6B; margin-top: 1px; }

/* ── Section label ── */
.section-label {
    font-size: 11px; font-weight: 500;
    letter-spacing: 0.07em; text-transform: uppercase;
    color: #6B6B6B; margin-bottom: 6px; margin-top: 4px;
}

/* ── Doc health ── */
.doc-card {
    background: #FFFFFF;
    border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 8px;
    padding: 14px 16px;
}
.grade-letter {
    font-size: 60px; font-weight: 500; line-height: 1;
    animation: gradePulse 2.5s ease-in-out infinite;
    display: block;
}
@keyframes gradePulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.06)} }
.signal-bar-bg {
    height: 5px; background: #FAF8F5;
    border-radius: 3px; overflow: hidden; flex: 1;
}
.signal-bar { height: 100%; border-radius: 3px; }

/* ── Contributor card ── */
.contrib-card {
    background: #FFFFFF;
    border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 8px; padding: 13px;
    font-family: 'Inter', system-ui, sans-serif;
    height: 100%;
}
.contrib-card.top { border: 1.5px solid #EF9F27; }

/* ── Player card ── */
.player-card {
    background: #FFFFFF;
    border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 10px; padding: 16px;
    font-family: 'Inter', system-ui, sans-serif;
    position: relative; height: 100%;
}
.player-card.g1 { border: 1.5px solid #EF9F27; }
.player-card.g2 { border: 1.5px solid #9CA3AF; }
.player-card.g3 { border: 1.5px solid #C97E3B; }

/* ── XP bar ── */
.xp-track {
    height: 7px; background: #FAF8F5;
    border-radius: 4px; overflow: hidden;
    border: 0.5px solid rgba(0,0,0,0.06);
}
.xp-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease; }

/* ── Mini stat ── */
.mini-stat {
    background: #FAF8F5; border-radius: 5px;
    padding: 5px 4px; text-align: center;
}
.mini-val { font-size: 13px; font-weight: 500; line-height: 1.2; }
.mini-lbl { font-size: 9px; color: #6B6B6B; }

/* ── Power badge ── */
.power-badge {
    position: absolute; top: 10px; right: 10px;
    background: #FAF8F5; border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 6px; padding: 3px 7px; text-align: center;
}
.power-num { font-size: 14px; font-weight: 500; line-height: 1; }
.power-lbl { font-size: 9px; color: #6B6B6B; text-transform: uppercase; letter-spacing: 0.04em; }

/* ── Rank badge ── */
.rank-chip {
    display: inline-block; font-size: 10px; font-weight: 500;
    padding: 1px 6px; border-radius: 3px;
    background: #FAF8F5; color: #6B6B6B;
    border: 0.5px solid rgba(0,0,0,0.08);
}
.rank-chip.gold { background: #FEF9EC; color: #92600A; border-color: #F5D07A; }

/* ── Sparkline ── */
.spark-label { font-size: 10px; color: #6B6B6B; margin-bottom: 2px; }

/* ── Activity chips ── */
.act-chip {
    display: inline-block;
    background: #FAF8F5; border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 4px; padding: 1px 6px;
    font-size: 10px; white-space: nowrap;
}

/* ── Lang pill ── */
.lang-pill {
    display: inline-block; font-size: 10px;
    padding: 1px 6px; border-radius: 3px; margin: 1px 1px 0 0;
    background: #FAF8F5; border: 0.5px solid rgba(0,0,0,0.08);
    color: #6B6B6B;
}

/* ── Shame card ── */
.shame-card {
    background: #FFFFFF;
    border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 8px; padding: 12px 14px;
    font-family: 'Inter', system-ui, sans-serif;
}

/* ── Sprite ── */
.sprite-svg { image-rendering: pixelated; image-rendering: crisp-edges; }
.spr-bounce { animation: spriteBounce 0.55s ease-in-out infinite; }
@keyframes spriteBounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }

/* ── Wandering sprites ── */
.wanderer-bar {
    position: fixed; bottom: 0; left: 0; width: 100%;
    height: 54px; pointer-events: none; z-index: 9999;
    overflow: hidden;
}
.wanderer {
    position: absolute; bottom: 4px;
    display: flex; flex-direction: column; align-items: center; gap: 1px;
}
.wanderer-name {
    font-size: 9px; font-weight: 500; color: #6B6B6B;
    background: white; border: 0.5px solid rgba(0,0,0,0.08);
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
