from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import  APIRouter, Depends, HTTPException
from pydantic import BaseModel
from models import  Users
from passlib.context import CryptContext
from database import session_local
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt


SECRET_KEY = "97aa25f319679c86c72febed95ab9a42305abe55cdc2aba34b71332f5e282bdc"
ALGORITHM = 'HS256'

router  = APIRouter(prefix="/auth", tags=['auth'])
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

def get_db():
    db  =  session_local()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class CreateUserRequest(BaseModel):
    username:str
    email: str
    first_name : str
    last_name:str
    password: str
    role: str
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type : str
    refresh_token:str

def authenticate_user(username:str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
       return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_token(username:str, user_id:int, role: str,expires_delta:timedelta):
    encode = {
        'sub':username ,
        'id': user_id,
        'role': role
    }
    encode.update({'exp':datetime.now(timezone.utc) + expires_delta})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def revoke_refresh_token(user_id:int, db: db_dependency):
    user_model = db.query(Users).filter(Users.id == user_id).first()
    print(user_model.refresh_token)
    user_model.refresh_token = None
    print(user_model.refresh_token)
    db.commit()


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id:int = payload.get('id')
        user_role:str = payload.get('role')

        user_model = db.query(Users).filter(Users.id == user_id).first()
        if user_model.refresh_token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")

        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "Could not validate user")
        return {
            'username': username, 'id': user_id, 'role': user_role
        }
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email = create_user_request.email,
        username = create_user_request.username,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        role= create_user_request.role,
        hashed_password = bcrypt_context.hash(create_user_request.password),
        phone_number = create_user_request.phone_number,
        is_active = True
    )
    db.add(create_user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(db: db_dependency,formData : Annotated[OAuth2PasswordRequestForm, Depends()]):
    user  = authenticate_user(formData.username, formData.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")
    token = create_token(user.username, user.id,user.role ,timedelta(minutes=20))
    refresh_token = create_token(user.username, user.id,user.role ,timedelta(days=7))
    user.refresh_token = refresh_token
    db.commit()
    return {
        'refresh_token':refresh_token,
        'access_token': token,
        'token_type' : 'bearer'
    }

@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
async def logout(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        user_id = payload.get('id')
        if user_id is not None:
            user_model = db.query(Users).filter(Users.id == user_id).first()
            user_model.refresh_token = None
            db.commit()
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")

