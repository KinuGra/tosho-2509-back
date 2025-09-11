# 起動
```
uvicorn app.main:app --reload --port 8000
```

# シードデータの挿入
```
python -m app.db.seed
```

# ライブラリのインストール
```
pip install -r requirements.txt
```