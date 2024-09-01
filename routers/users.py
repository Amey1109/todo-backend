from typing import Annotated
from fastapi import  APIRouter, Depends, HTTPException
from models import Users
from database import session_local
from sqlalchemy.orm import Session
from starlette import status
from .auth import get_current_user
from passlib.context import CryptContext
from pydantic import BaseModel, Field


def get_db():
    db  =  session_local()
    try:
        yield db
    finally:
        db.close()

router  = APIRouter(prefix="/user", tags=['user'])
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class NewPassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)

class NewPhoneNumber(BaseModel):
    phone_number:str = Field(min_length=10)

class CurrentUser(BaseModel):
    username: str
    last_name:str
    phone_number:str
    email:str
    role: str



@router.get("/get_current_user", status_code=status.HTTP_200_OK, response_model=CurrentUser)
async def get_current_user(user: user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated.")
    return db.query(Users).filter(Users.id == user.get('id')).first()

@router.put('/change_password', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db:db_dependency, new_password_request: NewPassword):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated.")
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    if not bcrypt_context.verify(new_password_request.current_password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password is incorrect.")
    new_hashed_password = bcrypt_context.hash(new_password_request.new_password)
    user_model.hashed_password = new_hashed_password
    db.add(user_model)
    db.commit()

@router.put("/update_phone_number", status_code=status.HTTP_204_NO_CONTENT)
async def update_phone_number(user: user_dependency, db: db_dependency, new_phone_number_request: NewPhoneNumber):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated.")
    user_model = db.query(Users).filter(Users.id == user.get("id")).first()
    user_model.phone_number = new_phone_number_request.phone_number
    db.commit()
