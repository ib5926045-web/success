import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./dev.db")
os.environ.setdefault("TELEGRAM_DEV_MODE", "true")
os.environ.setdefault("SECRET_KEY", "test_secret_key_32_chars_min___")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def _get_db():
        s = TestingSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _get_db
    # deps.get_current_user зависит от get_db — override по объекту функции покрывает и его
    import app.deps as depsmod
    app.dependency_overrides[depsmod.get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    r = client.post("/api/auth/telegram", json={"initData": "dev"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}
