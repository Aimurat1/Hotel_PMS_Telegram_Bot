import smtplib
import ssl
from email.message import EmailMessage

import random

def generate_code():
    code = str(random.randint(100000, 999999))
    return code

def send_email(email_to_send):
    # Define email sender and receiver
    email_sender = ''
    email_password = ''
    email_receiver = email_to_send

    generated_code = generate_code()
    print(generated_code)
    
    # Set the subject and body of the email
    subject = 'Код подтверждения'
    body = f"""
{generated_code}
    """

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())
    
    print("Sent")
    return generated_code
    
def main():
    send_email()
    return None

if __name__ == "__main__":
    main()