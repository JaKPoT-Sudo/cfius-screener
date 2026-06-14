"""
config.py — ALL regulatory parameters for CFIUS Screener.

Every number and list that controls a legal determination lives here, and no
logic lives here at all. The engine (jurisdiction_engine.py) applies these
values; it never defines its own. This is the same design rule SEAD 3 and
GhostTrace follow — when a regulation changes, you edit one file.

⚠ VERIFICATION NOTICE ⚠
Every threshold, list, and citation below was encoded from the public text of
31 CFR Part 800 (the CFIUS regulations) as best understood. None of it has
been verified by a CFIUS practitioner or export-control counsel. Before any
real-world use, every value marked VERIFY must be checked against the current
regulation. This is a portfolio screening aid, not legal advice.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# App identity + demo mode
# ---------------------------------------------------------------------------

APP_TITLE = "CFIUS Screener — Foreign Investment Transaction Screening"
DEMO_MODE = os.getenv("DEMO_MODE", "True").lower() in ("1", "true", "yes")
DEMO_BANNER = (
    "DEMO MODE — All transactions, companies, and investors are fictional. "
    "Screening output is a portfolio demonstration, not legal advice."
)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cfius_screener.db")

# ---------------------------------------------------------------------------
# Jurisdiction thresholds — 31 CFR Part 800
#
# WHY these specific numbers: they come straight from the regulation, not from
# judgment. 50% voting interest is the bright-line presumption of control
# (control can also exist below 50% through rights — handled as a separate
# input). 49% / 25% are the two prongs of the "substantial interest" mandatory
# declaration test.
# ---------------------------------------------------------------------------

# Majority voting interest → control, full stop. (VERIFY: § 800.208 also
# treats sub-majority interests as control when paired with governance rights;
# we capture that via the explicit control-rights input, not a percentage.)
CONTROL_MAJORITY_PCT = 50.0

# Mandatory declaration, "substantial interest" prong (VERIFY: § 800.401(b),
# § 800.244): a foreign government holds >= 49% of the acquirer, AND the
# acquirer obtains >= 25% voting interest in a TID US business.
SUBSTANTIAL_INTEREST_GOVT_PCT = 49.0
SUBSTANTIAL_INTEREST_ACQUISITION_PCT = 25.0

# Both substantial-interest thresholds are inclusive ("at least").
# Encoded as a constant so the test suite can assert the boundary explicitly.

# ---------------------------------------------------------------------------
# Excepted foreign states — § 800.218 (VERIFY)
#
# Investors from these states can qualify as "excepted investors"
# (§ 800.219), which removes covered-INVESTMENT jurisdiction and the
# mandatory-declaration requirements. It does NOT remove jurisdiction over
# covered CONTROL transactions — CFIUS can still review a Canadian company
# buying 100% of a US business; the buyer just isn't forced to file.
#
# SIMPLIFICATION (stated honestly in the UI): the real excepted-investor test
# has detailed criteria about the investor's own ownership chain and
# compliance history. We treat "organized in and principally owned from an
# excepted state" as qualifying. A real screen needs counsel for this step.
# ---------------------------------------------------------------------------

EXCEPTED_FOREIGN_STATES = (
    "Australia",
    "Canada",
    "New Zealand",
    "United Kingdom",
)

# ---------------------------------------------------------------------------
# TID US business definitions — § 800.248 (VERIFY)
# TID = critical Technology, critical Infrastructure, sensitive personal Data.
# ---------------------------------------------------------------------------

# Sensitive personal data (VERIFY: § 800.241): identifiable data in the
# enumerated categories maintained or collected on at least this many
# individuals — EXCEPT genetic data, which qualifies at any volume.
SENSITIVE_DATA_INDIVIDUALS_THRESHOLD = 1_000_000

# The enumerated sensitive-data categories (VERIFY against § 800.241 —
# encoded from memory of the regulation; used for form help text and the
# Milestone 2 Claude classifier, not for the determination itself).
SENSITIVE_DATA_CATEGORIES = (
    "Financial distress or hardship data",
    "Consumer report data",
    "Health insurance / long-term care / professional liability application data",
    "Physical, mental, or psychological health condition data",
    "Non-public electronic communications (email, messaging, chat)",
    "Geolocation data",
    "Biometric enrollment data",
    "Government ID or security clearance status data",
    "Security clearance or government employment application data",
    "Genetic test results (qualifies at ANY volume)",
)

# Representative critical-infrastructure functions (VERIFY: the authoritative
# list is Appendix A to Part 800 — 28 specific categories, each tied to a
# specific function like "own or operate". This subset drives form help text;
# the determination input is a simple yes/no the user asserts.)
CRITICAL_INFRASTRUCTURE_EXAMPLES = (
    "Internet protocol networks / internet exchange points",
    "Telecommunications backbone or submarine cable systems",
    "Industrial control systems for critical manufacturing",
    "Electric power generation, transmission, or distribution serving military installations",
    "Crude oil storage or LNG import/export terminals",
    "Financial market utilities / interbank clearing",
    "Rail lines and airports designated as strategic",
    "Public water systems serving large populations",
    "Manufacturing of items on defense-critical supply lists",
)

# ---------------------------------------------------------------------------
# Filing timelines — Part 800 Subparts D & E (VERIFY)
# Shown in the result UI so a deal team understands the clock they'd be on.
# ---------------------------------------------------------------------------

DECLARATION_ASSESSMENT_DAYS = 30   # short-form mandatory/voluntary declaration
NOTICE_REVIEW_DAYS = 45            # full voluntary notice, initial review
NOTICE_INVESTIGATION_DAYS = 45     # follow-on investigation if opened

# ---------------------------------------------------------------------------
# Citations — every engine finding points at one of these.
#
# WHY a dict instead of inline strings: the result page renders the citation
# next to every determination, and the README's verification table is built
# from this single source. All section numbers are VERIFY — encoded from
# memory of 31 CFR Part 800's structure.
# ---------------------------------------------------------------------------

CITATIONS = {
    "foreign_person": "31 CFR § 800.224",
    "us_business": "31 CFR § 800.252",
    "control": "31 CFR § 800.208",
    "covered_control_transaction": "31 CFR § 800.210",
    "covered_investment": "31 CFR § 800.211",
    "tid_us_business": "31 CFR § 800.248",
    "critical_technologies": "31 CFR § 800.215",
    "critical_infrastructure": "Appendix A to 31 CFR Part 800",
    "sensitive_personal_data": "31 CFR § 800.241",
    "substantial_interest": "31 CFR § 800.244",
    "excepted_foreign_state": "31 CFR § 800.218",
    "excepted_investor": "31 CFR § 800.219",
    "mandatory_declaration": "31 CFR § 800.401",
    "declaration_timeline": "31 CFR Part 800, Subpart D",
    "notice_timeline": "31 CFR Part 800, Subpart E",
}

VERIFICATION_DISCLAIMER = (
    "All regulatory parameters and citations encoded from the public text of "
    "31 CFR Part 800 and NOT verified by counsel. Screening aid only — not "
    "legal advice. Real CFIUS determinations require a qualified attorney."
)

# ---------------------------------------------------------------------------
# OFAC SDN screening — Milestone 3
#
# Source URLs from OFAC's public download page. Verified live June 2026.
# token_sort_ratio ≥ OFAC_MATCH_THRESHOLD is flagged as a candidate hit;
# ALL hits require human verification — fuzzy name matching cannot confirm
# legal identity.
# ---------------------------------------------------------------------------

OFAC_SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
OFAC_SDN_ALT_URL = "https://www.treasury.gov/ofac/downloads/alt.csv"
OFAC_MATCH_THRESHOLD = 90  # rapidfuzz token_sort_ratio — VERIFY: GhostTrace uses 90

# ---------------------------------------------------------------------------
# National security risk scoring — Milestone 3
#
# WHY: the jurisdictional determination (covered / mandatory) answers a legal
# question. The TVC risk score answers a separate analytic question: "how
# serious is this deal from a national security perspective?" The two scores
# can diverge — a NOT_COVERED deal can still carry high risk, and a MANDATORY
# deal involving an excepted ally carries less risk than the mandatory label
# alone suggests.
#
# Three dimensions — Threat / Vulnerability / Consequence:
#   THREAT      — How adversarial is the acquirer and its principals?
#   VULNERABILITY — How much sensitive access does this deal confer?
#   CONSEQUENCE — How bad would exploitation be at a national level?
#
# Weights are judgment calls informed by public CFIUS guidance and NSS
# priorities. ALL marked VERIFY — not validated by security professionals.
# ---------------------------------------------------------------------------

# Countries treated as high-threat in the US national security framework
# (VERIFY: aligned with EO 13873, EO 13884, EO 14038 country designations
# and CFIUS Committee practice). Common alias forms included for matching.
RISK_HIGH_RISK_COUNTRIES = (
    "China", "Prc",
    "Russia",
    "Iran",
    "North Korea", "Dprk",
    "Belarus",
    "Venezuela",
    "Cuba",
    "Syria",
)

# SOE / SWF threshold — foreign govt ownership % at which we flag the
# acquirer as effectively state-controlled. Using 49% to match the
# SUBSTANTIAL_INTEREST_GOVT_PCT threshold (already in regulations).
RISK_SOE_THRESHOLD = 49.0

# --- Threat weights ---
RISK_WEIGHT_HIGH_RISK_COUNTRY = 30   # acquirer is from a designated adversary state
RISK_WEIGHT_SOE_ACQUIRER = 20        # acquirer is ≥49% govt-owned (SOE / SWF)

# --- Vulnerability weights ---
RISK_WEIGHT_CRITICAL_TECH = 20       # target produces export-controlled technology
RISK_WEIGHT_EXPORT_AUTH = 15         # export to acquirer's country needs US authorization
RISK_WEIGHT_CRITICAL_INFRA = 20      # target owns or operates critical infrastructure
RISK_WEIGHT_SENSITIVE_DATA = 15      # target holds SPD on >1M individuals
RISK_WEIGHT_CONTROL_ACQUIRED = 10    # transaction confers control of the US business
RISK_WEIGHT_BOARD_ACCESS = 8         # acquirer gets board seat or observer seat
RISK_WEIGHT_TECH_INFO_ACCESS = 8     # acquirer gets non-public technical info access
RISK_WEIGHT_DECISION_ROLE = 6        # acquirer gets substantive decision-making role

# --- Consequence weights ---
RISK_WEIGHT_TID_CLASSIFICATION = 15  # TID status = CFIUS-recognized sensitive business
RISK_WEIGHT_MANDATORY_FILING = 10    # mandatory declaration = legally flagged severity
RISK_WEIGHT_TECH_TRANSFER = 15       # critical tech + export auth = direct transfer risk
RISK_WEIGHT_INFRA_DISRUPTION = 15    # critical infra acquisition = disruption potential
RISK_WEIGHT_DATA_EXPLOITATION = 10   # mass SPD = adversarial exploitation risk

# Score tier thresholds (total out of 100) — VERIFY
RISK_TIER_CRITICAL = 75
RISK_TIER_HIGH = 50
RISK_TIER_MEDIUM = 25
