import asyncio
import asyncpg
from urllib.parse import urlparse
import os

# Assuming monolith is running on localhost:5432 and realtime db is as well
MONOLITH_URL = "postgres://postgres:postgres@localhost:5432/handcrafts_db"
REALTIME_URL = "postgres://postgres:postgres@localhost:5432/realtime_db"

async def migrate_data():
    print("Connecting to monolith database...")
    monolith_conn = await asyncpg.connect(MONOLITH_URL)
    
    print("Connecting to realtime database...")
    realtime_conn = await asyncpg.connect(REALTIME_URL)
    
    # 1. Migrate Conversations
    print("Migrating conversations...")
    conversations = await monolith_conn.fetch("SELECT id, initiator_id, receiver_id, start_time FROM chatapp_conversation")
    for conv in conversations:
        await realtime_conn.execute(
            "INSERT INTO chat_conversations (id, initiator_id, receiver_id, start_time) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
            conv['id'], conv['initiator_id'], conv['receiver_id'], conv['start_time']
        )
        
    # 2. Migrate Messages
    print("Migrating messages...")
    messages = await monolith_conn.fetch("SELECT id, sender_id, text, attachment, conversation_id, timestamp, is_read, is_deleted, reply_to_id FROM chatapp_message")
    for msg in messages:
        await realtime_conn.execute(
            "INSERT INTO chat_messages (id, sender_id, text, attachment, conversation_id, timestamp, is_read, is_deleted, reply_to_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) ON CONFLICT DO NOTHING",
            msg['id'], msg['sender_id'], msg['text'], msg['attachment'], msg['conversation_id'], msg['timestamp'], msg['is_read'], msg['is_deleted'], msg['reply_to_id']
        )
        
    # 3. Migrate Notifications
    print("Migrating notifications...")
    notifications = await monolith_conn.fetch("SELECT id, user_id, message, image, timestamp, is_read, content_type_id, object_id FROM notifications_notification")
    for notif in notifications:
        # In the monolith, content_type_id is an int. We can map it loosely or leave it null for old notifications.
        # Here we just leave content_type as null or "legacy"
        await realtime_conn.execute(
            "INSERT INTO notifications_notification (id, user_id, message, image, timestamp, is_read, content_type, object_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT DO NOTHING",
            notif['id'], notif['user_id'], notif['message'], notif['image'], notif['timestamp'], notif['is_read'], "legacy", notif['object_id']
        )
        
    print("Data migration complete!")
    await monolith_conn.close()
    await realtime_conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_data())
