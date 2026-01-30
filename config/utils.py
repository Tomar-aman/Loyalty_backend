# from django.conf import settings
from config import settings
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from settings.models import SMTPSettings

def send_mail(subject, email_template_name, context, to_email, **kwargs):
    """
    Send email using custom EmailBackend directly.
    """

    # 1. Load SMTP settings
    mail_setting = SMTPSettings.objects.last()
    if mail_setting:
        host = mail_setting.host
        host_user = mail_setting.username
        host_pass = mail_setting.password
        host_port = mail_setting.port
        use_tls = mail_setting.use_tls
        from_email = f"{mail_setting.from_email}"
    else:
        host = settings.EMAIL_HOST
        host_user = settings.EMAIL_HOST_USER
        host_pass = settings.EMAIL_HOST_PASSWORD
        host_port = settings.EMAIL_PORT
        use_tls = settings.EMAIL_USE_TLS
        from_email = f"Loyalty <{settings.EMAIL_HOST_USER}>"

    # print("SMTP Settings:", host, host_user, host_port, use_tls, from_email)
    # 2. Create EmailBackend instance (your requirement)
    backend = EmailBackend(
        host=host,
        port=host_port,
        username=host_user,
        password=host_pass,
        use_tls=use_tls,
        timeout=15
    )
    # print(backend)
    # 3. Render email template
    html_body = render_to_string(email_template_name, context)

    # 4. Bind backend to the EmailMessage (THIS was the missing step)
    email = EmailMessage(
        subject=subject,
        body=html_body,
        from_email=from_email,
        to=[to_email],
        connection=backend,        # <-- REQUIRED or backend is ignored
    )
    email.content_subtype = "html"

    # 5. Attach file if provided
    if kwargs.get("filename") and kwargs.get("file"):
        email.attach(
            kwargs["filename"],
            kwargs["file"].read(),
            "application/pdf"
        )

    # 6. Send using EmailBackend
    try:
        email.send()
        return True
    except Exception as e:
        print("Email error:", e)
        return False