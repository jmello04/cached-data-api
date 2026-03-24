import os
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.infra.database.base import Base
from app.infra.database.models import Transaction  # noqa: F401 — registra no metadata

CATEGORIES = [
    "Alimentação",
    "Transporte",
    "Saúde",
    "Educação",
    "Tecnologia",
    "Entretenimento",
    "Vestuário",
    "Habitação",
    "Investimento",
    "Serviços",
]

MERCHANTS: dict[str, list[str]] = {
    "Alimentação": ["Supermercado Extra", "Pão de Açúcar", "iFood", "McDonald's", "Rappi", "Subway"],
    "Transporte": ["Uber", "99Taxi", "Shell", "Petrobras", "Posto BR", "BRT Rio"],
    "Saúde": ["Drogasil", "Ultrafarma", "Hospital Albert Einstein", "Clínica SIM", "UltraGenyx"],
    "Educação": ["Udemy", "Alura", "Coursera", "Descomplica", "FIAP", "FGV Online"],
    "Tecnologia": ["Amazon AWS", "Google Cloud", "Apple Store", "Samsung", "Kabum", "Pichau"],
    "Entretenimento": ["Netflix", "Spotify", "Steam", "Cinema Cinemark", "Ingresso.com", "Xbox"],
    "Vestuário": ["Renner", "Zara", "Riachuelo", "C&A", "Shein", "Nike Store"],
    "Habitação": ["OLX", "QuintoAndar", "Vivo Fibra", "Enel", "Comgás", "SABESP"],
    "Investimento": ["XP Investimentos", "Rico", "NuInvest", "Toro Investimentos", "Clear", "BTG"],
    "Serviços": ["Contabilizei", "99freelas", "GetNinjas", "Enjoei", "Mercado Livre", "Amazon"],
}

AMOUNT_RANGES: dict[str, tuple[float, float]] = {
    "Alimentação": (15.0, 800.0),
    "Transporte": (8.0, 350.0),
    "Saúde": (20.0, 2500.0),
    "Educação": (29.0, 1500.0),
    "Tecnologia": (50.0, 8000.0),
    "Entretenimento": (10.0, 600.0),
    "Vestuário": (30.0, 1200.0),
    "Habitação": (150.0, 5000.0),
    "Investimento": (100.0, 50000.0),
    "Serviços": (25.0, 3000.0),
}

STATUSES = ["completed", "completed", "completed", "pending", "refunded"]

DESCRIPTIONS = [
    "Compra realizada",
    "Pagamento mensal",
    "Assinatura recorrente",
    "Compra online",
    "Pagamento parcelado",
    "Transferência",
    "Débito automático",
    "Compra via app",
]


def _generate_transaction(max_days_ago: int = 365) -> dict:
    category = random.choice(CATEGORIES)
    merchant = random.choice(MERCHANTS[category])
    low, high = AMOUNT_RANGES[category]
    amount = round(random.uniform(low, high), 2)
    txn_date = datetime.now(timezone.utc) - timedelta(
        days=random.randint(0, max_days_ago),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return {
        "description": random.choice(DESCRIPTIONS),
        "amount": Decimal(str(amount)),
        "category": category,
        "merchant": merchant,
        "status": random.choice(STATUSES),
        "transaction_date": txn_date,
    }


def seed_database(total_records: int = 5000) -> None:
    engine = create_engine(settings.DATABASE_URL_SYNC, echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    existing = session.query(Transaction).count()
    if existing >= total_records:
        print(f"Banco já possui {existing} registros. Seed ignorado.")
        session.close()
        return

    print(f"Iniciando seed com {total_records} transações financeiras...")

    batch_size = 500
    batch: list[Transaction] = []

    for i in range(1, total_records + 1):
        batch.append(Transaction(**_generate_transaction()))

        if len(batch) >= batch_size:
            session.bulk_save_objects(batch)
            session.commit()
            batch = []
            print(f"  → {i}/{total_records} registros inseridos")

    if batch:
        session.bulk_save_objects(batch)
        session.commit()

    final_count = session.query(Transaction).count()
    session.close()

    print(f"\nSeed concluído com sucesso.")
    print(f"Total de registros no banco: {final_count}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    seed_database(total_records=count)
