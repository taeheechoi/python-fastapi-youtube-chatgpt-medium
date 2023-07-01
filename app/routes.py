from fastapi import APIRouter, Depends

from app import schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()


@router.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user
