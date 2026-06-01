"""Doc health scoring — tuned for the Internet Reliability SQL repo."""
from src.api import fetch_contents, fetch_raw_file

SQL_HEADER_KEYS = ("date created", "date:", "use case", "description", "owner")

SIGNAL_DEFS = [
    ("core_docs",   "📋", "Core docs (README, CLAUDE.md, ONBOARDING.md, Access.md)", 25),
    ("domain_cov",  "🗂",  "Domain README coverage (FTTP / Access / CPE / Tables)",   30),
    ("sql_headers", "🔖", "SQL doc-header compliance (date / use case / owner)",      25),
    ("governance",  "⚙️",  "CI & governance (.github/workflows, .gitignore)",          20),
]

GRADE_TIERS = [
    (85, "A", "#059669", "Ship it"),
    (65, "B", "#2563EB", "Mostly healthy"),
    (45, "C", "#D97706", "Needs love"),
    (0,  "D", "#DC2626", "Docs? What docs?"),
]

_KEY_DOCS = ["readme.md", "claude.md", "onboarding.md", "access.md"]
_DOMAINS  = ["FTTP", "Access", "CPE", "Tables"]


def score(repo: str, token: str) -> dict:
    result = {"scores": {}, "total": 0, "fix_list": [], "missing_dirs": []}

    root = fetch_contents(repo, token, "")
    if not isinstance(root, list):
        return result

    root_files = {i["name"].lower(): i for i in root if i["type"] == "file"}
    root_dirs  = {i["name"]: i for i in root if i["type"] == "dir"}

    # ── Signal 1: Core docs (25) ──────────────────────────────────────────────
    found_docs = [d for d in _KEY_DOCS if d in root_files]
    pts = round(25 * len(found_docs) / len(_KEY_DOCS))
    result["scores"]["core_docs"] = pts
    for d in _KEY_DOCS:
        if d not in root_files:
            result["fix_list"].append(f"📋 Missing root doc: {d}")

    # ── Signal 2: Domain README coverage (30) ────────────────────────────────
    covered = 0
    for domain in _DOMAINS:
        if domain not in root_dirs:
            result["missing_dirs"].append(domain)
            continue
        items = fetch_contents(repo, token, domain)
        if isinstance(items, list) and any(
            i["type"] == "file" and i["name"].lower() in ("readme.md", "readme.rst")
            for i in items
        ):
            covered += 1
        else:
            result["missing_dirs"].append(domain)
            result["fix_list"].append(f"🗂 {domain}/ is missing a README.md")
    result["scores"]["domain_cov"] = round(30 * covered / len(_DOMAINS))

    # ── Signal 3: SQL doc-header compliance (25) ─────────────────────────────
    # Sample up to 8 SQL files from the tree; check first 15 lines for required keys
    all_items_root = fetch_contents(repo, token, "")
    sql_files = []
    for domain in _DOMAINS[:3]:   # FTTP, Access, CPE
        items = fetch_contents(repo, token, domain)
        if isinstance(items, list):
            for item in items:
                if item["type"] == "file" and item["name"].lower().endswith(".sql"):
                    sql_files.append(item)
                    if len(sql_files) >= 8:
                        break
        if len(sql_files) >= 8:
            break

    if sql_files:
        compliant = 0
        for f in sql_files:
            raw = fetch_raw_file(f["download_url"], token)
            if raw:
                head = "\n".join(raw.split("\n")[:15]).lower()
                has_date  = any(k in head for k in ("date created", "date:"))
                has_use   = any(k in head for k in ("use case", "description", "purpose"))
                has_owner = "owner" in head
                if has_date and has_use and has_owner:
                    compliant += 1
        pct = compliant / len(sql_files)
        result["scores"]["sql_headers"] = round(25 * pct)
        if pct < 0.5:
            result["fix_list"].append(
                f"🔖 {len(sql_files) - compliant}/{len(sql_files)} sampled SQL files missing doc headers"
            )
    else:
        result["scores"]["sql_headers"] = 12  # neutral if no SQL found at root level

    # ── Signal 4: CI & governance (20) ────────────────────────────────────────
    gov_pts = 0
    has_gitignore = ".gitignore" in root_files
    has_github    = ".github" in root_dirs
    has_workflows = False
    if has_github:
        gh_items = fetch_contents(repo, token, ".github")
        has_workflows = isinstance(gh_items, list) and any(
            i["name"] == "workflows" for i in gh_items
        )
    if has_gitignore: gov_pts += 5
    if has_github:    gov_pts += 5
    if has_workflows: gov_pts += 10
    result["scores"]["governance"] = gov_pts
    if not has_gitignore: result["fix_list"].append("⚙️ No .gitignore found")
    if not has_workflows: result["fix_list"].append("⚙️ No .github/workflows found")

    result["total"] = sum(result["scores"].values())
    return result


def get_grade(total: int) -> tuple:
    """Returns (letter, color, label)."""
    for min_score, letter, color, label in GRADE_TIERS:
        if total >= min_score:
            return letter, color, label
    return "D", "#DC2626", "Docs? What docs?"
