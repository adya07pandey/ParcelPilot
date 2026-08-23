from __future__ import annotations

from sqlalchemy import inspect, text

from app.core.database import SessionLocal, engine
from app.models import Ticket
from app.tickets.classification import infer_ticket_terms


def ensure_subcategory_column() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("tickets")}
    if "subcategory" in columns:
        return
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE tickets ADD COLUMN subcategory VARCHAR(128)"))


def main() -> None:
    ensure_subcategory_column()
    db = SessionLocal()
    try:
        updated = 0
        for ticket in db.query(Ticket).all():
            category, subcategory = infer_ticket_terms(ticket)
            if ticket.category != category or ticket.subcategory != subcategory:
                ticket.category = category
                ticket.subcategory = subcategory
                updated += 1
        db.commit()
        print(f"updated {updated} tickets")
    finally:
        db.close()


if __name__ == "__main__":
    main()
