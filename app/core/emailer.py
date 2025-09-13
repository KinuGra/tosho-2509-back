import sys
import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.utils import formatdate
from fastapi import HTTPException
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ロガーの設定
logger = logging.getLogger("uvicorn.emailer")
logger.setLevel(logging.DEBUG)

# メール設定を環境変数から読み込み
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_verification_code(email: str, code: str) -> None:
    """認証コードをメールで送信する"""
    try:
        # 処理開始のログ
        logger.debug(f"[Emailer] 認証コード送信処理開始: {email}")
        
        # メール本文の作成
        message = f"""
=============================================
🔐 認証コード情報
---------------------------------------------
こちらの認証コードを入力してください：

🔑 認証コード: {code}

⏰ 有効期限: 5分

このメールは自動送信されています。
=============================================
"""
        
        # MIMETextオブジェクトの作成
        msg = MIMEText(message)
        msg["Subject"] = "認証コードのお知らせ"
        msg["From"] = SMTP_USER
        msg["To"] = email
        msg["Date"] = formatdate()
        
        # SMTPサーバーに接続してメール送信
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()  # TLS暗号化を有効化
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        
        # 成功ログ
        logger.info(f"[Emailer] ✅ 認証コード送信完了: {email}")
        
        # 開発環境用にコンソールにも表示
        print(f"\n[Emailer Console] 認証コード: {code}", flush=True)
        
    except Exception as e:
        error_msg = f"[Emailer] ❌ 認証コード送信中にエラーが発生: {str(e)}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr, flush=True)
        raise HTTPException(status_code=500, detail="認証コードの送信に失敗しました。")
