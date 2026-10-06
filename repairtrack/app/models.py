"""Модели хранилища: заказ на ремонт и журнал статусов."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrderStatus(str, enum.Enum):
    ACCEPTED = "accepted"          # принят
    IN_PROGRESS = "in_progress"    # в работе
    READY = "ready"                # готово
    UNREPAIRABLE = "unrepairable"  # ремонт невозможен
    ISSUED = "issued"              # выдан


class RepairOrder(Base):
    __tablename__ = "repair_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_number: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    # Хранится только SHA-256 от кода получения, сам код не сохраняется (D-02).
    retrieval_code_hash: Mapped[str] = mapped_column(String(64))

    owner_name: Mapped[str] = mapped_column(String(200))
    owner_phone: Mapped[str] = mapped_column(String(32))
    device_type: Mapped[str] = mapped_column(String(100))
    device_model: Mapped[str] = mapped_column(String(200))
    serial_number: Mapped[str] = mapped_column(String(100))
    problem_description: Mapped[str] = mapped_column(Text)
    accessories: Mapped[str] = mapped_column(Text, default="")
    condition_notes: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False), default=OrderStatus.ACCEPTED
    )
    total_cost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    events: Mapped[list["StatusEvent"]] = relationship(
        back_populates="order", order_by="StatusEvent.id"
    )


class StatusEvent(Base):
    """Запись журнала статусов. Через API только добавляется (SR-06, D-03)."""

    __tablename__ = "status_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("repair_orders.id"), index=True)
    old_status: Mapped[OrderStatus | None] = mapped_column(
        Enum(OrderStatus, native_enum=False), nullable=True
    )
    new_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, native_enum=False))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    order: Mapped[RepairOrder] = relationship(back_populates="events")
