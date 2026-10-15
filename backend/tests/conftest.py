import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite:///./test_aero.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_aero.db"):
        try:
            os.remove("./test_aero.db")
        except Exception:
            pass

@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token(db):
    user = User(
        email="test_admin@test.com",
        hashed_password=hash_password("admin123"),
        full_name="Admin Test",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role.value})

@pytest.fixture
def engineer_token(db):
    user = User(
        email="test_engineer@test.com",
        hashed_password=hash_password("eng123"),
        full_name="Engineer Test",
        role=UserRole.SUPPORT_ENGINEER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role.value})

@pytest.fixture
def requester_token(db):
    user = User(
        email="test_requester@test.com",
        hashed_password=hash_password("req123"),
        full_name="Requester Test",
        role=UserRole.REQUESTER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role.value})
