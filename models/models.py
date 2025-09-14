from sqlalchemy import String, Integer, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False, index=True)
    #one user has many transactions, collection on the parent side
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user"
    )

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False, index=True)
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="product"
    )

#Transaction acts as a JOINT table between User and Product, many to many relationship
class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    #better to use uuid.UUID, rather than str, as it gives beter type safety, validation, and efficiency and ensure globally unique ID
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        #postgreSQL UUID column type, and as_uuid=True, SqlAlchemy will automatically convert DB values into real Python uuid.UUID objects
        PG_UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        #to avoid accidental data loss, using with RESTRICT, instead of using Cascade
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        #to avoid accidental data loss, using with RESTRICT, instead of using Cascade
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    transaction_amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)

    #on the child table (Transaction), the reference to its parent (user, product) is always a single object, not a list, so no need for list[], it's a scalar ref
    user: Mapped["User"] = relationship(back_populates="transactions")
    product: Mapped["Product"] = relationship(back_populates="transactions")

    # __table_args__ = (
    #     Index("ix_transactions_user_ts", "user_id", "timestamp"),
    # )
    #composite index on (user_id, timestamp) and (product_id, timestamp) to optimise queries filtering by user or product within a time range
    __table_args__ = (
        Index("ix_transactions_user_ts", "user_id", "timestamp"),
        Index("ix_transactions_product_ts", "product_id", "timestamp"),
    )
