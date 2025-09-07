from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.deps import get_db
from app.schemas.auth import StepCompleteIn
from app.db.models import User, Step, UserStepProgress
from app.routers.auth import current_user_from_cookie

router = APIRouter(prefix="/progress", tags=["progress"])

def _level_up(user: User) -> None:
    # シンプルなレベル計算（例）：レベル^2 * 50 を超えたら +1
    needed = (user.level ** 2) * 50
    while user.exp >= needed:
        user.level += 1
        needed = (user.level ** 2) * 50

@router.post("/complete")
def complete_step(payload: StepCompleteIn, request: Request, db: Session = Depends(get_db)):
    user = current_user_from_cookie(request, db)
    step = db.get(Step, payload.step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    prog = (
        db.query(UserStepProgress)
          .filter(UserStepProgress.user_id == user.id, UserStepProgress.step_id == step.id)
          .first()
    )
    if prog and prog.is_cleared:
        return {"message": "Already cleared", "level": user.level, "exp": user.exp}

    if not prog:
        prog = UserStepProgress(user_id=user.id, step_id=step.id)

    prog.is_cleared = True
    prog.cleared_at = datetime.now(timezone.utc)

    user.exp += step.xp_reward
    _level_up(user)

    db.add(prog)
    db.add(user)
    db.commit()

    return {"message": "Cleared", "level": user.level, "exp": user.exp, "reward": step.xp_reward}
