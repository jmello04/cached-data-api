import os
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.infra.database.models import Transaction
from app.infra.database.session import Base

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

MERCHANTS = {
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


def generate_transaction(date_offset_days: int) -> dict:
    category = random.choice(CATEGORIES)
    merchant = random.choice(MERCHANTS[category])
    base_amounts = {
        "Alimentação": (15, 800),
        "Transporte": (8, 350),
        "Saúde": (20, 2500),
        "Educação": (29, 1500),
        "Tecnologia": (50, 8000),
        "Entretenimento": (10, 600),
        "Vestuário": (30, 1200),
        "Habitação": (150, 5000),
        "Investimento": (100, 50000),
        "Serviços": (25, 3000),
    }
    low, high = base_amounts[category]
    amount = round(random.uniform(low, high), 2)
    status = random.choice(STATUSES)
    txn_date = datetime.utcnow() - timedelta(
        days=random.randint(0, date_offset_days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return {
        "description": random.choice(DESCRIPTIONS),
        "amount": Decimal(str(amount)),
        "category": category,
        "merchant": merchant,
        "status": status,
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

    print(f"Iniciando seed com {total_records} transações...")

    batch_size = 500
    transactions = []

    for i in range(total_records):
        data = generate_transaction(date_offset_days=365)
        transactions.append(Transaction(**data))

        if len(transactions) >= batch_size:
            session.bulk_save_objects(transactions)
            session.commit()
            transactions = []
            print(f"  → {i + 1}/{total_records} registros inseridos")

    if transactions:
        session.bulk_save_objects(transactions)
        session.commit()

    final_count = session.query(Transaction).count()
    session.close()
    print(f"\nSeed concluído. Total de registros no banco: {final_count}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    seed_database(total_records=count)
