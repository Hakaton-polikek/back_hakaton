import os
from uuid import uuid4

import requests
from django.conf.global_settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

from Users.models import ConfirmRequest
from polikek_rf.settings import SMARTCAPTCHA_ENABLED


def send_code(user, action="Подтверждение почты", action2="подтверждения почты", action_endpoint="confirm-email"):
    token = uuid4()
    ConfirmRequest.objects.filter(user=user).delete()
    ConfirmRequest.objects.create(user=user, token=token)
    html_version = 'email_message.html'
    action = "IT-Cube | " + action
    html_message = render_to_string(html_version,
                                    {
                                         "username": user.name,
                                         "action": action,
                                         "verification_code": f"{os.environ.get('FRONTEND_HOST')}/{action_endpoint}/{token}",
                                         "action_2": action2
                                     })
    send_mail(subject=action,
              message=None,
              html_message=html_message,
              from_email=EMAIL_HOST_USER,
              recipient_list=[user.email]
              )
    return user


def check_captcha(token):
    """
    Функция проверки SmartCaptcha
    """
    if not SMARTCAPTCHA_ENABLED:
        return
    resp = requests.get(
        "https://smartcaptcha.yandexcloud.net/validate",
        {
            "secret": SMARTCAPTCHA_SERVER_KEY,
            "token": token
        },
        timeout=1
    )
    if resp.status_code != 200:
        raise ValidationError(detail={"message": "Не пройдена проверка SmartCaptcha!"})
