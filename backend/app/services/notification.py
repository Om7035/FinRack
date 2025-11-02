"""Multi-channel notification service (Email, SMS, Push)"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via multiple channels"""
    
    def __init__(self):
        """Initialize notification service"""
        self.sendgrid_client = None
        self.twilio_client = None
        
        # Initialize SendGrid
        if settings.SENDGRID_API_KEY:
            try:
                from sendgrid import SendGridAPIClient
                self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
                logger.info("SendGrid client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid: {e}")
        
        # Initialize Twilio
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                logger.info("Twilio client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email via SendGrid
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text content (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sendgrid_client:
            logger.warning("SendGrid not configured, skipping email")
            return False
        
        try:
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            message = Mail(
                from_email=Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def send_sms(
        self,
        to_phone: str,
        message: str
    ) -> bool:
        """
        Send SMS via Twilio
        
        Args:
            to_phone: Recipient phone number (E.164 format)
            message: SMS message content
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.twilio_client:
            logger.warning("Twilio not configured, skipping SMS")
            return False
        
        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_phone
            )
            
            logger.info(f"SMS sent to {to_phone}, SID: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    async def send_push_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send push notification via Firebase Cloud Messaging
        
        Args:
            user_id: User ID to send notification to
            title: Notification title
            body: Notification body
            data: Additional data payload
            
        Returns:
            True if sent successfully, False otherwise
        """
        # TODO: Implement FCM push notifications
        # This requires storing device tokens in the database
        logger.info(f"Push notification for user {user_id}: {title}")
        return True
    
    async def notify_transaction_alert(
        self,
        user_email: str,
        user_phone: Optional[str],
        transaction: Dict[str, Any],
        alert_type: str = "large_transaction"
    ) -> Dict[str, bool]:
        """
        Send transaction alert via configured channels
        
        Args:
            user_email: User's email
            user_phone: User's phone number
            transaction: Transaction data
            alert_type: Type of alert (large_transaction, fraud, etc.)
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {}
        
        # Email notification
        if alert_type == "large_transaction":
            subject = "Large Transaction Alert"
            html_content = f"""
            <h2>Large Transaction Detected</h2>
            <p>A large transaction was detected on your account:</p>
            <ul>
                <li><strong>Amount:</strong> ${transaction.get('amount', 0):.2f}</li>
                <li><strong>Merchant:</strong> {transaction.get('merchant_name', 'Unknown')}</li>
                <li><strong>Date:</strong> {transaction.get('date', 'Unknown')}</li>
            </ul>
            <p>If you did not make this transaction, please contact support immediately.</p>
            """
        elif alert_type == "fraud":
            subject = "⚠️ Suspicious Transaction Alert"
            html_content = f"""
            <h2 style="color: red;">Suspicious Transaction Detected</h2>
            <p>A potentially fraudulent transaction was detected:</p>
            <ul>
                <li><strong>Amount:</strong> ${transaction.get('amount', 0):.2f}</li>
                <li><strong>Merchant:</strong> {transaction.get('merchant_name', 'Unknown')}</li>
                <li><strong>Fraud Score:</strong> {transaction.get('fraud_score', 0):.1f}%</li>
            </ul>
            <p><strong>Action Required:</strong> Please review this transaction immediately.</p>
            """
        else:
            subject = "Transaction Alert"
            html_content = f"""
            <h2>Transaction Notification</h2>
            <p>Transaction: ${transaction.get('amount', 0):.2f} at {transaction.get('merchant_name', 'Unknown')}</p>
            """
        
        results['email'] = await self.send_email(user_email, subject, html_content)
        
        # SMS notification for high-priority alerts
        if user_phone and alert_type in ['fraud', 'large_transaction']:
            sms_message = f"FinRack Alert: ${transaction.get('amount', 0):.2f} transaction at {transaction.get('merchant_name', 'Unknown')}. Reply STOP to unsubscribe."
            results['sms'] = await self.send_sms(user_phone, sms_message)
        
        return results
    
    async def notify_budget_alert(
        self,
        user_email: str,
        budget: Dict[str, Any],
        alert_type: str = "warning"
    ) -> Dict[str, bool]:
        """
        Send budget alert notification
        
        Args:
            user_email: User's email
            budget: Budget data
            alert_type: warning or exceeded
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {}
        
        if alert_type == "exceeded":
            subject = "⚠️ Budget Exceeded"
            html_content = f"""
            <h2 style="color: red;">Budget Exceeded</h2>
            <p>Your budget for <strong>{budget.get('category', 'Unknown')}</strong> has been exceeded:</p>
            <ul>
                <li><strong>Budget:</strong> ${budget.get('amount', 0):.2f}</li>
                <li><strong>Spent:</strong> ${budget.get('current_spent', 0):.2f}</li>
                <li><strong>Over by:</strong> ${budget.get('current_spent', 0) - budget.get('amount', 0):.2f}</li>
            </ul>
            <p>Consider reviewing your spending in this category.</p>
            """
        else:
            subject = "Budget Warning"
            html_content = f"""
            <h2>Budget Warning</h2>
            <p>Your budget for <strong>{budget.get('category', 'Unknown')}</strong> is at {budget.get('percentage_used', 0):.1f}%:</p>
            <ul>
                <li><strong>Budget:</strong> ${budget.get('amount', 0):.2f}</li>
                <li><strong>Spent:</strong> ${budget.get('current_spent', 0):.2f}</li>
                <li><strong>Remaining:</strong> ${budget.get('remaining', 0):.2f}</li>
            </ul>
            """
        
        results['email'] = await self.send_email(user_email, subject, html_content)
        
        return results
    
    async def notify_goal_milestone(
        self,
        user_email: str,
        goal: Dict[str, Any],
        milestone: str
    ) -> Dict[str, bool]:
        """
        Send goal milestone notification
        
        Args:
            user_email: User's email
            goal: Goal data
            milestone: Milestone reached (25%, 50%, 75%, 100%)
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {}
        
        subject = f"🎯 Goal Milestone: {milestone}"
        html_content = f"""
        <h2>Congratulations! Goal Milestone Reached</h2>
        <p>You've reached <strong>{milestone}</strong> of your goal: <strong>{goal.get('name', 'Unknown')}</strong></p>
        <ul>
            <li><strong>Target:</strong> ${goal.get('target_amount', 0):.2f}</li>
            <li><strong>Current:</strong> ${goal.get('current_amount', 0):.2f}</li>
            <li><strong>Progress:</strong> {goal.get('percentage_complete', 0):.1f}%</li>
        </ul>
        <p>Keep up the great work! 🎉</p>
        """
        
        results['email'] = await self.send_email(user_email, subject, html_content)
        
        return results
    
    async def send_weekly_summary(
        self,
        user_email: str,
        summary_data: Dict[str, Any]
    ) -> bool:
        """
        Send weekly financial summary
        
        Args:
            user_email: User's email
            summary_data: Summary statistics
            
        Returns:
            True if sent successfully
        """
        subject = "📊 Your Weekly Financial Summary"
        html_content = f"""
        <h2>Weekly Financial Summary</h2>
        <h3>Spending Overview</h3>
        <ul>
            <li><strong>Total Spent:</strong> ${summary_data.get('total_spent', 0):.2f}</li>
            <li><strong>Total Income:</strong> ${summary_data.get('total_income', 0):.2f}</li>
            <li><strong>Net:</strong> ${summary_data.get('net', 0):.2f}</li>
        </ul>
        
        <h3>Top Categories</h3>
        <ul>
        """
        
        for category, amount in summary_data.get('top_categories', {}).items():
            html_content += f"<li>{category}: ${amount:.2f}</li>"
        
        html_content += """
        </ul>
        
        <h3>Budget Status</h3>
        <p>You're on track with {on_track} of {total} budgets.</p>
        
        <p>View detailed insights in your FinRack dashboard.</p>
        """.format(
            on_track=summary_data.get('budgets_on_track', 0),
            total=summary_data.get('total_budgets', 0)
        )
        
        return await self.send_email(user_email, subject, html_content)


# Global notification service instance
notification_service = NotificationService()
