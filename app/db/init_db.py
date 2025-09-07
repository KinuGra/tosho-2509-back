from app.db.base import Base, engine
from app.db import models  # noqa: F401 (import for side-effects)
print("Creating tables ...")
Base.metadata.create_all(bind=engine)
print("Done.")
