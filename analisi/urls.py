from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('partito/<slug:slug>/', views.partito, name='partito'),
    path('programma/<int:pk>/', views.programma, name='programma'),
]
