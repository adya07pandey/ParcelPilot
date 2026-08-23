import argparse
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.database import engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import User  # noqa: E402


def set_user_password(email: str, password: str) -> None:
    with Session(engine) as db:
        user = db.scalar(select(User).where(User.email == email.lower()))
        if not user:
            raise SystemExit(f"No user found for {email}")
        user.password_hash = hash_password(password)
        db.commit()
        print(f"Updated password hash for {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set a user's password hash.")
    parser.add_argument("email")
    parser.add_argument("password")
    args = parser.parse_args()
    set_user_password(args.email, args.password)


if __name__ == "__main__":
    main()
