"""Contributor metrics computation and badge assignment."""
import math
from datetime import datetime, timedelta, timezone
from src.gamification import BADGE_DEFS

LAZY_MSGS = {
    "fix", "wip", "asdf", "test", "update", "misc", "stuff", "changes", "lol",
    "fixes", "typo", "todo", "done", "temp", "tmp", "work", "edit", "minor",
    "cleanup", "ok", "commit", "push", "save", ".", "..", "...",
}


def _parse_dt(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _streak(date_set: set) -> int:
    days = sorted(date_set)
    if not days:
        return 0
    mx = cur = 1
    for i in range(1, len(days)):
        d1 = datetime.strptime(days[i - 1], "%Y-%m-%d")
        d2 = datetime.strptime(days[i], "%Y-%m-%d")
        cur = cur + 1 if (d2 - d1).days <= 1 else 1
        mx = max(mx, cur)
    return mx


def _blank_metrics(login: str, avatar: str = "") -> dict:
    return {
        "login": login,
        "avatar": avatar or f"https://avatars.githubusercontent.com/u/0?u={login}",
        "total_commits":     0,
        "lines_added":       0,
        "lines_deleted":     0,
        "night_commits":     0,    # >= 7pm
        "early_commits":     0,    # < 9:30am
        "friday_commits":    0,    # (kept for legacy)
        "weekend_commits":   0,    # Sat or Sun
        "thursday_hh":       0,    # Thursday 6-9pm — missed happy hour
        "ai_commits":        0,    # commit message mentions "claude"
        "lazy_commits":      0,    # "fix", "wip", etc.
        "comment_lines":     0,    # added lines starting with # or --
        "code_lines_added":  0,    # total added lines (denominator for comment ratio)
        "days_since_last":   999,  # gap from now to most-recent commit
        "streak":            0,
        "avg_gap_hours":     float("inf"),
        "commit_days":       set(),
        "commit_timestamps": [],
        "weekly_commits":    [],
    }


def _count_comment_lines_in_patch(patch: str) -> tuple[int, int]:
    """Return (comment_added, total_added) for a single file's patch string.

    Looks for added lines (prefix '+') whose first non-whitespace content
    starts with '#' (Python/shell) or '--' (SQL). Excludes the diff header
    line '+++'.
    """
    added = comments = 0
    for line in (patch or "").split("\n"):
        if not line.startswith("+") or line.startswith("+++"):
            continue
        added += 1
        content = line[1:].lstrip()
        if content.startswith("#") or content.startswith("--"):
            comments += 1
    return comments, added


def compute_contributor_metrics(stats_data: list, commit_list: list) -> dict:
    now        = datetime.now(timezone.utc)
    thirty_ago = now - timedelta(days=30)
    metrics: dict = {}

    # Pass 1 — weekly stats (preferred: gives us lines added/deleted).
    for contributor in stats_data or []:
        author = contributor.get("author")
        if not author:
            continue
        login = author["login"]
        metrics[login] = _blank_metrics(login, author.get("avatar_url", ""))
        for w in contributor.get("weeks", []):
            week_end = datetime.fromtimestamp(w["w"] + 7 * 86400, timezone.utc)
            if week_end >= thirty_ago:
                metrics[login]["total_commits"] += w["c"]
                metrics[login]["lines_added"]   += w["a"]
                metrics[login]["lines_deleted"]  += w["d"]
                metrics[login]["weekly_commits"].append({"ts": w["w"] * 1000, "c": w["c"]})

    # Pass 2 — walk the commit list. Seeds contributors missing from stats and
    # extracts time-based signals + per-commit text/diff scans.
    stats_had_commits = {login for login, m in metrics.items() if m["total_commits"] > 0}
    for commit in commit_list:
        author_obj = commit.get("author") or {}
        login = author_obj.get("login", "") if isinstance(author_obj, dict) else ""
        if not login:
            login = ((commit.get("commit") or {}).get("author") or {}).get("name", "")
        if not login:
            continue
        if login not in metrics:
            avatar = author_obj.get("avatar_url", "") if isinstance(author_obj, dict) else ""
            metrics[login] = _blank_metrics(login, avatar)

        commit_obj = commit.get("commit") or {}
        date_str   = (commit_obj.get("author") or {}).get("date", "")
        msg        = commit_obj.get("message", "") or ""
        dt = _parse_dt(date_str)
        if not dt:
            continue

        # Commit count fallback when stats endpoint was empty.
        if login not in stats_had_commits:
            metrics[login]["total_commits"] += 1
            stats = commit.get("stats") or {}
            metrics[login]["lines_added"]   += stats.get("additions", 0)
            metrics[login]["lines_deleted"] += stats.get("deletions", 0)

        hour, minute = dt.hour, dt.minute
        dow = dt.weekday()    # Mon=0 … Sun=6

        # ── Time-of-day signals ──
        if hour >= 19:
            metrics[login]["night_commits"] += 1
        if hour < 9 or (hour == 9 and minute < 30):
            metrics[login]["early_commits"] += 1
        if dow == 4:                                  # Friday (kept for compat)
            metrics[login]["friday_commits"] += 1
        if dow == 5 or dow == 6:                      # Saturday or Sunday
            metrics[login]["weekend_commits"] += 1
        if dow == 3 and 18 <= hour < 21:              # Thursday 6-9pm
            metrics[login]["thursday_hh"] += 1

        # ── Commit-message signals ──
        msg_lower = msg.lower()
        if "claude" in msg_lower:
            metrics[login]["ai_commits"] += 1
        if is_lazy(msg):
            metrics[login]["lazy_commits"] += 1

        # ── Diff scan (only if commit was enriched with files/patch) ──
        for f in (commit.get("files") or []):
            patch = f.get("patch", "")
            if not patch:
                continue
            c, a = _count_comment_lines_in_patch(patch)
            metrics[login]["comment_lines"]    += c
            metrics[login]["code_lines_added"] += a

        metrics[login]["commit_days"].add(dt.strftime("%Y-%m-%d"))
        metrics[login]["commit_timestamps"].append(dt.timestamp())

    # Derived metrics: streak, avg gap, days-since-last.
    for m in metrics.values():
        m["streak"] = _streak(m["commit_days"])
        ts = sorted(m["commit_timestamps"])
        if len(ts) > 1:
            gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
            m["avg_gap_hours"] = sum(gaps) / len(gaps) / 3600
        if ts:
            m["days_since_last"] = (now.timestamp() - ts[-1]) / 86400

    return {k: v for k, v in metrics.items() if v["total_commits"] > 0}


# Some badges fire only when the metric crosses a threshold (Silent Night, Doc
# Dread). These are independent of who's "top" — multiple players can earn them.
def _threshold_badges(m: dict) -> list[str]:
    out = []
    # Silent Night: no commit in the last 3 days.
    if m["days_since_last"] >= 3:
        out.append("silent_night")
    # Documentation Dread: meaningful code volume + comment ratio under 3%.
    if m["code_lines_added"] >= 100 and (m["comment_lines"] / m["code_lines_added"]) < 0.03:
        out.append("doc_dread")
    return out


def assign_badges(metrics_map: dict) -> dict:
    players = list(metrics_map.values())
    badge_map: dict = {login: [] for login in metrics_map}
    by_id = {b["id"]: b for b in BADGE_DEFS}

    # ── Threshold badges (any player who qualifies gets them) ──
    for m in players:
        for badge_id in _threshold_badges(m):
            badge = by_id.get(badge_id)
            if badge:
                badge_map[m["login"]].append(badge)

    # ── Top-scorer badges (awarded to the max in each category) ──
    def _metric(badge_id: str, m: dict) -> float:
        if badge_id == "commit_king":    return m["total_commits"]
        if badge_id == "night_owl":      return m["night_commits"]
        if badge_id == "early_bird":     return m["early_commits"]
        if badge_id == "line_lord":      return m["lines_added"]
        if badge_id == "delete_demon":   return m["lines_deleted"]
        if badge_id == "on_streak":      return m["streak"]
        if badge_id == "workaholic":     return m["weekend_commits"]
        if badge_id == "ai_whisperer":   return m["ai_commits"]
        if badge_id == "sober_royalty":  return m["thursday_hh"]
        if badge_id == "lazy_commit":    return m["lazy_commits"]
        if badge_id == "speed_runner":
            g = m["avg_gap_hours"]
            return 1 / g if g > 0 and math.isfinite(g) else 0
        return 0   # silent_night and doc_dread are threshold-based

    top_scorer_ids = {
        "commit_king", "night_owl", "early_bird", "line_lord", "delete_demon",
        "on_streak", "speed_runner", "workaholic", "ai_whisperer",
        "sober_royalty", "lazy_commit",
    }
    for badge in BADGE_DEFS:
        if badge["id"] not in top_scorer_ids:
            continue
        scored = [(m["login"], _metric(badge["id"], m)) for m in players]
        max_val = max((v for _, v in scored), default=0)
        if max_val <= 0:
            continue
        for login, val in scored:
            if val == max_val:
                badge_map[login].append(badge)

    return badge_map


def is_lazy(msg: str) -> bool:
    if not msg:
        return True
    clean = msg.strip().lower().split("\n")[0]
    return len(clean) < 10 or clean in LAZY_MSGS
