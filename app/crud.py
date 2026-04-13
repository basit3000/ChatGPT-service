import os
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
import models
import bcrypt

_fernet_key = os.getenv("FERNET_KEY")
if _fernet_key:
    _fernet = Fernet(_fernet_key.encode())
else:
    _fernet = Fernet(Fernet.generate_key())


def encrypt_api_key(api_key: str) -> str:
    return _fernet.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted: str) -> str:
    return _fernet.decrypt(encrypted.encode()).decode()


def create_user(db: Session, username: str, password: str):
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = models.User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_user_task(db: Session, text: str, languages: list, user_id: int = None):
    task = models.QueryTask(text=text, languages=languages, user_id=user_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_user_task(db: Session, task_id: int):
    return db.query(models.QueryTask).filter(models.QueryTask.id == task_id).first()

def get_tasks_by_user(db: Session, user_id: int):
    return db.query(models.QueryTask).filter(models.QueryTask.user_id == user_id).order_by(models.QueryTask.created_at.desc()).all()

def update_user_task(db: Session, task_id: int, results: dict, status: str = "Completed"):
    task = db.query(models.QueryTask).filter(models.QueryTask.id == task_id).first()
    task.results = results
    task.status = status
    db.commit()
    db.refresh(task)
    return task

def update_user_llm_settings(db: Session, user_id: int, provider: str, model: str, api_key: str = None):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.llm_provider = provider
    user.llm_model = model
    if api_key:
        user.api_key_encrypted = encrypt_api_key(api_key)
    db.commit()
    db.refresh(user)
    return user

def get_user_llm_config(user) -> dict:
    config = {
        "provider": user.llm_provider or "openai",
        "model": user.llm_model or "gpt-4o-mini",
        "api_key": None,
    }
    if user.api_key_encrypted:
        try:
            config["api_key"] = decrypt_api_key(user.api_key_encrypted)
        except Exception:
            pass
    return config