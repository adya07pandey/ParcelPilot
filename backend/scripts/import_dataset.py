import sys
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.database import Base, engine  # noqa: E402
from app.models import Account, Escalation, Order, ShipmentEvent, Ticket, TicketEvent, User  # noqa: E402


DATASET = ROOT.parent / "data" / "ParcelPilot_full_dataset.xlsx"


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    return value


def rows_from_sheet(workbook: Path, sheet: str) -> list[dict[str, Any]]:
    df = pd.read_excel(workbook, sheet_name=sheet)
    return [{key: clean_value(value) for key, value in row.items()} for row in df.to_dict("records")]


def upsert_rows(db: Session, model, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    table = model.__table__
    stmt = pg_insert(table).values(rows)
    update_cols = {column.name: stmt.excluded[column.name] for column in table.columns if not column.primary_key}
    db.execute(stmt.on_conflict_do_update(index_elements=[column.name for column in table.primary_key], set_=update_cols))


def import_dataset(workbook: Path) -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        upsert_rows(db, Account, rows_from_sheet(workbook, "accounts"))
        upsert_rows(db, User, rows_from_sheet(workbook, "users"))
        upsert_rows(db, Order, rows_from_sheet(workbook, "orders"))
        upsert_rows(db, Ticket, rows_from_sheet(workbook, "tickets"))
        upsert_rows(db, ShipmentEvent, rows_from_sheet(workbook, "shipment_events"))
        upsert_rows(db, TicketEvent, rows_from_sheet(workbook, "ticket_events"))
        upsert_rows(db, Escalation, rows_from_sheet(workbook, "escalations"))
        db.commit()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Import ParcelPilot workbook data into PostgreSQL/Neon.")
    parser.add_argument("--workbook", default=str(DATASET), help="Path to ParcelPilot_full_dataset.xlsx")
    args = parser.parse_args()
    import_dataset(Path(args.workbook))
    print("Imported ParcelPilot dataset.")


if __name__ == "__main__":
    main()
