import sys
import logging
from fastapi import HTTPException

# ロガーの設定
logger = logging.getLogger("uvicorn.emailer")
logger.setLevel(logging.DEBUG)

def send_verification_code(email: str, code: str) -> None:
    """開発環境用の認証コード表示"""
    try:
        # 処理開始のログ
        logger.debug(f"[Emailer] 認証コード送信処理開始: {email}")
        
        # 目立つ形式でコンソールに認証コードを表示
        message = f"""
    =============================================
    🔐 認証コード情報
    ---------------------------------------------
    📧 メールアドレス: {email}
    🔑 認証コード: {code}
    ⏰ 有効期限: 5分
    =============================================
    """
        
        # 複数の方法でログを出力（確実に見えるように）
        logger.info(f"\n[Emailer] {message}")
        print(f"\n[Emailer Console] {message}", flush=True)
        print(f"[Emailer Stderr] {message}", file=sys.stderr, flush=True)
        
        # 成功ログ
        logger.info(f"[Emailer] ✅ 認証コード送信完了: {email}")
        
    except Exception as e:
        error_msg = f"[Emailer] ❌ 認証コード送信中にエラーが発生: {str(e)}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr, flush=True)
        raise HTTPException(status_code=500, detail="認証コードの送信に失敗しました。")
