from datetime import datetime
from typing import Any, Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _fetch_all_transactions(self) -> pd.DataFrame:
        query = text(
            """
            SELECT
                id,
                description,
                amount::float AS amount,
                category,
                merchant,
                status,
                transaction_date
            FROM transactions
            ORDER BY transaction_date DESC
            """
        )
        result = await self.db.execute(query)
        rows = result.fetchall()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=result.keys())

    async def get_summary_report(self) -> dict[str, Any]:
        df = await self._fetch_all_transactions()
        if df.empty:
            return {"message": "Sem dados disponíveis", "total_records": 0}

        summary = {
            "total_records": int(len(df)),
            "total_amount": round(float(df["amount"].sum()), 2),
            "average_amount": round(float(df["amount"].mean()), 2),
            "max_amount": round(float(df["amount"].max()), 2),
            "min_amount": round(float(df["amount"].min()), 2),
            "std_deviation": round(float(df["amount"].std()), 2),
            "total_categories": int(df["category"].nunique()),
            "total_merchants": int(df["merchant"].nunique()),
            "status_distribution": df["status"]
            .value_counts()
            .to_dict(),
            "monthly_totals": self._compute_monthly_totals(df),
            "generated_at": datetime.utcnow().isoformat(),
        }
        return summary

    def _compute_monthly_totals(self, df: pd.DataFrame) -> list[dict]:
        df = df.copy()
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        df["month"] = df["transaction_date"].dt.to_period("M").astype(str)
        monthly = (
            df.groupby("month")
            .agg(
                total=("amount", "sum"),
                count=("amount", "count"),
                average=("amount", "mean"),
            )
            .reset_index()
        )
        monthly["total"] = monthly["total"].round(2)
        monthly["average"] = monthly["average"].round(2)
        return monthly.to_dict(orient="records")

    async def get_by_category_report(self) -> dict[str, Any]:
        df = await self._fetch_all_transactions()
        if df.empty:
            return {"message": "Sem dados disponíveis", "categories": []}

        category_stats = (
            df.groupby("category")
            .agg(
                total_amount=("amount", "sum"),
                transaction_count=("amount", "count"),
                average_amount=("amount", "mean"),
                max_amount=("amount", "max"),
                min_amount=("amount", "min"),
                percentage_of_total=(
                    "amount",
                    lambda x: round(x.sum() / df["amount"].sum() * 100, 2),
                ),
            )
            .reset_index()
        )

        for col in ["total_amount", "average_amount", "max_amount", "min_amount"]:
            category_stats[col] = category_stats[col].round(2)

        category_stats = category_stats.sort_values("total_amount", ascending=False)

        top_merchant_per_category = (
            df.groupby(["category", "merchant"])["amount"]
            .sum()
            .reset_index()
            .sort_values("amount", ascending=False)
            .groupby("category")
            .first()
            .reset_index()[["category", "merchant"]]
            .rename(columns={"merchant": "top_merchant"})
        )

        merged = category_stats.merge(top_merchant_per_category, on="category", how="left")

        return {
            "total_categories": int(len(merged)),
            "categories": merged.to_dict(orient="records"),
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_top_transactions(
        self, limit: int = 10, order_by: str = "amount"
    ) -> dict[str, Any]:
        df = await self._fetch_all_transactions()
        if df.empty:
            return {"message": "Sem dados disponíveis", "transactions": []}

        valid_columns = {"amount", "transaction_date"}
        sort_col = order_by if order_by in valid_columns else "amount"

        top = df.nlargest(limit, sort_col)
        top = top.copy()
        top["transaction_date"] = top["transaction_date"].astype(str)
        top["id"] = top["id"].astype(str)
        top["amount"] = top["amount"].round(2)

        return {
            "limit": limit,
            "order_by": sort_col,
            "transactions": top.to_dict(orient="records"),
            "generated_at": datetime.utcnow().isoformat(),
        }
