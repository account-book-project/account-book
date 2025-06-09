from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    activation_link = f"http://localhost:8000/api/users/activate/{uid}/{token}/"  # 배포시  배포주소로 변경필요

    subject = "회원가입 인증 이메일"
    message = f"아래 링크를 클릭하여 이메일 인증을 완료하세요:\n{activation_link}"

    send_mail(
        subject,
        message,
        from_email=None,  # DEFAULT_FROM_EMAIL 사용
        recipient_list=[user.email],
        fail_silently=False,
    )
