from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from Main.utils import send_code
from Users.models import User


class UserSerializer(ModelSerializer):
    password = serializers.CharField()
    email = serializers.EmailField()

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        user = User(**validated_data)
        user.save()
        send_code(user, "Подтвердите ваш адрес электронной почты!", "подтверждения аккаунта",
                  "confirm-email")
        return user

    def update(self, instance, validated_data):
        password = validated_data.get("password")
        if password:
            validated_data["password"] = make_password(password)
        return super().update(instance, validated_data)

    class Meta:
        model = User
        fields = ["email", "password", "name"]
