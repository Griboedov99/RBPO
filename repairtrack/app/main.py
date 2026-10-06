"""RepairTrack — минимальная запускаемая основа API сервисного центра."""

import hashlib
import hmac
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app.models import OrderStatus, RepairOrder, StatusEvent
from app.schemas import OrderCreate, OrderCreated, OrderOut, PublicStatusOut, PublicStatusQuery


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="RepairTrack",
    description="Учёт техники на ремонте. Минимальная основа к EK1: "
    "аутентификация и разграничение ролей (D-01, D-04) ещё не реализованы.",
    version="0.1.0",
    lifespan=lifespan,
)


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/orders",
    response_model=OrderCreated,
    status_code=status.HTTP_201_CREATED,
    tags=["orders"],
)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)) -> OrderCreated:
    """Приём устройства: создаёт заказ, номер квитанции и код получения."""
    retrieval_code = secrets.token_urlsafe(16)  # 128 бит случайности (D-02)
    order = RepairOrder(**payload.model_dump(), retrieval_code_hash=hash_code(retrieval_code))
    db.add(order)
    db.flush()
    order.receipt_number = f"RT-{order.id:06d}"
    db.add(StatusEvent(order_id=order.id, old_status=None, new_status=OrderStatus.ACCEPTED))
    db.commit()
    return OrderCreated(
        id=order.id,
        receipt_number=order.receipt_number,
        retrieval_code=retrieval_code,
        status=order.status,
    )


@app.get("/orders/{order_id}", response_model=OrderOut, tags=["orders"])
def get_order(order_id: int, db: Session = Depends(get_db)) -> RepairOrder:
    """Карточка заказа для сотрудника."""
    order = db.get(RepairOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


@app.post("/public/status", response_model=PublicStatusOut, tags=["public"])
def public_status(query: PublicStatusQuery, db: Session = Depends(get_db)) -> PublicStatusOut:
    """Статус заказа для клиента без входа: по номеру квитанции и коду (SR-08)."""
    order = db.scalar(
        select(RepairOrder).where(RepairOrder.receipt_number == query.receipt_number)
    )
    code_ok = order is not None and hmac.compare_digest(
        order.retrieval_code_hash, hash_code(query.retrieval_code)
    )
    if not code_ok:
        # Единый отказ: не раскрывает, существует ли квитанция.
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return PublicStatusOut(status=order.status, total_cost=order.total_cost)
