from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UsersViewSet


router_v_1 = DefaultRouter()
router_v_1.register("ingredients", IngredientViewSet, basename="ingredients")
router_v_1.register("recipes", RecipeViewSet, basename="recipes")
router_v_1.register("tags", TagViewSet, basename="tags")
router_v_1.register("users", UsersViewSet, basename="users")


urlpatterns = [
    path("", include(router_v_1.urls)),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
