from fastapi import FastAPI, Depends, HTTPException, Path
from typing import Annotated

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

import models
from models import Todos
from database import engine, SessionLocal


app = FastAPI()

'''
ця команда буде виконана лише у тому випадку, якщо не існує нашого todos.db
отже, якщо ми повернемося до наших моделей і покращимо наші таблиці todos.db, 
це не призведе до автоматичного покращення таблиць за допомогою цього швидкого та простого способу створення баз даних.
простіше просто видалити нашу бд, а потім створити її заново, якщо ми додамо щось додаткове до нашої бд

Alembic will teach how to enhance DB without deleting each time.
'''
models.Base.metadata.create_all(bind=engine)


# ми можемо отримувати інфу з бази даних, повертати її клієнту, а потім закривати з'єднання з базою.
def get_db():
    db = SessionLocal()
    try:
        yield db  # yield означає, що перед відправкою відповіді виконується лише код до оператора yield включно
    finally:
        db.close()  # код що слідує після yield, виконується після отримання відповіді.


db_dependency = Annotated[Session, Depends(get_db)]


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    completed: bool





@app.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency): #depends це dependency injection
    return db.query(Todos).all()


@app.get("/todos/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency,todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo Not found.")


@app.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: TodoRequest):
    todo_model = Todos(**todo_request.model_dump())

    db.add(todo_model) # add означає підготовку бази
    db.commit()  # commit означає її очищення і власне виконання транзакції з БД



@app.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo Not found.")

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.completed = todo_request.completed

    db.add(todo_model)
    db.commit()



@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency,todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo Not found.")

    db.query(Todos).filter(Todos.id == todo_id).delete()

    db.commit()

