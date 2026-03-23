import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, String, Numeric, DateTime, Index, text
from sqlalchemy.dialects.postgresql import UUID

from app.infra.database.session import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    category = Column(String(100), nullable=False)
    merchant = Column(String(150), nullable=False)
    status = Column(String(50), nullable=False, default="completed")
    transaction_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(
        DateTime, nullable=False, server_default=text("NOW()"), default=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_transactions_category", "category"),
        Index("ix_transactions_date", "transaction_date"),
        Index("ix_transactions_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} amount={self.amount} category={self.category}>"
