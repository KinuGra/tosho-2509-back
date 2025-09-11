from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token, ALGORITHM
from app.core.config import settings
from app.deps import get_db
import logging
import sys

# ロガーの設定
logger = logging.getLogger("uvicorn.auth")
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "sq_token"
COOKIE_SECURE = False  # 本番は True + HTTPS
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 1週間

def set_auth_cookie(response: Response, token: str) -> None:
    """認証用クッキーを設定する共通関数"""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=COOKIE_MAX_AGE,
        path="/"
    )

@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    set_auth_cookie(response, token)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    try:
        logger.info(f"[Auth] 👤 ログインリクエスト受信: email={payload.email}")
        
        # ユーザー検索
        user = db.query(User).filter(User.email == payload.email).first()
        if not user:
            logger.warning(f"[Auth] ❌ ユーザーが見つかりません: {payload.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # パスワード検証
        if not verify_password(payload.password, user.password_hash):
            logger.warning(f"[Auth] ❌ パスワードが一致しません: {payload.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # トークン生成
        logger.info(f"[Auth] 🔑 トークン生成: user_id={user.id}")
        token = create_access_token(str(user.id))
        
        # クッキー設定
        logger.info(f"[Auth] 🍪 クッキー設定: user_id={user.id}")
        response.set_cookie(
            COOKIE_NAME, 
            token, 
            httponly=COOKIE_HTTPONLY, 
            secure=COOKIE_SECURE, 
            samesite=COOKIE_SAMESITE
        )
        
        logger.info(f"[Auth] ✅ ログイン成功: user_id={user.id}")
        print(f"[Auth Console] ✅ ログイン成功: email={payload.email}, user_id={user.id}", flush=True)
        
        return {"access_token": token, "token_type": "bearer"}
        
    except HTTPException as he:
        # 既知のエラーは再送
        raise he
    except Exception as e:
        # 予期しないエラー
        error_msg = f"[Auth] ❌ ログイン処理中にエラーが発生: {str(e)}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr, flush=True)
        raise HTTPException(status_code=500, detail="Internal server error")

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    try:
        logger.debug(f"[Auth] 🔒 認証チェック開始")
        logger.debug(f"[Auth] 📝 リクエストヘッダー: {dict(request.headers)}")
        logger.debug(f"[Auth] 🍪 リクエストクッキー: {request.cookies}")
        
        token = request.cookies.get(COOKIE_NAME)
        if not token:
            logger.warning("[Auth] ❌ トークンが見つかりません")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
            
        logger.debug(f"[Auth] 🎟 トークン検証開始")
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            logger.warning("[Auth] ❌ トークンにユーザーIDがありません")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
            
        # ユーザーの取得
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.warning(f"[Auth] ❌ ユーザーが見つかりません: ID={user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
            
        logger.info(f"[Auth] ✅ 認証成功: user_id={user_id}")
        return user
        
    except JWTError as e:
        logger.error(f"[Auth] ❌ トークン検証エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    except Exception as e:
        logger.error(f"[Auth] ❌ 認証処理中のエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error"
        )

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    logger.info(f"[Auth] 👤 ユーザー情報取得: id={user.id}")
    return {
        "id": user.id,
        "email": user.email,
        "exp": user.exp,
        "level": user.level
    }
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

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

@router.get("/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    user = current_user_from_cookie(request, db)
    return {"id": user.id, "email": user.email, "level": user.level, "exp": user.exp}