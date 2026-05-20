"""Badges explainer tab — fun copy + how-to-earn for every badge.

Renders as a single embedded HTML grid so the layout is consistent
and links from player_grid (#badge-<id> anchors) work natively.
"""
from src.gamification import BADGE_DEFS, TIER_STYLES


# Each entry: (id, how_to_earn, fun_flavor)
BADGE_COPY = {
    "commit_king":   ("Most commits in the last 30 days.",
                      "You don't just write code — you make commits like it's a personal sport. Every keystroke a victory lap."),
    "line_lord":     ("Most lines added in the last 30 days.",
                      "Volume is your love language. Quality? We'll get to that in code review. Probably."),
    "on_streak":     ("Longest unbroken run of commit days.",
                      "Vacation? Never heard of her. The contribution graph is your portrait gallery."),
    "delete_demon":  ("Most lines deleted in the last 30 days.",
                      "The best code is no code. You're out here making the repo smaller, faster, lighter. Marie Kondo would weep."),
    "speed_runner":  ("Shortest average gap between commits.",
                      "Commit. Push. Commit. Push. You operate at a tempo most humans can't sustain."),

    "night_owl":     ("Most commits after 7 PM.",
                      "Code at midnight hits different. The bugs you write now are tomorrow's problem — and you're at peace with that."),
    "early_bird":    ("Most commits before 9:30 AM.",
                      "First in, coffee in hand, productivity meter pegged. The rest of us are still trying to find our chargers."),
    "workaholic":    ("Most commits on a Saturday or Sunday.",
                      "Weekends are just weekdays with worse lighting, apparently. Your hobbies and your job are the same shape."),
    "ai_whisperer":  ("Most commits mentioning 'Claude' in the message.",
                      "You and your AI co-author are basically a duo now. Cool. We're not mad. We're just taking notes."),
    "sober_royalty": ("Most commits Thursday between 6 PM and 9 PM.",
                      "The team's at happy hour. You're at your keyboard. Bottoms up to type 'git push'."),

    "silent_night":  ("No commits in the last 3+ days.",
                      "The repo whispers your name into the void. Are you OK? Did you finally take that vacation? Blink twice."),
    "doc_dread":     ("Less than 3% of your added lines are comments (# or --).",
                      "Future-you opens this code in 6 months and weeps. Past-you knew what it did. Past-you is gone now."),
    "lazy_commit":   ("Most commits with messages like 'fix', 'wip', 'update'.",
                      "'fix'. Fix WHAT, exactly? Your descendants will never know. The git log is a haiku of regret."),
}


# Visual hero block — big icon + name in tier-colored card.
def _hero_card(badge: dict, how: str, flavor: str) -> str:
    style = TIER_STYLES.get(badge["tier"], ("background:#FAF8F5;color:#1A1A1A",))[0]
    tier_label = badge["tier"].upper()
    return (
        f'<div class="badge-explain" id="badge-{badge["id"]}">'
        f'<div class="badge-hero" style="{style}">'
        f'<div class="badge-hero-icon">{badge["icon"]}</div>'
        f'<div>'
        f'<div class="badge-hero-name">{badge["label"]}</div>'
        f'<div class="badge-hero-tier">{tier_label}</div>'
        f'</div></div>'
        f'<div class="badge-how"><span class="badge-how-lbl">How to earn</span> {how}</div>'
        f'<div class="badge-flavor">{flavor}</div>'
        f'</div>'
    )


def _section(title: str, subtitle: str, badge_ids: list[str], by_id: dict) -> str:
    cards = "".join(
        _hero_card(by_id[bid], *BADGE_COPY[bid])
        for bid in badge_ids if bid in by_id and bid in BADGE_COPY
    )
    return (
        f'<div class="badge-section">'
        f'<div class="badge-section-head">'
        f'<div class="badge-section-title">{title}</div>'
        f'<div class="badge-section-sub">{subtitle}</div></div>'
        f'<div class="badge-grid">{cards}</div>'
        f'</div>'
    )


