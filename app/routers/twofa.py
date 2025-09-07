import secrets, hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.deps import get_db
from app.schemas.auth import Request2FAIn, Verify2FAIn
from app.db.models import VerificationCode, User
from app.core.emailer import send_verification_code

router = APIRouter(prefix="/2fa", tags=["2fa"])

def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

@router.post("/request")
def request_code(payload: Request2FAIn, db: Session = Depends(get_db)):
    # 6桁コードを生成（000000〜999999）
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    vc = VerificationCode(
        email=payload.email,
        code_hash=_hash_code(code),
        expires_at=expires,
        attempts_left=3
    )
    db.add(vc)
    db.commit()
    send_verification_code(payload.email, code)
    return {"message": "Verification code sent"}

@router.post("/verify")
def verify_code(payload: Verify2FAIn, db: Session = Depends(get_db)):
    # 最新のレコードを拾う
    vc = (
        db.query(VerificationCode)
          .filter(VerificationCode.email == payload.email)
          .order_by(VerificationCode.created_at.desc())
          .first()
    )
    if not vc:
        raise HTTPException(status_code=400, detail="No code requested")
    if vc.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Code expired")
    if vc.attempts_left <= 0:
        raise HTTPException(status_code=400, detail="No attempts left")

    if _hash_code(payload.code) != vc.code_hash:
        vc.attempts_left -= 1
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid code")

    # 成功：ここでアプリ要件に応じてフラグを立てるなど
    # 例：ユーザーを確定アクティブにするとか、2FA済みセッションにするとか
    return {"message": "2FA success"}
