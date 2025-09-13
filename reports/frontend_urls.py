from django.urls import path
from . import frontend_views

urlpatterns = [
    # Authentication URLs
    path('login/', frontend_views.login_view, name='login'),
    path('register/', frontend_views.register_view, name='register'),
    path('logout/', frontend_views.logout_view, name='logout'),
    
    # API endpoints for frontend
    path('api/register/', frontend_views.register_api, name='register_api'),
    path('api/user/profile/', frontend_views.user_profile_api, name='user_profile'),
    path('api/auth/status/', frontend_views.auth_status, name='auth_status'),
    path('auth/session-login/', frontend_views.session_login, name='session_login'),
    
    # Home redirect
    path('', frontend_views.home_view, name='home'),
    
    # Citizen URLs
    path('citizen/dashboard/', frontend_views.citizen_dashboard, name='citizen_dashboard'),
    path('citizen/submit/', frontend_views.citizen_submit_report, name='citizen_submit'),
    
    # Admin URLs are now handled at project level with /management/ prefix
]