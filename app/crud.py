from sqlalchemy.orm import Session
import models

def create_user_task(db: Session, text: str, languages: list):
    task = models.QueryTask(text=text, languages=languages)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_user_task(db: Session, task_id: int):
    return db.query(models.QueryTask).filter(models.QueryTask.id == task_id).first()

def update_user_task(db: Session, task_id: int, results: dict):
    task = db.query(models.QueryTask).filter(models.QueryTask.id == task_id).first()
    task.results = results
    task.status = "Completed"
    db.commit()
    db.refresh(task)
    return task