import logging

logger = logging.getLogger(__name__)

async def send_push_notification(user_id: int, title: str, body: str):
    """
    Sends an FCM push notification to the user.
    """
    logger.info(f"Sending FCM to user {user_id}: {title} - {body}")
    
    # Here we would:
    # 1. Call Auth Service (via InternalHTTPClient) to get the user's FCM token
    # 2. Use firebase-admin SDK to send the message
    
    # from firebase_admin import messaging
    # message = messaging.Message(
    #     notification=messaging.Notification(title=title, body=body),
    #     token=fcm_token
    # )
    # response = messaging.send(message)
