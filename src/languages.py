"""Extension-based language detection.

GitHub's /languages endpoint uses Linguist, which weights by byte count and
gets fooled by Jupyter notebooks (a single .ipynb is huge JSON, so a repo
with one notebook + 100 SQL files reports as 'Jupyter Notebook'). This
module walks the git tree and ranks languages by *file count*, which
matches what a human reading the repo would call it.
"""
from dataclasses import dataclass


# Maps extension → display name. Lower-cased keys, leading dot stripped.
EXTENSION_MAP: dict[str, str] = {
    "sql":   "SQL",
    "py":    "Python",
    "ipynb": "Jupyter",
    "js":    "JavaScript",
    "ts":    "TypeScript",
    "tsx":   "TypeScript",
    "jsx":   "JavaScript",
    "java":  "Java",
    "kt":    "Kotlin",
    "go":    "Go",
    "rs":    "Rust",
    "rb":    "Ruby",
    "php":   "PHP",
    "cs":    "C#",
    "cpp":   "C++",
    "cc":    "C++",
    "c":     "C",
    "h":     "C/C++ header",
    "swift": "Swift",
    "scala": "Scala",
    "r":     "R",
    "sh":    "Shell",
    "bash":  "Shell",
    "ps1":   "PowerShell",
    "html":  "HTML",
    "css":   "CSS",
    "scss":  "Sass",
    "md":    "Markdown",
    "yml":   "YAML",
    "yaml":  "YAML",
    "json":  "JSON",
    "toml":  "TOML",
    "xml":   "XML",
    "dockerfile": "Dockerfile",
    "tf":    "Terraform",
}

# Ignore generated / vendored / config noise so the ranking reflects real work.
IGNORE_PREFIXES = (
    "node_modules/", "vendor/", "dist/", "build/", ".git/", "__pycache__/",
    ".venv/", "venv/", "env/", ".idea/", ".vscode/",
)
IGNORE_SUFFIXES = (".min.js", ".min.css", ".lock", ".map")


@dataclass(frozen=True)
class LanguageStat:
    name: str
    files: int
    pct:  float


class LanguageDetector:
    """Rank languages in a repo by file count, using extension lookup.

    Single responsibility: turn a list of tree-blob dicts (from
    GET /repos/.../git/trees) into a ranked list of LanguageStat. Doesn't
    fetch, doesn't render — pass in tree, get back stats.
    """

    def __init__(
        self,
        extension_map: dict[str, str] = EXTENSION_MAP,
        ignore_prefixes: tuple = IGNORE_PREFIXES,
        ignore_suffixes: tuple = IGNORE_SUFFIXES,
    ):
        self._ext_map  = extension_map
        self._prefixes = ignore_prefixes
        self._suffixes = ignore_suffixes

    def _should_skip(self, path: str) -> bool:
        if any(path.startswith(p) for p in self._prefixes):
            return True
        if any(path.endswith(s) for s in self._suffixes):
            return True
        return False

    def _classify(self, path: str) -> str | None:
        base = path.rsplit("/", 1)[-1].lower()
        if base == "dockerfile" or base.startswith("dockerfile."):
            return self._ext_map.get("dockerfile")
        if "." not in base:
            return None
        ext = base.rsplit(".", 1)[-1]
        return self._ext_map.get(ext)

    def rank(self, tree: list[dict]) -> list[LanguageStat]:
        counts: dict[str, int] = {}
        for blob in tree:
            path = blob.get("path", "")
            if not path or self._should_skip(path):
                continue
            lang = self._classify(path)
            if not lang:
                continue
            counts[lang] = counts.get(lang, 0) + 1

        total = sum(counts.values()) or 1
        ranked = sorted(counts.items(), key=lambda kv: -kv[1])
        return [LanguageStat(name=n, files=c, pct=c / total * 100) for n, c in ranked]

    def primary(self, tree: list[dict]) -> str:
        ranked = self.rank(tree)
        return ranked[0].name if ranked else "—"
