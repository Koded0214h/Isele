from django.urls import path
from . import views

urlpatterns = [
    path('webhook/whatsapp/', views.whatsapp_webhook, name='whatsapp_webhook'),
]