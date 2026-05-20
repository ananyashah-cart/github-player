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
        "total_commits": 0,
        "lines_added": 0,
        "lines_deleted": 0,
        "night_commits": 0,
        "early_commits": 0,
        "friday_commits": 0,
        "streak": 0,
        "avg_gap_hours": float("inf"),
        "commit_days": set(),
        "commit_timestamps": [],
        "weekly_commits": [],
    }


def compute_contributor_metrics(stats_data: list, commit_list: list) -> dict:
    thirty_ago = datetime.now(timezone.utc) - timedelta(days=30)
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

    # Pass 2 — walk the commit list. Seeds any contributor missing from stats
    # (covers the 202-race on /stats/contributors) and adds time-based signals.
    stats_had_commits = {login for login, m in metrics.items() if m["total_commits"] > 0}
    for commit in commit_list:
        author_obj = commit.get("author") or {}
        login = author_obj.get("login", "") if isinstance(author_obj, dict) else ""
        if not login:
            # Fall back to commit.author.name when GitHub didn't resolve a user.
            login = ((commit.get("commit") or {}).get("author") or {}).get("name", "")
        if not login:
            continue
        if login not in metrics:
            avatar = author_obj.get("avatar_url", "") if isinstance(author_obj, dict) else ""
            metrics[login] = _blank_metrics(login, avatar)

        date_str = (commit.get("commit") or {}).get("author", {}).get("date", "")
        dt = _parse_dt(date_str)
        if not dt:
            continue

        # If /stats/contributors didn't give us a commit count, count from /commits.
        if login not in stats_had_commits:
            metrics[login]["total_commits"] += 1

        hour = dt.hour
        dow  = dt.weekday()   # 4 = Friday (Python convention)
        day_key = dt.strftime("%Y-%m-%d")
        if hour >= 18:
            metrics[login]["night_commits"] += 1
        if hour < 10:
            metrics[login]["early_commits"] += 1
        if dow == 4:
            metrics[login]["friday_commits"] += 1
        metrics[login]["commit_days"].add(day_key)
        metrics[login]["commit_timestamps"].append(dt.timestamp())

    # Derived: streak + avg gap.
    for m in metrics.values():
        m["streak"] = _streak(m["commit_days"])
        ts = sorted(m["commit_timestamps"])
        if len(ts) > 1:
            gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
            m["avg_gap_hours"] = sum(gaps) / len(gaps) / 3600

    return {k: v for k, v in metrics.items() if v["total_commits"] > 0}


def assign_badges(metrics_map: dict) -> dict:
    players = list(metrics_map.values())
    badge_map: dict = {login: [] for login in metrics_map}

    def _metric(badge_id: str, m: dict) -> float:
        if badge_id == "commit_king":  return m["total_commits"]
        if badge_id == "night_owl":    return m["night_commits"]
        if badge_id == "early_bird":   return m["early_commits"]
        if badge_id == "line_lord":    return m["lines_added"]
        if badge_id == "delete_demon": return m["lines_deleted"]
        if badge_id == "on_streak":    return m["streak"]
        if badge_id == "speed_runner":
            g = m["avg_gap_hours"]
            return 1 / g if g > 0 and math.isfinite(g) else 0
        if badge_id == "fri_deployer": return m["friday_commits"]
        return 0

    for badge in BADGE_DEFS:
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
