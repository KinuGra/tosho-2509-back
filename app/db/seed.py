# app/db/seed.py
from app.db.base import SessionLocal
from app.db.models import Topic, Step

def seed():
    db = SessionLocal()
    try:
        # --- お題の存在チェック ---
        topic_title = "自分の編集をpushしてみよう"
        topic = db.query(Topic).filter(Topic.title == topic_title).first()

        if topic:
            print(f"⚠️ 既にお題 '{topic_title}' が存在します (id={topic.id})")
        else:
            topic = Topic(
                title=topic_title,
                description="HTMLの見出し色変更→add→commit→push"
            )
            db.add(topic)
            db.commit()
            db.refresh(topic)
            print(f"✅ お題 '{topic_title}' を作成しました (id={topic.id})")

        # --- ステップの存在チェック ---
        steps_data = [
            (1, "見出しの色を変える（エディタ編集）", 10),
            (2, "変更をステージングに追加（git add）", 15),
            (3, "コミット（git commit）", 20),
            (4, "プッシュ（git push）", 25),
        ]

        for order_no, title, xp in steps_data:
            step = (
                db.query(Step)
                .filter(Step.topic_id == topic.id, Step.order_no == order_no)
                .first()
            )
            if step:
                print(f"  ⚠️ ステップ {order_no} '{title}' は既に存在します (id={step.id})")
            else:
                step = Step(topic_id=topic.id, order_no=order_no, title=title, xp_reward=xp)
                db.add(step)
                db.commit()
                print(f"  ✅ ステップ {order_no} '{title}' を追加しました")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
