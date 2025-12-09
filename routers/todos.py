from fastapi import Depends, HTTPException, Path, APIRouter
from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from ..models import Todos
from ..database import SessionLocal
from .auth import get_current_user


router = APIRouter()


"""
ця команда буде виконана лише у тому випадку, якщо не існує нашого todos.db
отже, якщо ми повернемося до наших моделей і покращимо наші таблиці todos.db,
це не призведе до автоматичного покращення таблиць за допомогою цього швидкого та простого способу створення баз даних.
простіше просто видалити нашу бд, а потім створити її заново, якщо ми додамо щось додаткове до нашої бд

Alembic will teach how to enhance DB without deleting each time.
"""


# ми можемо отримувати інфу з бази даних, повертати її клієнту, а потім закривати з'єднання з базою.
def get_db():
    db = SessionLocal()
    try:
        yield db  # yield означає, що перед відправкою відповіді виконується лише код до оператора yield включно
    finally:
        db.close()  # код що слідує після yield, виконується після отримання відповіді.


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):  # це dependency injection
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    return db.query(Todos).filter(Todos.owner_id == user.get("id")).all()



@router.get("/todos/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    todo_model = (db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get("id")).first())

    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo Not found.")



@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get("id"))

    db.add(todo_model)  # add означає підготовку бази
    db.commit()  # commit означає її очищення і власне виконання транзакції з БД



@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency,db: db_dependency,todo_request: TodoRequest,todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    todo_model = (db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get("id")).first())

    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo Not found.")

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()



@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()

    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo Not found.")

    db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).delete()
    db.commit()
