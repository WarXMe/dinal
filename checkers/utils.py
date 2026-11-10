"""
╔══════════════════════════════════════════╗
║   CHECKER UTILS                         ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
"""
import re


def parse_combos(text: str) -> list[tuple[str, str]]:
    """Parse email:pass or email|pass combos. Returns deduplicated list."""
    seen   = set()
    combos = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # support : and | separators
        sep = None
        if "|" in line:
            sep = "|"
        elif ":" in line:
            sep = ":"
        else:
            continue
        parts = line.split(sep, 1)
        if len(parts) != 2:
            continue
        email, pw = parts[0].strip(), parts[1].strip()
        if not email or not pw:
            continue
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            continue
        key = f"{email.lower()}:{pw}"
        if key not in seen:
            seen.add(key)
            combos.append((email, pw))
    return combos


CHECKER_DISPLAY = {
    "xbox":      "🎮 Xbox Full Capture",
    "fortnite":  "🎯 Fortnite",
    "minecraft": "⛏️ Minecraft",
    "gamepass":  "🎫 Game Pass",
    "ea":        "🎮 EA",
}

CHECKER_EMOJI = {
    "xbox":      "🎮",
    "fortnite":  "🎯",
    "minecraft": "⛏️",
    "gamepass":  "🎫",
    "ea":        "🕹️",
}
