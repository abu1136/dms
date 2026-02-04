import os
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.config import get_settings
from app.database.base import Base
from app.database.session import get_db
from app.auth.security import get_password_hash
from app.models.user import User
from app.models.document import Document
import app.routers.documents as documents_router
import app.routers.templates as templates_router
import app.routers.backup as backup_router
import app.routers.sync as sync_router
import app.services.template as template_service


# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db, tmp_path):
    settings = get_settings()
    original_storage_dir = settings.storage_dir
    original_lifespan = app.router.lifespan_context
    storage_dir = tmp_path / "uploads"
    storage_dir.mkdir(parents=True, exist_ok=True)
    settings.storage_dir = str(storage_dir)
    
    for module in [documents_router, templates_router, backup_router, sync_router, template_service]:
        module.settings.storage_dir = settings.storage_dir
    
    @asynccontextmanager
    async def test_lifespan(_app):
        yield
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    app.router.lifespan_context = test_lifespan
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan
    settings.storage_dir = original_storage_dir


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_invalid_credentials(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "invalid", "password": "invalid"}
    )
    assert response.status_code == 401


def _create_user(db, username, password, role="user"):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=get_password_hash(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, username, password):
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_document_access_control(client, db):
    user1 = _create_user(db, "user1", "password1")
    user2 = _create_user(db, "user2", "password2")
    
    settings = get_settings()
    file_name = "DOC-TEST-0001.pdf"
    file_path = os.path.join(settings.storage_dir, file_name)
    with open(file_path, "wb") as f:
        f.write(b"test")
    
    doc = Document(
        document_number="DOC-20260101-0001",
        title="Secret",
        template_id=None,
        requested_by_id=user1.id,
        file_path=file_path,
        file_name=file_name,
        mime_type="application/pdf",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    user1_headers = _login(client, "user1", "password1")
    user2_headers = _login(client, "user2", "password2")
    
    response = client.get(f"/api/documents/{doc.id}", headers=user1_headers)
    assert response.status_code == 200
    
    response = client.get(f"/api/documents/{doc.id}", headers=user2_headers)
    assert response.status_code == 404
    
    response = client.get(f"/api/documents/{doc.id}/download", headers=user2_headers)
    assert response.status_code == 404
    
    response = client.get("/api/documents/search?document_number=DOC-20260101", headers=user2_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_document_with_invalid_template(client, db):
    _create_user(db, "user3", "password3")
    headers = _login(client, "user3", "password3")
    
    response = client.post(
        "/api/documents/",
        json={"title": "Doc", "template_id": 9999, "content": "hello"},
        headers=headers,
    )
    assert response.status_code == 404


def test_backup_restore_roundtrip(client, db):
    _create_user(db, "admin", "adminpass", role="admin")
    headers = _login(client, "admin", "adminpass")
    
    settings = get_settings()
    storage_dir = settings.storage_dir
    templates_dir = os.path.join(storage_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    doc_path = os.path.join(storage_dir, "DOC-RESTORE.pdf")
    tpl_path = os.path.join(templates_dir, "template.pdf")
    with open(doc_path, "wb") as f:
        f.write(b"doc")
    with open(tpl_path, "wb") as f:
        f.write(b"tpl")
    
    response = client.post("/api/admin/backup/create", headers=headers)
    assert response.status_code == 200
    backup_name = response.json()["backup_file"]
    
    os.remove(doc_path)
    os.remove(tpl_path)
    assert not os.path.exists(doc_path)
    assert not os.path.exists(tpl_path)
    
    response = client.post(
        "/api/admin/backup/restore",
        json={"backup_file": backup_name},
        headers=headers,
    )
    assert response.status_code == 200
    assert os.path.exists(doc_path)
    assert os.path.exists(tpl_path)
