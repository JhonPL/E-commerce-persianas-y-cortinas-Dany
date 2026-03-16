from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('productos',  views.ProductoViewSet,  basename='producto')
router.register('categorias', views.CategoriaViewSet, basename='categoria')

urlpatterns = [path('', include(router.urls))]