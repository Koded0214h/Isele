"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from core import views

# It's better practice to define views in a proper views.py file, 
# but for a simple health check, defining it here is acceptable.


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("core.urls")),
    # CORRECTION: Do not call the function. Pass the function object (health)
    # The URL pattern should be '/health', not starting with a slash path('health', ...
    path('health/', views.health, name='health'),
]