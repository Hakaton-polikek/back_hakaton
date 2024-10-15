from rest_framework.routers import SimpleRouter

from Users.views import UserViewSet

users_router = SimpleRouter()
users_router.register('api/users', UserViewSet)