_CSS = """
* { box-sizing: border-box; }
body { margin: 0; padding: 6px 2px 24px; background: #FAF8F5;
       font-family: 'Inter', system-ui, sans-serif; color: #1A1A1A; }

.badge-intro {
    background: linear-gradient(135deg, #EF9F27 0%, #d65108 100%);
    color: white;
    border-radius: 12px;
    padding: 22px 26px;
    margin-bottom: 22px;
}
.badge-intro h2 { margin: 0 0 6px 0; font-size: 22px; font-weight: 600; }
.badge-intro p  { margin: 0; font-size: 13px; line-height: 1.55; opacity: 0.95; }

.badge-section { margin-bottom: 22px; }
.badge-section-head { margin-bottom: 10px; }
.badge-section-title {
    font-size: 15px; font-weight: 600; color: #1A1A1A;
    margin-bottom: 2px;
}
.badge-section-sub {
    font-size: 11px; color: #6B6B6B;
    text-transform: uppercase; letter-spacing: 0.06em;
}

.badge-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    align-items: stretch;
}
@media (max-width: 900px) {
    .badge-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
    .badge-grid { grid-template-columns: 1fr; }
}

.badge-explain {
    background: #FFFFFF;
    border: 0.5px solid rgba(0,0,0,0.08);
    border-radius: 10px;
    padding: 14px;
    display: flex; flex-direction: column;
    scroll-margin-top: 30px;     /* offset for anchor jumps */
}
.badge-explain:target {
    box-shadow: 0 0 0 3px #EF9F27;
    transition: box-shadow 0.4s ease;
}

.badge-hero {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 12px; border-radius: 8px;
    margin-bottom: 10px;
}
.badge-hero-icon { font-size: 32px; line-height: 1; }
.badge-hero-name { font-size: 15px; font-weight: 600; line-height: 1.2; }
.badge-hero-tier {
    font-size: 9.5px; font-weight: 500;
    letter-spacing: 0.08em; opacity: 0.75;
    margin-top: 2px;
}

.badge-how {
    font-size: 12px; color: #1A1A1A;
    margin-bottom: 8px; line-height: 1.5;
}
.badge-how-lbl {
    display: inline-block;
    background: #FAF8F5; color: #6B6B6B;
    font-size: 9.5px; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.06em;
    padding: 2px 7px; border-radius: 4px;
    margin-right: 5px;
}
.badge-flavor {
    font-size: 12px; color: #6B6B6B;
    line-height: 1.55; font-style: italic;
}
"""


def build() -> tuple[str, int]:
    """Return (full_html, iframe_height_px) for the Badges tab."""
    by_id = {b["id"]: b for b in BADGE_DEFS}

    intro = (
        '<div class="badge-intro">'
        '<h2>🎖 The Badge Codex</h2>'
        "<p>Every contributor in this repo gets badges — some are flexes, "
        "some are warnings, all are auto-awarded based on the last 30 days "
        "of commits. They land in your player card whether you wanted them "
        "or not. No takebacks.</p>"
        "</div>"
    )

    achievement_ids = ["commit_king", "line_lord", "on_streak", "delete_demon", "speed_runner"]
    activity_ids    = ["night_owl", "early_bird", "workaholic", "ai_whisperer", "sober_royalty"]
    cursed_ids      = ["silent_night", "doc_dread", "lazy_commit"]

    body = (
        _section("🏆 Achievement Badges", "Earn these by being good at your job",
                 achievement_ids, by_id)
        + _section("⏰ Activity Badges", "Earn these by when (or how) you commit",
                   activity_ids, by_id)
        + _section("💀 Cursed Badges", "These find you. You don't choose them.",
                   cursed_ids, by_id)
    )

    html = (
        f'<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{_CSS}</style></head><body>'
        f'{intro}{body}'
        # On load, jump to the anchor if one was set in the URL hash.
        '<script>'
        'if (window.location.hash) {'
        '  const el = document.querySelector(window.location.hash);'
        '  if (el) el.scrollIntoView({behavior: "smooth", block: "start"});'
        '}'
        '</script>'
        '</body></html>'
    )

    # Rough height estimate: intro + 3 sections of ~3 rows each.
    height = 250 + 3 * 360 + 80
    return html, height
