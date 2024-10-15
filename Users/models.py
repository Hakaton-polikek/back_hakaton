import datetime

from django.db import models


class User(models.Model):
    class RoleChoice(models.TextChoices):
        USER = ("user", "Пользователь",)
        ADMIN = ("admin", "Администратор",)
        DEV = ("dev", "Разработчик",)

    email = models.EmailField(unique=True)
    password = models.CharField()
    is_active = models.BooleanField(default=False)
    role = models.CharField(choices=RoleChoice.choices, default=RoleChoice.USER)
    banned = models.BooleanField(default=False)
    name = models.CharField(max_length=40, blank=True, null=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"

    def to_dict(self):
        data = dict(
            id=self.pk, email=self.email, is_active=self.is_active, role=self.role,
            banned=self.banned, last_active=self.last_active
        )
        additional_data = {"name": self.name, "photo": self.photo, "inn": self.inn}
        for field in additional_data:
            if additional_data[field]:
                data[field] = additional_data[field]
        return data


class ConfirmRequest(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    token = models.UUIDField()
    datetime = models.DateTimeField(auto_created=True, auto_now_add=True)

    class Meta:
        db_table = "confirms"

    def validate(self):
        valid_datetime = datetime.datetime.now()-datetime.timedelta(minutes=10)
        return self.datetime.timestamp() > valid_datetime.timestamp()


class Token(models.Model):
    user = models.ForeignKey("User", models.CASCADE)
    token = models.UUIDField()
    expiration_date = models.DateField()


class Group(models.Model):
    class Places(models.TextChoices):
        it_cube = "it-cube", "IT-КУБ"
        cvantorium = "cvantorium", "Кванториум"
        it_cube_skopin = "it-cube-scopin", "IT-КУБ Г. Скопин"
        it_cube_sasobo = "it-cube-sasovo", "IT-КУБ Г. Сасово"
    class Specialities(models.TextChoices):
        sys_admin = "sys-admin", "Системный Администратор"
        back_dev = "back-dev", "Бэкенд-разработчик"
    place = models.CharField(choices=Places.choices)

