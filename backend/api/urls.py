from django.urls import include, path, re_path
from rest_framework import routers

from api.views import (IngredientsViewSet, RecipeViewSet, ShoppingViewSet,
                       TagsViewSet, UserCreateViewSet, UserFollowViewSet)

router_v1 = routers.DefaultRouter()


router_v1.register(r'tags', TagsViewSet, basename='tags')

router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(
    r'recipes/download_shopping_cart',
    RecipeViewSet,
    basename='download_shopping_cart',
)
router_v1.register(
    r'recipes/(?P<id>\d+)/shopping_cart', ShoppingViewSet, basename='shopping'
)

router_v1.register(r'ingredients', IngredientsViewSet, basename='ingredients')


router_v1.register(
    r'users/subscriptions', UserFollowViewSet, basename='subscriptions'
)
router_v1.register(r'users', UserCreateViewSet, basename='users')


urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls')),
    re_path('auth/', include('djoser.urls.authtoken')),
]
