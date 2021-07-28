import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_server = "smtp.gmail.com"
port = 465  # For SSL
sender_email = 'tamamsignup@gmail.com'
password = 'T.amam.24.35.42'



def send_confirmation(recipient, token):

    message = MIMEMultipart("alternative")
    message["Subject"] = "Confirm your email - TAMAM"
    message["From"] = sender_email
    message["To"] = recipient

    html = """\
    <html>
      <body>
        <p>Welcome to TAMAM!</p>
        <p>Please click <a href=http://localhost:4000/authenticate/confirm-email/"""+token+""">here</a> to confirm your account.</p>
      </body>
    </html>
    """
    msgcontent = MIMEText(html, "html")
    message.attach(msgcontent)

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient, message.as_string())
