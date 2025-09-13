from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.models import User
from app.deps import get_db

router = APIRouter(prefix="/users", tags=["users"])

# --- 経験値 API ---
@router.get("/{user_id}/exp")
def get_exp(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.id, "exp": user.exp}

@router.put("/{user_id}/exp")
def update_exp(user_id: int, amount: int, db: Session = Depends(get_db)):
    """
    経験値を加算/減算する
    amount=10 → exp +10
    amount=-5 → exp -5
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.exp += amount
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "exp": user.exp}

# --- 進捗 API ---
@router.get("/{user_id}/progress")
def get_progress(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.id, "progress": user.progress}

@router.put("/{user_id}/progress/{index}")
def update_progress_flag(user_id: int, index: int, db: Session = Depends(get_db)):
    """
    指定インデックス (0始まり) を "1" に変更する
    例: progress="0100", index=2 → "0110"
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if index < 0 or index >= len(user.progress):
        raise HTTPException(status_code=400, detail="Index out of range")

    progress_list = list(user.progress)
    progress_list[index] = "1"
    user.progress = "".join(progress_list)

    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "progress": user.progress}

@router.put("/{user_id}/progress")
def overwrite_progress(user_id: int, new_progress: str, db: Session = Depends(get_db)):
    """
    progress を丸ごと上書きする
    例: new_progress="1111"
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not all(c in "01" for c in new_progress):
        raise HTTPException(status_code=400, detail="Invalid progress format")

    user.progress = new_progress
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "progress": user.progress}