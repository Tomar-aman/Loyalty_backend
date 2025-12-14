from firebase_admin import messaging
from .firebase import init_firebase
from users.models import User

def send_push_to_token(token: str, title: str, body: str, data: dict = None):
    init_firebase()
    msg = messaging.Message(
        token=token,
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()}
    )
    return messaging.send(msg)

def send_push_to_user(user_id: int, title: str, body: str, data: dict = None):
    user = User.objects.filter(pk=user_id).only('device_token').first()
    if not user or not user.device_token:
        raise ValueError('User device token not available.')
    return send_push_to_token(user.device_token, title, body, data)