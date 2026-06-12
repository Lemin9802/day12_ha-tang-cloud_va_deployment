import time
from dataclasses import dataclass, field

from fastapi import HTTPException

from .config import settings


PRICE_PER_REQUEST_USD = 0.001


@dataclass
class BudgetRecord:
    user_id: str
    month: str = field(default_factory=lambda: time.strftime("%Y-%m"))
    request_count: int = 0
    spent_usd: float = 0.0


_records: dict[str, BudgetRecord] = {}


def _get_record(user_id: str) -> BudgetRecord:
    month = time.strftime("%Y-%m")
    record = _records.get(user_id)

    if not record or record.month != month:
        record = BudgetRecord(user_id=user_id, month=month)
        _records[user_id] = record

    return record


def check_budget(user_id: str, estimated_cost: float = PRICE_PER_REQUEST_USD) -> BudgetRecord:
    record = _get_record(user_id)

    if record.spent_usd + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "user_id": user_id,
                "spent_usd": round(record.spent_usd, 6),
                "monthly_budget_usd": settings.monthly_budget_usd,
                "resets_at": "next month",
            },
        )

    return record


def record_usage(user_id: str, actual_cost: float = PRICE_PER_REQUEST_USD) -> BudgetRecord:
    record = _get_record(user_id)
    record.request_count += 1
    record.spent_usd += actual_cost
    return record


def get_usage(user_id: str) -> dict:
    record = _get_record(user_id)

    return {
        "user_id": user_id,
        "month": record.month,
        "request_count": record.request_count,
        "spent_usd": round(record.spent_usd, 6),
        "monthly_budget_usd": settings.monthly_budget_usd,
        "remaining_usd": round(max(0, settings.monthly_budget_usd - record.spent_usd), 6),
    }
