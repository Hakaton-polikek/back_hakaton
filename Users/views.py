import datetime
from uuid import uuid4

from django.contrib.auth.hashers import check_password
from django.db import IntegrityError
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from Main.utils import check_captcha
from Users.models import User, Token, ConfirmRequest
from Users.serializers import UserSerializer
from Users.utils import UserAuthentication, validate_permissions


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
