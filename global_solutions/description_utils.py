"""Helpers for splitting video descriptions on detail pages."""

from __future__ import annotations

import re

from django.utils.html import strip_tags

DEFAULT_SIDEBAR_WORD_LIMIT = 60


def split_description_text(text: str, word_limit: int = DEFAULT_SIDEBAR_WORD_LIMIT) -> tuple[str, str]:
    """
    Return (sidebar_lead, remainder) for plain-text descriptions.

    Strips HTML first so tags do not affect word counts or display.
    """
    plain = strip_tags(text or "").strip()
    if not plain:
        return "", ""

    word_end = 0
    count = 0
    for match in re.finditer(r"\S+", plain):
        count += 1
        if count == word_limit:
            word_end = match.end()
            break

    if word_end == 0:
        return plain, ""

    return plain[:word_end].rstrip(), plain[word_end:].lstrip()
