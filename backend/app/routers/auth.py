from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.limiter import limiter
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, ProfileUpdateRequest, RegisterRequest, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
@limiter.limit("5/minute")  # 注册限制：每分钟5次
def register(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user, token = auth_service.register(
            db, req.username, req.password, req.name,
            req.gender, req.skill_level, req.birth_year, req.bio,
        )
        return {"token": token, "user": UserResponse.model_validate(user)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")  # 登录限制：每分钟10次
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    try:
        user, token = auth_service.login(db, req.username, req.password)
        return {"token": token, "user": UserResponse.model_validate(user)}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_me(req: ProfileUpdateRequest, current_user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    user = auth_service.update_profile(
        db, current_user, req.name, req.gender,
        req.skill_level, req.birth_year, req.bio,
    )
    return UserResponse.model_validate(user)


@router.get("/me/stats")
def me_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return auth_service.get_user_stats(db, current_user.id)
