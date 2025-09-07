from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token, ALGORITHM
from app.core.config import settings
from app.deps import get_db
from fastapi import Request
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "sq_token"
COOKIE_SECURE = False  # 本番は True + HTTPS
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"

@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    response.set_cookie(COOKIE_NAME, token, httponly=COOKIE_HTTPONLY, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE)
    return {"access_token": token}

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user.id))
    response.set_cookie(COOKIE_NAME, token, httponly=COOKIE_HTTPONLY, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE)
    return {"access_token": token}

def get_current_user(token: str | None = None, db: Session = Depends(get_db), response: Response | None = None):
    # Cookie 優先 → Authorization ヘッダでもよい
    from fastapi import Request
    def extractor(request: Request) -> str | None:
        return request.cookies.get(COOKIE_NAME) or None
    # FastAPI の依存関数の外から cookie を直接参照しづらいので、実運用ではミドルウェアに分けてもOK
    # ここでは簡略化のため、ヘッダの Bearer だけにするか、各ハンドラで Cookie 参照しても良い
    raise NotImplementedError

# Cookie からユーザーを引く小ユーティリティ
def current_user_from_cookie(request: Request, db: Session) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user