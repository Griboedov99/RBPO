import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    """Клиент API с отдельной базой в памяти для каждого теста."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def order_payload():
    return {
        "owner_name": "Тестовый Клиент",
        "owner_phone": "+70000000000",
        "device_type": "ноутбук",
        "device_model": "Учебная модель X1",
        "serial_number": "SN-TEST-0001",
        "problem_description": "Не включается",
        "accessories": "зарядное устройство",
        "condition_notes": "царапина на крышке",
    }
