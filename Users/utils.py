import datetime
import os

from django.contrib.auth.hashers import check_password, make_password
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import ValidationError, AuthenticationFailed, PermissionDenied

from Main.utils import send_code
from Users.models import User, ConfirmRequest, Token


def validate_permissions(token, role="smm"):
    """
    Функция проверки прав пользователя по токену
    """
    try:
        token = Token.objects.get(token=token)
        if token.expiration_date < datetime.date.today():
            raise ValidationError
        user = token.user
    except:
        raise AuthenticationFailed(detail={"message": "Невалидный токен!"})
    roles = [role[0] for role in user.RoleChoice.choices]
    access = False
    for i in range(roles.index(user.role)+1):
        if roles[i] == role.lower():
            access = True
    if not access:
        raise PermissionDenied(detail={"message": "Недостаточно прав для выполнения данного действия!"})
    return user


def base_authenticate(request, role):
    token = request.COOKIES.get("token")
    user = validate_permissions(token, role)
    return user, token


class UserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return base_authenticate(request, "user")


class OrgAdminAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return base_authenticate(request, "org-admin")


class DevAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return base_authenticate(request, "dev")


class AdminAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return base_authenticate(request, "admin")

def on_start():
    try:
        ADMIN_USERNAME = os.environ["ADMIN_USERNAME"]
        ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
        ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
    except:
        print("[ROOT-ADMIN] В .env нет данных рут-админки")
    else:
        try:
            admin = User.objects.get(name=ADMIN_USERNAME)
            admin.email = ADMIN_EMAIL
            if not check_password(ADMIN_PASSWORD, admin.password):
                admin.password = make_password(ADMIN_PASSWORD)
                print("[ROOT-ADMIN] Пароль изменён")
                admin.save()
        except:
            try:
                admin = User.objects.create(name=ADMIN_USERNAME, email=ADMIN_EMAIL,
                                             password=make_password(ADMIN_PASSWORD), role="admin")
                send_code(admin, "[ROOT-ADMIN] Подтверждение аккаунта", "подтверждения аккаунта",
                          "confirm-account")
                admin.save()
                print("[ROOT-ADMIN] Рут-админка добавлена, ссылка-подтверждение отправлена на почту!")
            except Exception as e:
                print(f"[ROOT-ADMIN] Неизвестная ошибка:\n {e}")


on_start()
