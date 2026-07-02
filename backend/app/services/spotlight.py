"""Spotlighting preprocessing (Layer 1).

Datamarking-style spotlighting: wrap untrusted content in explicit delimiters and
interleave a marker so a downstream LLM can reliably distinguish data from
instructions. This is a lightweight demo implementation; the production version
follows the datamarking/encoding strategies from the spotlighting literature.
"""

DELIMITER = "▁"  # marker interleaved between tokens


def spotlight(content: str, marker: str = DELIMITER) -> str:
    marked = marker.join(content.split(" "))
    return f"<<UNTRUSTED_DATA>>\n{marked}\n<</UNTRUSTED_DATA>>"
