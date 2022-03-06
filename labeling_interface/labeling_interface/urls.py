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
from labeling_interface.settings import RELATIVE_BASE_URL

urlpatterns = [
    path(RELATIVE_BASE_URL + 'aesthetics_labeling/<int:comparison_id>/', views.comparison, name='comparison'),
    path(RELATIVE_BASE_URL + 'aesthetics_labeling/static/<path:static_path>', views.image),
    path(RELATIVE_BASE_URL + 'accounts/login', views.login_view, name='login'),
    path(RELATIVE_BASE_URL + 'aesthetics_labeling/', views.aesthetics_labeling_homepage),
    path(RELATIVE_BASE_URL + 'admin/', admin.site.urls),
    path(RELATIVE_BASE_URL + '', views.index),
    path(RELATIVE_BASE_URL + 'aesthetics_labeling/email_in_use', views.email_in_use),
    path(RELATIVE_BASE_URL + 'aesthetics_labeling/informed_consent', views.informed_consent),
    path(RELATIVE_BASE_URL + 'aesthetics_labeling/request_additional/', views.request_additional),
    path(RELATIVE_BASE_URL + 'aesthetics_labeling/text_questions', views.text_questions),
    path(RELATIVE_BASE_URL + 'accounts/logout', auth_views.LogoutView.as_view()),
] + static(RELATIVE_BASE_URL + 'aesthetics_labeling/media/', document_root = settings.MEDIA_ROOT) + static(RELATIVE_BASE_URL + 'aesthetics_labeling/static/', document_root=settings.STATIC_ROOT)
