from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from portfolio import views as portfolio_views

urlpatterns = [
    path('', include('portfolio.urls')),
    path('admin/', admin.site.urls),

    path('register/', portfolio_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='portfolio/login.html'), name='login'),
    path('logout/', portfolio_views.logout_view, name='logout'),
]