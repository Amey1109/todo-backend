from typing import Annotated
from fastapi import  APIRouter, Depends, HTTPException
from models import  Todos
from database import session_local
from sqlalchemy.orm import Session
from starlette import status
from .auth import get_current_user

def get_db():
    db  =  session_local()
    try:
        yield db
    finally:
        db.close()

router  = APIRouter(prefix="/admin", tags=['admin'])
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/todos", status_code= status.HTTP_200_OK)
async def get_all_todos(user: user_dependency, db:db_dependency):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    return db.query(Todos).all()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user:user_dependency,db:db_dependency,todo_id:str):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Todo with {todo_id} not found')
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()

