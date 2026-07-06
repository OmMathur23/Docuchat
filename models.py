from sqlalchemy.orm import Mapped, mapped_column
from database import Base
from sqlalchemy import ForeignKey

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class User(Base):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True)
    email : Mapped[str] = mapped_column(unique = True)
    hashed_password : Mapped[str] 