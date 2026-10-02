import getpass

from auth import hash_password
from database import SessionLocal, User, init_db


def main() -> None:
    name = input("User name: ").strip()
    password = getpass.getpass("Password: ")
    if not name or not password:
        raise SystemExit("User name and password are required.")

    init_db()
    if SessionLocal is None:
        raise SystemExit("DATABASE_URL is not configured.")
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.name == name).first()
        if existing:
            raise SystemExit(f"User '{name}' already exists.")
        db.add(User(name=name, password=hash_password(password)))
        db.commit()
        print(f"Created user '{name}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
