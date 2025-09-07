from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.deps import get_db
from app.db.models import User

router = APIRouter(prefix="/ranking", tags=["ranking"])

@router.get("")
def get_ranking(db: Session = Depends(get_db), limit: int = 50):
    rows = db.query(User.id, User.email, User.level, User.exp) \
             .order_by(desc(User.level), desc(User.exp)) \
             .limit(limit).all()
    return [{"user_id": r.id, "email": r.email, "level": r.level, "exp": r.exp} for r in rows]
