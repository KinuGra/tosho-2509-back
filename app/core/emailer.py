from app.core.config import settings

def send_verification_code(email: str, code: str) -> None:
    if settings.MAIL_BACKEND == "dummy":
        print(f"[DUMMY MAIL] to={email} code={code}")
    else:
        # SMTP 実装に差し替え
        raise NotImplementedError("SMTP backend not wired yet")
