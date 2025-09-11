import secrets, hashlib
import logging
import sys
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.deps import get_db
from app.schemas.auth import Request2FAIn, Verify2FAIn
from app.db.models import VerificationCode, User
from app.core.emailer import send_verification_code
from app.core.config import settings

# ロガーの設定
logger = logging.getLogger("uvicorn.twofa")
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/2fa", tags=["2fa"])

def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

@router.post("/request")
async def request_code(payload: Request2FAIn, db: Session = Depends(get_db)):
    try:
        logger.info(f"2FAリクエストを受信: email={payload.email}")
        
        try:
            # 既存のコードをクリア
            deleted = db.query(VerificationCode).filter(
                VerificationCode.email == payload.email
            ).delete()
            logger.debug(f"[2FA] 🗑 削除された既存のコード数: {deleted}")
            db.commit()

            # 6桁コードを生成（000000〜999999）
            code = f"{secrets.randbelow(1_000_000):06d}"
            
            # ログ出力（複数の方法で出力）
            logger.info(f"[2FA] 🔑 認証コード生成: {payload.email}: {code}")
            logger.debug(f"[2FA] 📝 コード詳細 - メール: {payload.email}, コード: {code}")
            print(f"\n[2FA Console] 🔐 認証コード情報: {payload.email}: {code}\n", flush=True)

            # メール送信処理
            logger.info(f"[2FA] 📧 メール送信開始: {payload.email}")
            send_verification_code(payload.email, code)
            logger.info(f"[2FA] ✅ メール送信完了: {payload.email}")
        except Exception as e:
            error_msg = f"[2FA] ❌ 認証コード処理中にエラーが発生: {str(e)}"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr, flush=True)
            raise HTTPException(status_code=500, detail="認証コードの処理に失敗しました。")

        # データベースに保存
        expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        vc = VerificationCode(
            email=payload.email,
            code_hash=_hash_code(code),
            expires_at=expires,
            attempts_left=3
        )
        db.add(vc)
        db.commit()
        logger.info(f"[2FA] 認証コードをデータベースに保存: {payload.email}")

        return {"message": "Verification code sent"}
        
    except Exception as e:
        logger.error(f"[2FA] エラーが発生: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"認証コードの処理中にエラーが発生しました: {str(e)}"
        )

@router.post("/verify")
def verify_code(payload: Verify2FAIn, db: Session = Depends(get_db)):
    # 最新のレコードを拾う
    logger.debug(f"Verifying code for email: {payload.email}")
    vc = (
        db.query(VerificationCode)
          .filter(VerificationCode.email == payload.email)
          .order_by(VerificationCode.created_at.desc())
          .first()
    )
    if not vc:
        logger.warning(f"No verification code found for email: {payload.email}")
        raise HTTPException(status_code=400, detail="No code requested")
    current_time = datetime.now(timezone.utc)
    expires_at = vc.expires_at if vc.expires_at.tzinfo else vc.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < current_time:
        logger.warning(f"Code expired for email: {payload.email}")
        raise HTTPException(status_code=400, detail="Code expired")
    if vc.attempts_left <= 0:
        logger.warning(f"No attempts left for email: {payload.email}")
        raise HTTPException(status_code=400, detail="No attempts left")

    logger.debug(f"Checking code hash for email: {payload.email}")
    if _hash_code(payload.code) != vc.code_hash:
        vc.attempts_left -= 1
        db.commit()
        logger.warning(f"Invalid code for email: {payload.email}. Attempts left: {vc.attempts_left}")
        raise HTTPException(status_code=400, detail="Invalid code")

    logger.info(f"Successful 2FA verification for email: {payload.email}")
    return {"message": "2FA success"}

# テスト用エンドポイントを追加
@router.get("/debug/latest-code/{email}")
async def get_latest_code(email: str, db: Session = Depends(get_db)):
    """
    開発環境でのテスト用：最新の認証コード情報を取得
    注意：本番環境では無効化すること
    """
    try:
        logger.debug(f"Fetching latest verification code for email: {email}")
        vc = (
            db.query(VerificationCode)
              .filter(VerificationCode.email == email)
              .order_by(VerificationCode.created_at.desc())
              .first()
        )
        
        if not vc:
            logger.warning(f"No verification code found for email: {email}")
            raise HTTPException(status_code=404, detail="No verification code found")
        
        current_time = datetime.now(timezone.utc)
        # 期限切れの確認時にタイムゾーン情報を確実に持つようにする
        expires_at = vc.expires_at if vc.expires_at.tzinfo else vc.expires_at.replace(tzinfo=timezone.utc)
        created_at = vc.created_at if vc.created_at.tzinfo else vc.created_at.replace(tzinfo=timezone.utc)
        
        response_data = {
            "email": email,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "attempts_left": vc.attempts_left,
            "is_expired": expires_at < current_time
        }
        logger.debug(f"Verification code details: {response_data}")
        return response_data
    except Exception as e:
        logger.error(f"Error fetching verification code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
