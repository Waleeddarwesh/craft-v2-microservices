from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Conversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(BigInteger, primary_key=True, index=True)
    initiator_id = Column(BigInteger, index=True, nullable=False)
    receiver_id = Column(BigInteger, index=True, nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, index=True)
    sender_id = Column(BigInteger, index=True, nullable=False)
    text = Column(Text, nullable=True)
    attachment = Column(String(500), nullable=True)
    conversation_id = Column(BigInteger, ForeignKey("chat_conversations.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    reply_to_id = Column(BigInteger, ForeignKey("chat_messages.id"), nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
    replies = relationship("Message", backref="parent_message", remote_side=[id])

class UserPresence(Base):
    __tablename__ = "chat_user_presence"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())

class Notification(Base):
    __tablename__ = "notifications_notification"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True, nullable=False)
    message = Column(String(255), nullable=False)
    image = Column(String(500), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    content_type = Column(String(50), nullable=True) # E.g. 'order', 'return'
    object_id = Column(BigInteger, nullable=True) # ID of the related object

class NotificationPreference(Base):
    __tablename__ = "notifications_notification_preference"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    in_app = Column(Boolean, default=True)
    email = Column(Boolean, default=True)
    push = Column(Boolean, default=True)
    sms = Column(Boolean, default=False)
