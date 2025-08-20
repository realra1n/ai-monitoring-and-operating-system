import time
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ..schemas.auth import Token, User
from ..models.memory import USERS, TOKENS, TENANT

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def login_service(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = f"tok-{int(time.time()*1000)}-{form_data.username}"
    TOKENS[token] = form_data.username
    return Token(access_token=token)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    if token == "tok-demo":
        return User(id=1, name="Demo Admin", email="demo@oneservice.local", role="TENANT_ADMIN", tenant=TENANT)
    user_email = TOKENS.get(token)
    if not user_email or user_email not in USERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = USERS[user_email]
    return User(id=user["id"], name=user["name"], email=user_email, role=user["role"], tenant=user["tenant"])
