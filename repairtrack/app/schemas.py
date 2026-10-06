"""Схемы запросов и ответов API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import OrderStatus


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_name: str = Field(min_length=1, max_length=200)
    owner_phone: str = Field(min_length=5, max_length=32)
    device_type: str = Field(min_length=1, max_length=100)
    device_model: str = Field(min_length=1, max_length=200)
    serial_number: str = Field(min_length=1, max_length=100)
    problem_description: str = Field(min_length=1, max_length=2000)
    accessories: str = Field(default="", max_length=1000)
    condition_notes: str = Field(default="", max_length=1000)


class OrderCreated(BaseModel):
    """Ответ при приёме: код получения показывается только здесь, один раз."""

    id: int
    receipt_number: str
    retrieval_code: str
    status: OrderStatus


class StatusEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    old_status: OrderStatus | None
    new_status: OrderStatus
    created_at: datetime


class OrderOut(BaseModel):
    """Внутреннее представление заказа для сотрудников (без кода и его хеша)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_number: str
    owner_name: str
    owner_phone: str
    device_type: str
    device_model: str
    serial_number: str
    problem_description: str
    accessories: str
    condition_notes: str
    status: OrderStatus
    total_cost: int | None
    created_at: datetime
    events: list[StatusEventOut]


class PublicStatusQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receipt_number: str = Field(min_length=1, max_length=16)
    retrieval_code: str = Field(min_length=1, max_length=64)


class PublicStatusOut(BaseModel):
    """Ответ клиенту без входа: только статус и итоговая стоимость (SR-08)."""

    status: OrderStatus
    total_cost: int | None
