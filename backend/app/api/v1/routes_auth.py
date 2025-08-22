from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from ...schemas.auth import Token, User
from ...services.auth import login_service, get_current_user

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    return await login_service(form)


@router.get("/me", response_model=User)
async def me(current: User = Depends(get_current_user)):
    return current
