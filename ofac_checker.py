"""ofac_checker.py — OFAC SDN fuzzy-match screening.

Ported from GhostTrace with CFIUS-specific simplifications:
- Screens a single acquirer name rather than a whole entity network
- Inline _normalize() so there's no entity_resolver dependency
- Same matching logic: rapidfuzz token_sort_ratio >= OFAC_MATCH_THRESHOLD

Downloads sdn.csv + alt.csv on the first screen_entities() call per process
and caches them in memory. On Render free tier every cold start is a fresh
process, so the download happens at most once per session (~3-5 seconds).

ALL hits are candidates — fuzzy name matching cannot confirm legal identity.
Human verification is required before any compliance action.
"""

from __future__ import annotations

import csv
import io
import logging
import urllib.request
from typing import NamedTuple

from rapidfuzz import fuzz
from rapidfuzz import process as rfprocess

from config import OFAC_MATCH_THRESHOLD, OFAC_SDN_ALT_URL, OFAC_SDN_CSV_URL

logger = logging.getLogger(__name__)

# Corporate suffixes stripped during name normalization
_CORP_SUFFIXES = frozenset({
    "inc", "llc", "ltd", "corp", "co", "company", "limited", "group",
    "holdings", "pte", "sa", "bv", "ag", "plc", "pty", "gmbh",
    "lp", "llp", "lllp", "jsc", "ooo", "pjsc", "sas", "spa",
})

# Module-level cache — populated on first screen_entities() call
_sdn_entries: list[tuple[str, str, str, str]] | None = None


class OFACHit(NamedTuple):
    entity_name: str   # name submitted for screening
    sdn_name: str      # matching SDN list name
    score: int         # 0-100 fuzzy similarity
    sdn_program: str   # sanctions program (e.g. SDGT, IRAN, RUSSIA)
    sdn_type: str      # individual | entity | vessel | aircraft | alias


def _normalize(name: str) -> str:
    """Lowercase, strip punctuation, drop leading 'the' and corporate suffixes."""
    cleaned = "".join(ch if ch.isalnum() or ch == " " else " " for ch in name.lower())
    tokens = cleaned.split()
    if tokens and tokens[0] == "the":
        tokens = tokens[1:]
    while tokens and tokens[-1] in _CORP_SUFFIXES:
        tokens = tokens[:-1]
    return " ".join(tokens)


def _fetch_csv(url: str) -> list[list[str]]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CFIUS-Screener portfolio tool (jak.potvin@gmail.com)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(content)))


def _load() -> list[tuple[str, str, str, str]]:
    """Download and parse SDN primary names and aliases into (norm, original, program, type)."""
    entries: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()

    # Primary names from sdn.csv: entry_num, name, type, program(s), ...
    try:
        for row in _fetch_csv(OFAC_SDN_CSV_URL):
            if len(row) < 2:
                continue
            name = row[1].strip().strip('"')
            program = row[3].strip().strip('"') if len(row) > 3 else ""
            sdn_type = row[2].strip().strip('"').lower() if len(row) > 2 else "entity"
            if not name or name in ("-0-", "SDN Name", "Name"):
                continue
            norm = _normalize(name)
            if norm and norm not in seen:
                seen.add(norm)
                entries.append((norm, name, program, sdn_type))
        logger.info("OFAC SDN primary: %d names loaded", len(entries))
    except Exception as exc:
        logger.warning("OFAC SDN primary list unavailable: %s", exc)

    # Aliases from alt.csv: entry_num, strength, aka_type, alternate_name, ...
    before = len(entries)
    try:
        for row in _fetch_csv(OFAC_SDN_ALT_URL):
            if len(row) < 4:
                continue
            name = row[3].strip().strip('"')
            if not name or name in ("-0-", "Alternate Name", "Alternate name"):
                continue
            norm = _normalize(name)
            if norm and norm not in seen:
                seen.add(norm)
                entries.append((norm, name, "", "alias"))
        logger.info("OFAC SDN aliases: %d additional loaded", len(entries) - before)
    except Exception as exc:
        logger.warning("OFAC SDN alias list unavailable: %s", exc)

    return entries


def _ensure_loaded() -> list[tuple[str, str, str, str]]:
    global _sdn_entries
    if _sdn_entries is None:
        _sdn_entries = _load()
    return _sdn_entries


def screen_entities(entity_names: list[str]) -> list[OFACHit]:
    """Fuzzy-match entity names against the OFAC SDN list.

    Returns OFACHit records for every name/SDN pair whose token_sort_ratio
    meets OFAC_MATCH_THRESHOLD. Results are candidates — human verification
    required before any compliance action.
    """
    entries = _ensure_loaded()
    if not entries:
        return []

    sdn_norm_names = [e[0] for e in entries]
    hits: list[OFACHit] = []

    for entity_name in entity_names:
        norm = _normalize(entity_name)
        if not norm:
            continue
        results = rfprocess.extract(
            norm,
            sdn_norm_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=OFAC_MATCH_THRESHOLD,
            limit=3,
        )
        for _matched_norm, score, idx in results:
            _, original, program, sdn_type = entries[idx]
            hits.append(OFACHit(
                entity_name=entity_name,
                sdn_name=original,
                score=int(score),
                sdn_program=program,
                sdn_type=sdn_type,
            ))

    return hits


def reset_cache() -> None:
    """Clear the in-memory SDN cache. Used in tests to inject mock data."""
    global _sdn_entries
    _sdn_entries = None
