from celery import shared_task
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

@shared_task()
def send_otp_email(email, otp):
    subject = 'OTP Verification'
    message = f'Your OTP is: {otp}'
    from_email = 'carthikn1920@gmail.com'
    recipient_list = [email]
    logger.info(f'Sending OTP email to {email}')

    try:
        send_mail(subject, message, from_email, recipient_list)
        logger.info('Email sent successfully')
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")


