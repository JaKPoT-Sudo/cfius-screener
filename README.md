# CFIUS Screener

Screens proposed transactions (M&A, minority investments, joint ventures)
involving foreign persons for **CFIUS jurisdiction** and
**mandatory-declaration triggers** under 31 CFR Part 800, and shows its work:
every determination comes with the legal question, the facts that answered
it, and the regulation that drives it.

Part of a portfolio of AI-powered national security and defense compliance
tools (personnel security, acquisition intelligence, supply chain risk, ATO
compliance, influence-operations detection, hidden-ownership tracing — and
now foreign-investment screening).

## What it determines

For a given transaction the screener answers, in order:

1. **Is the acquirer a foreign person, and is the target a US business?**
2. **Is the target a TID US business?** (critical Technology, critical
   Infrastructure, or sensitive personal Data)
3. **Does CFIUS have jurisdiction?** Either a *covered control transaction*
   (majority stake or contractual control rights) or a *covered investment*
   (non-controlling stake in a TID business with a board seat, observer seat,
   non-public technical information access, or a substantive decision-making
   role).
4. **Is the acquirer an excepted investor?** (Australia, Canada, New Zealand,
   United Kingdom — simplified country-of-origin test)
5. **Is a declaration mandatory?** Two prongs: *substantial interest* (a
   foreign government holds ≥49% of the acquirer and the acquirer takes ≥25%
   of a TID business) and *critical technology* (the target makes
   export-controlled technology that would need a US authorization for the
   acquirer's home country).

Verdicts: **Not covered** · **Covered — voluntary filing available** ·
**Mandatory declaration required**.

## Design principle

> **The law is deterministic code. The facts are Claude's job. The human
> confirms in between.**

Whether a CFIUS filing is legally mandatory is a question of law with civil
penalties up to the value of the transaction. A language model never makes
that call here. The decision tree (`jurisdiction_engine.py`) is pure,
deterministic, table-driven-tested code; every threshold lives in
`config.py` with its citation. Claude's roles arrive in Milestone 2 —
parsing a plain-English deal description into structured facts (which a
human confirms before anything runs) and drafting the memo narrative *about*
the engine's conclusions.

## Milestones

- **Milestone 1 ✅ — the engine.** Deterministic Part 800 decision tree,
  structured-fact screening form, full findings trail with citations,
  seeded demo scenarios, table-driven test suite.
- **Milestone 2 — the Claude layer.** Plain-English intake (Claude Haiku
  parse → human confirmation screen), TID classification assist, screening
  memorandum narrative, PDF export (ReportLab).
- **Milestone 3 — the risk layer.** OFAC SDN screening of the foreign
  parties (rapidfuzz), threat / vulnerability / consequence risk scoring
  with config-driven weights.

## Demo scenarios (seeded automatically — all fictional)

| Deal | Branch it demonstrates |
|---|---|
| Golden Harbor Capital (China, 51% state-owned) takes 30% + board seat in Meridian Photonics (export-controlled optics) | **Mandatory** — both prongs trigger |
| Laurentide Pension Investment Board (Canada) buys 100% of TrueNorth Logistics Software (non-TID) | **Covered but voluntary** — control jurisdiction survives excepted-investor status; the filing obligation doesn't |
| Al Dhafra Strategic Investments (UAE sovereign fund) takes 28% non-controlling + board observer in HelixPrint Genomics (genetic data) | **Mandatory without control** — covered investment + substantial-interest prong |

## Run locally

```
pip install -r requirements.txt
uvicorn main:app --reload
```

Demo data seeds itself on startup (idempotent — Render's free tier wipes
SQLite on every cold start, so seeding runs every boot by design).

Tests: `py -m pytest`

## Honest limitations

- **Screening aid, not legal advice.** Real CFIUS determinations require
  counsel.
- All regulatory parameters and citations were encoded from the public text
  of 31 CFR Part 800 and **have not been verified by a practitioner**. Every
  value carries a VERIFY marker in `config.py`.
- The critical-technology test depends on an export-control classification
  (ITAR/EAR) that this tool asks the user to assert — a real determination
  needs export-control counsel.
- The excepted-investor test is simplified to country of origin; the real
  § 800.219 criteria examine the investor's ownership chain and compliance
  history.
- "Control" under CFIUS is functional and fact-specific; the engine covers
  the bright-line indicators (majority interest, contractual control
  rights), not every fact pattern.
- Real estate jurisdiction (31 CFR Part 802 — land near military
  installations) is out of scope.
- No authentication; demo data only — obviously fictional names throughout.
