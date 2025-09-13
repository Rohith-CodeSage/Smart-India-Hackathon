from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, DepartmentViewSet, create_report_session, get_user_reports

router = DefaultRouter()
router.register('reports', ReportViewSet, basename='report')
router.register('departments', DepartmentViewSet, basename='department')

urlpatterns = [
    path('', include(router.urls)),
    # Session-based endpoints for frontend compatibility
    path('reports/create/', create_report_session, name='create_report_session'),
    path('reports/user/', get_user_reports, name='get_user_reports'),
]