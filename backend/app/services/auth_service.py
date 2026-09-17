from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.user import User


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_user_by_email(
    db: Session,
    email: str
):
    return db.query(User).filter(
        User.email == email
    ).first()


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str
):
    hashed_password = hash_password(password)

    new_user = User(
        name=name,
        email=email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )