from rest_framework.routers import SimpleRouter

from Main.views import TestsViewSet

main_router = SimpleRouter(trailing_slash=False)
main_router.register('api/tests', TestsViewSet)