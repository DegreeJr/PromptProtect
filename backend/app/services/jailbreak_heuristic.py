"""Direct-jailbreak heuristic (Layer 3).

The ML classifier (`services/classifier.py`) is fine-tuned on BIPIA, whose
attack distribution is *indirect* prompt injection (malicious instructions
embedded in retrieved/external content, typically aimed at data exfiltration or
unauthorized actions). It generalizes poorly to *direct* jailbreak phrasing such
as "ignore all previous instructions" or "you are now DAN", scoring them benign
with high confidence.

This layer closes that gap with a small, curated set of regex patterns covering
common English and Indonesian jailbreak phrasings. It is intentionally
conservative — patterns target imperative override phrases, not individual
keywords — so that ordinary benign text does not trigger false positives.

Combined with the ML classifier via OR logic in `api/analyze.py`: if either the
model or this layer flags the content, the final verdict is injection.
"""

import re

# Each entry: (compiled_pattern, short_label). Patterns are matched
# case-insensitively against the raw content. Kept deliberately specific to
# imperative override / role-reset phrasing to minimize false positives.
_RAW_PATTERNS: list[tuple[str, str]] = [
    # --- English: instruction override ---
    (r"\bignore\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above|earlier)\s+(?:instructions?|prompts?|context|rules?)",
     "ignore-previous-instructions"),
    (r"\bdisregard\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above|earlier|any)\s+(?:instructions?|prompts?|context|rules?)",
     "disregard-previous-instructions"),
    (r"\bforget\s+(?:everything|all|your\s+instructions?|prior\s+context|previous\s+(?:instructions?|context))",
     "forget-instructions"),
    (r"\boverride\s+(?:all\s+)?(?:previous|prior|system)\s+(?:instructions?|rules?|settings?)",
     "override-instructions"),

    # --- English: role / mode manipulation ---
    (r"\byou\s+are\s+now\s+(?:dan\b|in\s+developer\s+mode|unrestricted|jailbroken|an?\s+unrestricted)",
     "you-are-now-role"),
    (r"\b(?:act|pretend|behave)\s+as\s+(?:if\s+you\s+are\s+)?(?:dan\b|an?\s+unrestricted|a\s+jailbroken)",
     "act-as-unrestricted"),
    (r"\bdan\s+mode\b",  # DAN
     "dan-mode"),
    # "developer mode" only when it's being *activated/entered*, not merely mentioned
    # (avoids FPs like "the developer mode of this camera ...").
    (r"\b(?:enter|entering|enable|enabling|activate|activating|switch(?:ing)?\s+to|into|in|now\s+in)\s+developer\s+mode\b",
     "developer-mode"),
    # "system override" as a directive (colon/imperative), not a passing mention.
    (r"\bsystem\s+override\s*[:\-]|\b(?:initiate|activate|engage|enable)\s+system\s+override\b",
     "system-override"),
    # "without restrictions/filters/..." only when tied to an imperative to act/respond.
    (r"\b(?:respond|answer|reply|act|behave|operate|comply|do\s+anything)\b[^.?!]*\bwithout\s+(?:any\s+)?(?:restrictions?|filters?|limitations?|rules?|censorship|guidelines?)\b",
     "without-restrictions"),
    (r"\bbypass\s+(?:all\s+)?(?:your\s+)?(?:filters?|restrictions?|safety|guidelines?|rules?)",
     "bypass-safety"),
    (r"\b(?:reveal|show|print|repeat|leak)\s+(?:me\s+)?(?:your\s+|the\s+)?(?:system\s+prompt|initial\s+instructions?|hidden\s+(?:prompt|instructions?))",
     "reveal-system-prompt"),

    # --- Indonesian: instruction override ---
    (r"\babaikan\s+(?:semua\s+)?(?:instruksi|perintah|aturan|petunjuk|arahan)\s+(?:sebelumnya|sebelum\s+ini|di\s*atas|terdahulu)?",
     "abaikan-instruksi"),
    (r"\blupakan\s+(?:semua\s+)?(?:instruksi|perintah|aturan|petunjuk|konteks)(?:\s+(?:sebelumnya|sebelum\s+ini))?",
     "lupakan-perintah"),
    (r"\bhiraukan\s+(?:semua\s+)?(?:instruksi|perintah|aturan)\s+(?:sebelumnya|di\s*atas|terdahulu)?",
     "hiraukan-instruksi"),
    (r"\b(?:jangan\s+hiraukan|abaikan)\s+(?:instruksi|perintah|aturan)\b",
     "id-abaikan-generic"),

    # --- Indonesian: role / mode manipulation ---
    (r"\b(?:kamu|anda)\s+(?:sekarang|kini)\s+(?:adalah\s+)?(?:dan\b|mode\s+pengembang|tanpa\s+batas(?:an)?|tidak\s+terbatas)",
     "id-kamu-sekarang-role"),
    (r"\b(?:berperan|berpura-pura|bertindak)\s+(?:sebagai|seolah)\s+(?:dan\b|tanpa\s+batas(?:an)?|tidak\s+terbatas)",
     "id-berperan-tanpa-batas"),
    # "tanpa batasan/aturan/..." hanya jika terikat perintah bertindak/menjawab.
    (r"\b(?:jawab|menjawab|balas|bertindak|berperilaku|beroperasi|lakukan\s+apa\s*pun|respons?)\b[^.?!]*\btanpa\s+(?:batasan|aturan|filter|larangan|pembatasan|sensor)\b",
     "id-tanpa-batasan"),
    # "mode pengembang" hanya saat diaktifkan/dimasuki, bukan sekadar disebut.
    (r"\b(?:masuk(?:i)?|aktifkan|mengaktifkan|beralih\s+ke|ke|dalam|sekarang\s+(?:dalam|di))\s+mode\s+pengembang\b",
     "id-mode-pengembang"),
    (r"\b(?:tampilkan|tunjukkan|ungkapkan|bocorkan)\s+(?:prompt\s+sistem|instruksi\s+(?:awal|tersembunyi|sistem))",
     "id-ungkap-prompt-sistem"),
]

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pat, re.IGNORECASE), label) for pat, label in _RAW_PATTERNS
]


def detect(content: str) -> tuple[bool, list[str]]:
    """Return (is_jailbreak, matched_pattern_labels).

    is_jailbreak is True if any curated jailbreak pattern matches. The list of
    matched labels is returned for transparency/explainability.
    """
    matched = [label for pattern, label in _PATTERNS if pattern.search(content)]
    return (len(matched) > 0), matched
