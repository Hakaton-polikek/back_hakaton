from rest_framework.routers import SimpleRouter

from Users.views import UserViewSet

users_router = SimpleRouter(trailing_slash=False)
users_router.register('api/users', UserViewSet)