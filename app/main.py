import os
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from itsdangerous import URLSafeSerializer, BadSignature
from dotenv import load_dotenv
import schemas
import crud
import models
from util import perform_query
from providers import PROVIDERS, get_models as get_provider_models, get_all_models
from database import get_db, engine
from typing import List, Optional

load_dotenv()

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
signer = URLSafeSerializer(SECRET_KEY)

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(request: Request, db: Session) -> Optional[models.User]:
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return None
    try:
        user_id = signer.loads(session_cookie)
    except BadSignature:
        return None
    return db.query(models.User).filter(models.User.id == user_id).first()


@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/index")


@app.get("/index", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(name="index.html", request=request, context={"user": user})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(name="login.html", request=request, context={"error": None})


@app.post("/login")
def login(request: Request, data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, data.username)
    if not user or not crud.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    response = Response(status_code=200)
    response.set_cookie(
        key="session",
        value=signer.dumps(user.id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(name="register.html", request=request, context={"error": None})


@app.post("/register")
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if len(data.username) < 3:
        raise HTTPException(status_code=422, detail="Username must be at least 3 characters")
    if len(data.password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    existing = crud.get_user_by_username(db, data.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    user = crud.create_user(db, data.username, data.password)
    response = Response(status_code=201)
    response.set_cookie(
        key="session",
        value=signer.dumps(user.id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@app.post("/logout")
def logout():
    response = RedirectResponse(url="/index", status_code=303)
    response.delete_cookie("session")
    return response


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    tasks = crud.get_tasks_by_user(db, user.id)
    return templates.TemplateResponse(name="history.html", request=request, context={"user": user, "tasks": tasks})


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    config = crud.get_user_llm_config(user)
    user_key = config["api_key"]
    user_provider = config["provider"]
    provider_models = get_all_models({user_provider: user_key} if user_key else None)
    return templates.TemplateResponse(name="settings.html", request=request, context={
        "user": user,
        "provider": config["provider"],
        "model": config["model"],
        "has_api_key": user_key is not None,
        "provider_models": provider_models,
    })


@app.post("/settings")
def save_settings(request: Request, data: schemas.LLMSettingsRequest, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    if data.provider not in PROVIDERS:
        raise HTTPException(status_code=422, detail="Unsupported provider")
    crud.update_user_llm_settings(db, user.id, data.provider, data.model, data.api_key)
    return {"status": "ok"}


@app.get("/api/models/{provider}")
def get_models(provider: str, request: Request, db: Session = Depends(get_db)):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider")
    user = get_current_user(request, db)
    api_key = None
    if user:
        config = crud.get_user_llm_config(user)
        if config["provider"] == provider:
            api_key = config["api_key"]
    return {"models": get_provider_models(provider, api_key)}


@app.post("/result", response_model=schemas.UserResponse)
def result(request: Request, data: schemas.UserRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    user_id = user.id if user else None
    llm_config = crud.get_user_llm_config(user) if user else None
    task = crud.create_user_task(db, data.text, data.languages, user_id=user_id)
    background_tasks.add_task(perform_query, task.id, data.text, data.languages, db, llm_config)
    return {"task_id": task.id}


@app.get("/result/{task_id}", response_model=schemas.UserStatus)
def get_result(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_user_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "status": task.status,
        "results": task.results or {}
    }


@app.get("/result/content/{task_id}")
def get_result_content(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_user_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
