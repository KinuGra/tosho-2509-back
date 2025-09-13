from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, twofa, progress, ranking, gitsim
import logging
import sys

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.StreamHandler(sys.stderr)
    ]
)

# 主要なロガーのログレベルを設定
for logger_name in ['uvicorn', 'uvicorn.access', 'uvicorn.error', 'fastapi']:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

# アプリケーション固有のロガーを設定
app_logger = logging.getLogger('app')
app_logger.setLevel(logging.DEBUG)
app_logger.info('アプリケーションのログ設定を初期化しました')

app = FastAPI(title=settings.APP_NAME)

# フロントが Next.js 等の場合の CORS 設定（必要に応じて調整）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(twofa.router)
app.include_router(progress.router)
app.include_router(ranking.router)
app.include_router(gitsim.router)

@app.get("/health")
def health():
    return {"status": "ok"}
