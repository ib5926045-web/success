from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsPatch(BaseModel):
    rating_opt_out: bool | None = None

@router.patch("")
def patch(body: SettingsPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.rating_opt_out is not None:
        user.rating_opt_out = body.rating_opt_out
    db.commit()
    return {"ok": True, "rating_opt_out": user.rating_opt_out}
