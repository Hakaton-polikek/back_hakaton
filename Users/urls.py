from rest_framework.routers import SimpleRouter

from Users.views import UserViewSet, AdminViewSet

users_router = SimpleRouter(trailing_slash=False)
admin_router = SimpleRouter(trailing_slash=False)
users_router.register('api/users', UserViewSet)
admin_router.register("api/admins", AdminViewSet)
