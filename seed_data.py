"""seed_data.py — fictional demo transactions, loaded on every startup.

Render's free tier wipes SQLite on every cold start, so this runs from the
lifespan handler and must be idempotent. Every name is obviously fictional.

The three scenarios are chosen to exercise the three main branches of the
decision tree — including one where the answer is "no filing required",
because a screener that only ever says YES is not credible:

1. MANDATORY (both prongs)  — Chinese-state-backed fund takes 30% + board
   seat in an export-controlled photonics maker.
2. COVERED BUT VOLUNTARY    — Canadian pension fund buys 100% of a non-TID
   logistics-software company (excepted investor).
3. MANDATORY (substantial-interest prong only) — UAE sovereign wealth fund
   takes 28% non-controlling + board observer in a genetic-testing company.
   The subtle one: no control, but covered investment + mandatory filing.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from jurisdiction_engine import TransactionFacts
from models import Screening
from screening_service import run_and_store

_SEED_SCENARIOS = [
    TransactionFacts(
        us_business_name="Meridian Photonics Corporation",
        us_business_description=(
            "Tempe, Arizona manufacturer of semiconductor inspection optics "
            "and EUV metrology components. Several product lines are "
            "controlled under the EAR (Commerce Control List Category 3) and "
            "require a license for export to China."
        ),
        acquirer_name="Golden Harbor Capital Pte. Ltd.",
        acquirer_country="China",
        foreign_govt_ownership_pct=51.0,
        voting_interest_pct=30.0,
        contractual_control_rights=False,
        board_seat=True,
        access_nonpublic_tech_info=True,
        produces_critical_tech=True,
        export_authorization_required=True,
    ),
    TransactionFacts(
        us_business_name="TrueNorth Logistics Software LLC",
        us_business_description=(
            "Columbus, Ohio SaaS provider of commercial freight scheduling "
            "and warehouse management software. No government customers, no "
            "export-controlled technology, no sensitive personal data."
        ),
        acquirer_name="Laurentide Pension Investment Board",
        acquirer_country="Canada",
        foreign_govt_ownership_pct=0.0,
        voting_interest_pct=100.0,
    ),
    TransactionFacts(
        us_business_name="HelixPrint Genomics Inc.",
        us_business_description=(
            "San Diego direct-to-consumer genetic testing company holding "
            "genetic test results and identifiable health data on roughly "
            "2.1 million US customers."
        ),
        acquirer_name="Al Dhafra Strategic Investments PJSC",
        acquirer_country="United Arab Emirates",
        foreign_govt_ownership_pct=100.0,
        voting_interest_pct=28.0,
        board_observer=True,
        sensitive_personal_data=True,
    ),
]


def load_seed_data(db: Session) -> None:
    """Idempotent: seeds only when no demo screenings exist."""
    if db.query(Screening).filter(Screening.is_demo.is_(True)).count() > 0:
        return
    for facts in _SEED_SCENARIOS:
        run_and_store(db, facts, is_demo=True)
