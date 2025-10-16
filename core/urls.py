from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('contact/', views.contact_us, name='contact_us'),
]