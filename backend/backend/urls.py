from api.views import (IngredientsViewSet, RecipeViewSet, ShoppingViewSet,
                       TagsViewSet, UserCreateViewSet, UserFollowViewSet)
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers
from rest_framework.authtoken import views

router = routers.DefaultRouter()


router.register(r'tags', TagsViewSet, basename='tags')

router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(
    r'recipes/download_shopping_cart',
    RecipeViewSet,
    basename='download_shopping_cart',
)
router.register(
    r'recipes/(?P<id>\d+)/shopping_cart', ShoppingViewSet, basename='shopping'
)

router.register(r'ingredients', IngredientsViewSet, basename='ingredients')


router.register(
    r'users/subscriptions', UserFollowViewSet, basename='subscriptions'
)
router.register(r'users', UserCreateViewSet, basename='users')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('djoser.urls')),
    re_path('api/auth/', include('djoser.urls.authtoken')),
    path('api-token-auth/', views.obtain_auth_token),
    path('auth/', include('djoser.urls.jwt')),
]
