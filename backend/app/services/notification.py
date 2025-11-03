"""Notification service for email, SMS, and push notifications"""
from typing import Optional, Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
import redis.asyncio as redis
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via multiple channels"""
    
    def __init__(self):
        """Initialize notification clients"""
        # SendGrid for email
        self.sendgrid_client = None
        if settings.SENDGRID_API_KEY:
            self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        
        # Twilio for SMS
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
        
        # Redis for pub/sub
        self.redis_client = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis client"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send email notification
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            from_email: Sender email (optional)
            
        Returns:
            Success status
        """
        if not self.sendgrid_client:
            logger.warning("SendGrid not configured, skipping email")
            return False
        
        try:
            message = Mail(
                from_email=from_email or settings.SENDGRID_FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.sendgrid_client.send(message)
            logger.info(f"Email sent to {to_email}: {response.status_code}")
            return response.status_code == 202
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_sms(
        self,
        to_phone: str,
        message: str
    ) -> bool:
        """
        Send SMS notification
        
        Args:
            to_phone: Recipient phone number
            message: SMS message
            
        Returns:
            Success status
        """
        if not self.twilio_client:
            logger.warning("Twilio not configured, skipping SMS")
            return False
        
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_phone
            )
            
            logger.info(f"SMS sent to {to_phone}: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    async def send_push(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send push notification (placeholder for FCM/APNS)
        
        Args:
            user_id: User ID
            title: Notification title
            body: Notification body
            data: Additional data
            
        Returns:
            Success status
        """
        # TODO: Implement FCM/APNS integration
        logger.info(f"Push notification for user {user_id}: {title}")
        return True
    
    async def send_websocket(
        self,
        user_id: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send notification via WebSocket (Redis pub/sub)
        
        Args:
            user_id: User ID
            event_type: Event type
            data: Event data
            
        Returns:
            Success status
        """
        try:
            redis_client = await self._get_redis()
            
            message = {
                'type': event_type,
                'data': data,
                'timestamp': str(datetime.utcnow())
            }
            
            # Publish to user-specific channel
            channel = f"user:{user_id}"
            await redis_client.publish(channel, json.dumps(message))
            
            logger.info(f"WebSocket message sent to {channel}: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            return False
    
    async def notify_transaction_added(
        self,
        user_id: str,
        user_email: str,
        transaction: Dict[str, Any]
    ) -> None:
        """Notify user about new transaction"""
        # Send WebSocket notification
        await self.send_websocket(
            user_id=user_id,
            event_type='transaction_added',
            data=transaction
        )
        
        # Send email for large transactions (optional)
        if abs(float(transaction.get('amount', 0))) > 1000:
            await self.send_email(
                to_email=user_email,
                subject='Large Transaction Alert',
                html_content=f"""
                <h2>Large Transaction Detected</h2>
                <p>Amount: ${transaction.get('amount')}</p>
                <p>Merchant: {transaction.get('merchant_name', 'Unknown')}</p>
                <p>Date: {transaction.get('date')}</p>
                """
            )
    
    async def notify_budget_alert(
        self,
        user_id: str,
        user_email: str,
        budget: Dict[str, Any],
        percentage_used: float
    ) -> None:
        """Notify user about budget threshold"""
        message = f"Budget Alert: {budget['name']} is {percentage_used:.0f}% used"
        
        # WebSocket
        await self.send_websocket(
            user_id=user_id,
            event_type='budget_alert',
            data={'budget': budget, 'percentage_used': percentage_used}
        )
        
        # Email
        await self.send_email(
            to_email=user_email,
            subject=message,
            html_content=f"""
            <h2>Budget Alert</h2>
            <p>{budget['name']} budget is {percentage_used:.0f}% used</p>
            <p>Spent: ${budget.get('spent', 0)}</p>
            <p>Budget: ${budget.get('amount', 0)}</p>
            """
        )
    
    async def notify_goal_milestone(
        self,
        user_id: str,
        user_email: str,
        goal: Dict[str, Any],
        milestone_percentage: int
    ) -> None:
        """Notify user about goal milestone"""
        message = f"Goal Milestone: {goal['name']} is {milestone_percentage}% complete!"
        
        await self.send_websocket(
            user_id=user_id,
            event_type='goal_milestone',
            data={'goal': goal, 'percentage': milestone_percentage}
        )
        
        await self.send_email(
            to_email=user_email,
            subject=message,
            html_content=f"""
            <h2>🎉 Goal Milestone Reached!</h2>
            <p>{goal['name']} is {milestone_percentage}% complete</p>
            <p>Current: ${goal.get('current_amount', 0)}</p>
            <p>Target: ${goal.get('target_amount', 0)}</p>
            """
        )
    
    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()


# Global instance
notification_service = NotificationService()


# Fix missing import
from datetime import datetime
