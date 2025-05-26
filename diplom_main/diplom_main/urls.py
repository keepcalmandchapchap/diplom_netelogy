"""
URL configuration for diplom_main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from shop_api.views import RegisterView, LoginView, PositionView, UserInfoViewForOwner

router = DefaultRouter()
router.register('api/position', PositionView, 'position')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), #исходя из ответов GigaChat, то лучше оставить проверку токенов на фронтенд
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', RegisterView.as_view(), name='user'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/user_info/owner/', UserInfoViewForOwner.as_view(), name='user_info_owner')
]
urlpatterns += router.urls
