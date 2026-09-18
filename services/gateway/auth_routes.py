from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from sqlalchemy import select  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore

from services.common.auth import create_access_token, get_current_user, hash_password, verify_password
from services.gateway.database import get_db
from services.gateway.models import TokenResponseSchema, User, UserLoginSchema, UserRegisterSchema, UserResponseSchema

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegisterSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = User(
        email=payload.email, hashed_password=hash_password(payload.password), full_name=payload.full_name
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponseSchema)
async def login_user(payload: UserLoginSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": user.id, "email": user.email, "name": user.full_name})
    return TokenResponseSchema(access_token=access_token, user=UserResponseSchema.model_validate(user))


@router.get("/me", response_model=UserResponseSchema)
async def get_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = current_user.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
