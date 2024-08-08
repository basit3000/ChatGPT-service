from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import schemas
import crud
import models
from utily import perform_query
from database import get_db, engine
from typing import List

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/index', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/result", response_model=schemas.UserResponse)
def result(request: schemas.UserRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = crud.create_user_task(db, request.text, request.languages)
    background_tasks.add_task(perform_query, task.id, request.text, request.languages, db)
    return {"task_id": task.id}

@app.get("/result/{task_id}", response_model=schemas.UserStatus)
def get_result(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_user_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "status": task.status,
        "results": task.results
    }

@app.get("/result/content/{task_id}")
def get_result_content(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_user_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
