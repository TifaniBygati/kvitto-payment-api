from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    create_engine,
    select,
    ForeignKey,
    JSON
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    Session,
)

PROJECT_DIR = Path(__file__).parent.parent.resolve()
DB_PATH = PROJECT_DIR / "database" / "database_tariffs.sqlite"

engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

def utc_now():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class Tariff(Base):
    __tablename__ = 'tariffs'

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(unique=True)

    price: Mapped[int] = mapped_column()

class Payment(Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    status: Mapped[str] = mapped_column(
        default = 'pending'
    )
    tariff_id: Mapped[int] = mapped_column(
        ForeignKey('tariffs.id'),

    )
    amount: Mapped[int] = mapped_column(

    )
    discount: Mapped[int] = mapped_column(
        default=0
    )
    method: Mapped[str] = mapped_column(

    )
    installment_months: Mapped[int | None] = mapped_column(
        nullable=True
    )
    schedule: Mapped[list[int] | None] = mapped_column(
        JSON,
        nullable=True,

    )
    email: Mapped[str] = mapped_column(

    )
    created_at : Mapped[datetime] = mapped_column(
        default=utc_now
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        nullable=True,
        unique=True
    )


def init_db():
    Base.metadata.create_all(engine)

    with Session(engine) as session:

        tariffs = (
            session.execute(
                select(Tariff)
            )
            .scalars().all()
        )

        if not tariffs:
            tariffs1 = Tariff(
                title = 'basic',
                price = 990000,
            )
            tariffs2 = Tariff(
                title = 'standard',
                price = 1990000,
            )
            tariffs3 = Tariff(
                title = 'premium',
                price = 2990000,
            )
            session.add_all([tariffs1, tariffs2, tariffs3])

            session.commit()

def get_tariffs_sqlite():
    with Session(engine) as session:
        tariffs = (
            session.execute(
                select(Tariff)
            )
            .scalars()
            .all()
        )
        return tariffs

def find_tariff_sqlite(tariff_id):
    with Session(engine) as session:
        tariff = (
            session.execute(
            select(Tariff)
            .where(Tariff.id == tariff_id)
            )
            .scalar_one_or_none()
        )

        return tariff

def save_payment_sqlite(payment):
    with Session(engine) as session:
        session.add(payment)
        session.commit()
        session.refresh(payment)
        return payment

def find_payment_by_idempotency_key_sqlite(idempotency_key):
    with Session(engine) as session:
        payment = (
            session.execute(
                select(Payment)
                .where(Payment.idempotency_key == idempotency_key)
            )
            .scalar_one_or_none()
        )
        return payment

def find_payment_by_id_sqlite(payment_id):
    with Session(engine) as session:
        payment = (
            session.execute(
                select(Payment)
                .where(Payment.id == payment_id)
            )
            .scalar_one_or_none()
        )
        return payment

def update_payment_status_sqlite(payment_id, payment_status):
    with Session(engine) as session:
        payment = (
            session.execute(
                select(Payment)
                .where(Payment.id == payment_id)
            )
            .scalar_one()
        )
        payment.status = payment_status

        session.commit()
