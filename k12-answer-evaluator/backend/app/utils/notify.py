"""
Shared utility: create a notification row.
Import this anywhere in the backend to fire a notification.
"""
from app.models.notification import Notification


def create_notification(db, user_id: str, type_: str, title: str, body: str = None, link: str = None):
    n = Notification(user_id=user_id, type=type_, title=title, body=body, link=link)
    db.add(n)
    db.commit()
    return n
