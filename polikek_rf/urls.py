from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from Main.urls import main_router
from Users.urls import users_router, admin_router

urlpatterns = [
    path("", include(users_router.urls)),
    path("", include(main_router.urls)),
    path("", include(admin_router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),

]

