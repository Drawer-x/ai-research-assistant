from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserLogin, UserRegister

router = APIRouter(prefix="/auth", tags=["认证"])


def user_data(user: User) -> dict:
    return {"id": user.id, "username": user.username, "email": user.email}


@router.post("/register")
def register(payload: UserRegister, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if not username:
        return error_response("用户名不能为空")
    existing = db.scalar(select(User).where(or_(User.username == username, User.email == payload.email)))
    if existing:
        return error_response("用户名或邮箱已存在", 409)
    user = User(username=username, email=str(payload.email), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response({"user_id": user.id, "username": user.username, "email": user.email})


@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        return error_response("用户名或密码错误", 401)
    return success_response({"token": create_access_token(user.id), "token_type": "bearer", "user": user_data(user)})


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return success_response(user_data(current_user))
