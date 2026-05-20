"""Doc health scoring — 6 signals, max 100 points."""
from src.api import fetch_contents, fetch_raw_file

README_NAMES = {"readme.md", "readme.rst", "readme", "readme.txt"}
CODE_EXTS    = {".js", ".ts", ".py", ".java", ".go", ".rb", ".cs", ".cpp", ".c", ".rs"}
COMMENT_STARTS = ("//", "#", "/*", " *", "/**", '"""', "'''", "--")

SIGNAL_DEFS = [
    ("readme",    "📄", "Root README",              30),
    ("subdir",    "📂", "Subdir README coverage",   35),
    ("comments",  "💬", "Comment density",          20),
    ("configs",   "⚙️",  "Config docs",              15),
]

GRADE_TIERS = [
    (85, "A", "#27500A", "Ship it"),
    (65, "B", "#0C447C", "Mostly healthy"),
    (45, "C", "#633806", "Needs love"),
    (0,  "D", "#72243E", "Docs? What docs?"),
]


def _is_readme(name: str) -> bool:
    return name.lower() in README_NAMES


def _is_md(name: str) -> bool:
    return name.lower().endswith(".md")


def _is_code(name: str) -> bool:
    return any(name.lower().endswith(e) for e in CODE_EXTS)


def score(repo: str, token: str) -> dict:
    result = {"scores": {}, "total": 0, "fix_list": [], "missing_dirs": []}

    root = fetch_contents(repo, token, "")
    if not isinstance(root, list):
        return result

    root_files = [i for i in root if i["type"] == "file"]
    root_dirs  = [i for i in root if i["type"] == "dir" and not i["name"].startswith(".")]
    root_names = {f["name"].lower() for f in root_files}

    # ── Signal 1: Root README (+30) ──
    has_readme = any(_is_readme(f["name"]) for f in root_files)
    result["scores"]["readme"] = 30 if has_readme else 0
    if not has_readme:
        result["fix_list"].append("📄 No root README found")

    # ── Signal 2: Subdir README coverage (+35) ──
    dirs_with_docs = 0
    for d in root_dirs[:20]:
        items = fetch_contents(repo, token, d["name"])
        if isinstance(items, list) and any(
            i["type"] == "file" and (_is_readme(i["name"]) or _is_md(i["name"]))
            for i in items
        ):
            dirs_with_docs += 1
        else:
            result["missing_dirs"].append(d["name"])

    total_dirs = max(min(len(root_dirs), 20), 1)
    result["scores"]["subdir"] = round(35 * dirs_with_docs / total_dirs)
    for d in result["missing_dirs"]:
        result["fix_list"].append(f"📂 /{d} is missing a README")

    # ── Signal 3: Comment density (+20) ──
    code_files = [f for f in root_files if _is_code(f["name"])][:5]
    total_lines = comment_lines = 0
    for f in code_files:
        raw = fetch_raw_file(f["download_url"], token)
        if raw:
            lines = raw.split("\n")
            total_lines += len(lines)
            comment_lines += sum(
                1 for line in lines if line.strip().startswith(COMMENT_STARTS)
            )

    if total_lines > 0:
        density = comment_lines / total_lines
        result["scores"]["comments"] = round(20 * min(1.0, density / 0.15))
        if density < 0.05:
            result["fix_list"].append("💬 Very low comment density in code files")
    else:
        result["scores"]["comments"] = 10

    # ── Signal 4: Config docs (+15) ──
    config_names = {".env.example", "docker-compose.yml", "makefile", "dockerfile"}
    found = [c for c in config_names if c in root_names]
    if any(i["name"].lower() == ".github" for i in root):
        found.append(".github")
    documented = [c for c in found if has_readme]
    result["scores"]["configs"] = round(15 * len(documented) / max(len(found), 1)) if found else 8

    result["total"] = sum(result["scores"].values())
    return result


def get_grade(total: int) -> tuple:
    """Returns (letter, color, label)."""
    for min_score, letter, color, label in GRADE_TIERS:
        if total >= min_score:
            return letter, color, label
    return "D", "#72243E", "Docs? What docs?"
