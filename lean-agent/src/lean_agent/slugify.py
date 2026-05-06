import re
import unicodedata


def slugify_idea(text: str, max_words: int = 8) -> str:
    """Turn an idea description into a filesystem-safe folder slug."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)
    words = cleaned.split()
    truncated = words[:max_words]
    return "-".join(truncated)
