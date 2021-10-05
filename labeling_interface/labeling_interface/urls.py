"""labeling_interface URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

import aesthetics_labeling.views as views
import labeling_interface.settings as settings

urlpatterns = [
    path(settings.BASE_URL + 'admin/', admin.site.urls),
    path(settings.BASE_URL + '', views.index),
    path(settings.BASE_URL + 'aesthetics_labeling/', views.aesthetics_labeling_homepage),
    path(settings.BASE_URL + 'aesthetics_labeling/demographics', views.demographics),
    path(settings.BASE_URL + 'aesthetics_labeling/<int:comparison_id>/', views.comparison, name='comparison'),
    path(settings.BASE_URL + 'accounts/login', auth_views.LoginView.as_view(), name='login')
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
