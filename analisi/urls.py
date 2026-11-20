from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('partito/<slug:slug>/', views.partito, name='partito'),
    path('programma/<int:pk>/', views.programma, name='programma'),
    path('come-giudichiamo/', views.metodo, name='metodo'),
    path('risultati/', views.risultati, name='risultati'),
    path('risultati/<slug:slug>/', views.risultati_tipo, name='risultati_tipo'),
    path('risultati/elezione/<int:pk>/', views.risultati_elezione, name='risultati_elezione'),
    path('confronto/', views.confronto, name='confronto'),
    path('confronto/<slug:slug>/', views.confronto_tema, name='confronto_tema'),
]
