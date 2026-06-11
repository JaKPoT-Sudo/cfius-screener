"""screening_service.py — glue between the pure engine and the database.

jurisdiction_engine.py deliberately knows nothing about SQLAlchemy, and
models.py knows nothing about legal tests. This module is the only place the
two meet: run the facts through the engine, persist both, hand back the row.
Both the web form (main.py) and the demo seeder (seed_data.py) go through
this one function so a screening is created exactly the same way everywhere.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from sqlalchemy.orm import Session

from jurisdiction_engine import Determination, TransactionFacts, determine_jurisdiction
from models import Screening


def run_and_store(db: Session, facts: TransactionFacts, *, is_demo: bool = False) -> Screening:
    determination = determine_jurisdiction(facts)
    row = Screening(
        **facts.model_dump(exclude={"is_us_business"}),
        outcome=determination.outcome.value,
        covered_basis=determination.covered_basis,
        is_tid=determination.is_tid,
        tid_categories_json=json.dumps(determination.tid_categories),
        excepted_investor=determination.excepted_investor,
        mandatory_reasons_json=json.dumps(determination.mandatory_reasons),
        findings_json=json.dumps([asdict(f) for f in determination.findings]),
        is_demo=is_demo,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def findings_of(row: Screening) -> list[dict]:
    return json.loads(row.findings_json)


def tid_categories_of(row: Screening) -> list[str]:
    return json.loads(row.tid_categories_json)


def mandatory_reasons_of(row: Screening) -> list[str]:
    return json.loads(row.mandatory_reasons_json)
