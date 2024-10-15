import datetime
from math import ceil
from uuid import uuid4

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from Main.utils import check_captcha, send_code
from Users.models import User, Token, ConfirmRequest
from Users.serializers import UserSerializer
from Users.utils import UserAuthentication, validate_permissions, AdminAuthentication


@extend_schema(tags=["Пользователи"])
class UserViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [UserAuthentication]

    @extend_schema(parameters=[OpenApiParameter(location=OpenApiParameter.COOKIE, name="token"),
                               inline_serializer(name="UserGetSerializer",
                                                 fields={"id": serializers.IntegerField(required=False)})])
    @action(methods=["GET"], detail=False, url_path="get")
    def get(self, request: Request):
        token = request.COOKIES.get("token")
        user_id = request.query_params.get("id")
        if user_id:
            user_id = int(user_id)
            try:
                validate_permissions(token, "admin")
                user = User.objects.get(id=user_id)
            except:
                return Response(status=404, data={"message": "Пользователя с таким id не существует!"})
        else:
            user = request.user
        return Response(status=200, data=user.to_dict())

    @extend_schema(request=inline_serializer(name="UserAddSerializer",
                                             fields={"email": serializers.EmailField(required=True),
                                                     "password": serializers.CharField(required=True),
                                                     "name": serializers.CharField(required=False),
                                                     }))
    @action(methods=["POST"], detail=False,
            parser_classes=[JSONParser], authentication_classes=[])
    def register(self, request):
        """
        Функция регистрации пользователя
        """
        check_captcha(request.data.get("smart_token"))
        user_serializer = self.serializer_class(data=request.data)
        try:
            user_serializer.is_valid(raise_exception=True)
            user_serializer.create(user_serializer.validated_data)
        except IntegrityError:
            return Response(status=400, data={"message": "Пользователь с таким email уже существует!"})
        return Response(status=200, data={"message": "Успешная регистрация!"})

    @extend_schema(request=inline_serializer(name="UserLoginSerializer",
                                             fields={"email": serializers.EmailField(required=True),
                                                     "password": serializers.CharField(required=True)}))
    @action(methods=["POST"], detail=False, parser_classes=[JSONParser], authentication_classes=[])
    def login(self, request):
        """
        Функция авторизации пользователя
        """
        email = request.data.get("email")
        password = request.data.get("password")
        try:
            user = User.objects.get(email=email)
        except:
            return Response(status=400, data={"message": "Неверный email или пароль!"})
        if not check_password(password, user.password):
            return Response(status=400, data={"message": "Неверный email или пароль!"})
        if not user.is_active:
            return Response(status=400, data={"message": "Пользователь не подтвердил почту!"})
        expiration_date = datetime.date.today() + datetime.timedelta(days=7)
        token = Token.objects.create(user=user, token=uuid4(), expiration_date=expiration_date)
        response = Response(status=200, data={"email": user.email, "username": user.name})
        response.set_cookie("token", token.token, expires=expiration_date)
        return response

    @extend_schema(request=None, parameters=[OpenApiParameter(location=OpenApiParameter.COOKIE, name="token")])
    @action(methods=["POST"], detail=False, parser_classes=[JSONParser])
    def logout(self, request: Request):
        response = Response(status=200, data={"message": "Токен пользователя сброшен!"})
        token = Token.objects.get(token=request.auth)
        response.delete_cookie("token")
        token.delete()
        return response

    @extend_schema(request=inline_serializer(name="UserConfirmEmailSerializer",
                                             fields={"email": serializers.EmailField(required=True),
                                                     "confirm-token": serializers.UUIDField(required=True)}))
    @action(methods=["POST"], detail=False, url_path="confirm-email",
            parser_classes=[JSONParser], authentication_classes=[])
    def confirm_email(self, request):
        """
        Функция подтверждения почты
        """
        email = request.data.get("email")
        token = request.data.get("confirm-token")
        try:
            confirm_request = ConfirmRequest.objects.get(token=token)
        except:
            return Response(status=404, data={"message": "Несуществующий токен подтверждения!"})
        if email != confirm_request.user.email:
            return Response(status=404, data={"message": "Несуществующий токен подтверждения!"})
        if not confirm_request.validate():
            confirm_request.delete()
            return Response(status=400, data={"message": "Ссылка для подтверждения истекла"})
        confirm_request.user.is_active = True
        confirm_request.user.save()
        confirm_request.delete()
        return Response(status=200, data={"message": "Почта подтверждена!"})


