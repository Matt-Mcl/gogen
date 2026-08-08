"""gogensite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path, re_path
from django.contrib.auth import views as auth_views

from gogen import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('settings/', views.settings_view, name='settings'),
    path('register/', views.register, name='register'),

    # Scraped puzzles, addressed by date.
    re_path(r'^(?P<puzzle_type>uber|hyper|ultra)_archive(?P<puzzle_date>(\d{4})(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01]))$', views.puzzle_view, name='puzzle_view'),

    # Generated puzzles, addressed by seed. Unbounded, because dates now sit
    # behind _archive and can no longer be swallowed by a seed.
    re_path(r'^(?P<puzzle_type>uber|hyper|ultra)(?P<seed>[1-9]\d*)$', views.generated_puzzle_view, name='generated_puzzle_view'),

    # Difficulty switcher: jump to the earliest puzzle of this type not yet solved.
    re_path(r'^(?P<puzzle_type>uber|hyper|ultra)$', views.difficulty_view, name='difficulty_view'),

    path('', views.daily_view, name='daily_view'),
]
