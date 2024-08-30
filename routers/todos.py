from typing import Annotated, Literal
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Path, APIRouter
from models import Todos
from database import session_local
from starlette import status
from pydantic import BaseModel, Field
from .auth import get_current_user
router = APIRouter()

def get_db():
    db  =  session_local()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title : str =  Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int =  Field(gt=0, lt=6)
    complete: bool


@router.get("/todos",   status_code=status.HTTP_200_OK)
async def get_all_todos(user:user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    todo_for_current_user = db.query(Todos).filter(Todos.owner_id == user.get('id')).all()
    return todo_for_current_user

@router.get("/todos/{todo_id}",status_code=status.HTTP_200_OK)
async def get_todo_by_id(user:user_dependency, db:db_dependency, todo_id:int= Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id ==todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is not None:
        return todo_model
    else:
        raise HTTPException(status_code=404, detail="Todo not found.")


@router.post("/todos", status_code=status.HTTP_201_CREATED)
async def create_todo(user:user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    todo_model = Todos(**todo_request.model_dump(), owner_id = user.get('id'))
    db.add(todo_model)
    db.commit()

@router.put('/todos/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency,db: db_dependency,todo_request: TodoRequest, todo_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.complete = todo_request.complete
    todo_model.priority = todo_request.priority

    db.add(todo_model)
    db.commit()

@router.put('/todos/toggle_todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def toggle_todo(user:user_dependency,db:db_dependency, todo_id: int=Path(gt=0), status: Literal['complete', 'un_complete']='complete'):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
    todo_model.complete = (status == 'complete')
    db.commit()


@router.delete('/todos/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency,db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()