@extend_schema(tags=["Админы"])
class AdminViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @extend_schema(parameters=[OpenApiParameter(location=OpenApiParameter.COOKIE, name="token")],
                   request=inline_serializer(name="AdminAddSerializer",
                                             fields={"email": serializers.EmailField(required=True),
                                                     "role": serializers.ChoiceField(choices=User.RoleChoice.choices)}))
    @action(methods=["POST"], detail=False, url_path="add",
            parser_classes=[JSONParser], authentication_classes=[AdminAuthentication])
    def add(self, request: Request):
        email = request.data.get("email")
        role = request.data.get("role")
        try:
            user = User.objects.get(email=email)
        except:
            return Response(status=404, data={"message": "Пользователя с таким email не существует!"})
        user.role = role
        user.save()
        user.password = make_password(uuid4().hex)
        Token.objects.filter(user=user).delete()
        send_code(user, f"Сброс пароля в связи с выдачей роли {role}")
        return Response(status=200, data={"message": "Админ добавлен!"})

    @extend_schema(parameters=[OpenApiParameter(location=OpenApiParameter.COOKIE, name="token"),
                               inline_serializer(name="AdminsGetSerializer",
                                                 fields={"limit": serializers.IntegerField(required=False),
                                                         "page": serializers.IntegerField(required=False)})])
    @action(methods=["GET"], detail=False, url_path="get", authentication_classes=[AdminAuthentication])
    def get(self, request: Request):
        try:
            limit = int(request.query_params.get("limit"))
            page = int(request.query_params.get("page"))
        except:
            return Response(status=400, data={"message": "Невалидные данные limit и(или) page"})
        admins = User.objects.filter(~Q(role="user"))
        admins = [admin.to_dict() for admin in admins]
        total_pages = ceil(len(admins) / limit)
        admins = admins[(page - 1) * limit:page * limit]
        if not admins:
            return Response(status=404, data={"message": f"Админов на {page} странице не найдено!"})
        return Response(status=200, data={"total_pages": total_pages, "admins": admins})

    @extend_schema(parameters=[OpenApiParameter(location=OpenApiParameter.COOKIE, name="token", required=False),
                               inline_serializer(name="AdminDeleteSerializer",
                                                 fields={"id": serializers.IntegerField(required=True)})])
    @action(methods=["DELETE"], detail=False, url_path="delete", authentication_classes=[AdminAuthentication])
    def delete(self, request: Request):
        admin_id = request.query_params.get("id")
        try:
            admin = User.objects.filter(~Q(role="user"), id=admin_id)[0]
        except:
            return Response(status=404, data={"message": "Админа с таким id не существует!"})
        admin.delete()
        return Response(status=200, data={"message": "Админ удалён!"})

    @extend_schema(parameters=[OpenApiParameter(location=OpenApiParameter.COOKIE, name="token")],
                   request=inline_serializer(name="AdminBanSerializer",
                                             fields={"id": serializers.IntegerField(required=True)}))
    @action(methods=["PATCH"], detail=False, url_path="ban",
            parser_classes=[JSONParser], authentication_classes=[AdminAuthentication])
    def ban(self, request: Request):
        user_id = request.data.get("id")
        try:
            admin = User.objects.get(id=user_id)
        except:
            return Response(status=404, data={"message": "Админа с таким id не существует!"})
        admin.banned = True
        admin.role = User.RoleChoice.USER
        admin.password = make_password(f"Ты забанен гад!{uuid4().hex}")
        Token.objects.filter(user=admin).delete()
        admin.save()
        return Response(status=200, data={"message": "Админ был безжалостно забанен!"})

    @extend_schema(parameters=[OpenApiParameter(location=OpenApiParameter.COOKIE, name="token")],
                   request=inline_serializer(name="AdminUnbanSerializer",
                                             fields={"id": serializers.IntegerField(required=True)}))
    @action(methods=["PATCH"], detail=False, url_path="unban",
            parser_classes=[JSONParser], authentication_classes=[AdminAuthentication])
    def unban(self, request: Request):
        user_id = request.data.get("id")
        try:
            admin = User.objects.get(id=user_id, banned=True)
        except:
            return Response(status=404, data={"message": "Забаненного админа с таким id не существует!"})
        admin.banned = False
        admin.save()
        send_code(admin, "Сброс пароля после разбана", "сброса пароля")
        return Response(status=200, data={"message": "Администратор был помилован"})

