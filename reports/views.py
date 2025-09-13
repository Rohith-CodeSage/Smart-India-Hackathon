from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from datetime import timedelta
import math

from .models import Report, Department
from .serializers import (
    ReportListSerializer, ReportDetailSerializer, ReportCreateSerializer,
    ReportUpdateSerializer, DepartmentSerializer, AnalyticsSerializer
)
from .permissions import IsOwnerOrAdmin, IsAdminUser


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for Report CRUD operations with filtering and permissions"""
    
    queryset = Report.objects.select_related(
        'reported_by', 'assigned_department', 'assigned_to'
    ).all()
    
    # Filtering and search
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'status', 'priority', 'assigned_department']
    search_fields = ['title', 'description', 'address']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ReportCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReportUpdateSerializer
        elif self.action == 'retrieve':
            return ReportDetailSerializer
        return ReportListSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == 'create':
            # Any authenticated user can create reports
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update']:
            # Only admins can update reports
            permission_classes = [IsAdminUser]
        elif self.action == 'destroy':
            # Only the owner or admin can delete
            permission_classes = [IsOwnerOrAdmin]
        else:
            # View actions require authentication
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user role and query parameters"""
        queryset = self.queryset
        user = self.request.user
        
        # Citizens can only see their own reports by default
        if not user.is_admin():
            queryset = queryset.filter(reported_by=user)
        
        # Location-based filtering
        lat = self.request.query_params.get('latitude')
        lng = self.request.query_params.get('longitude')
        radius = self.request.query_params.get('radius', '5')  # Default 5km
        
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                radius = float(radius)
                # Simple distance filtering (for more accuracy, use PostGIS)
                lat_range = radius / 111.0  # Approximate km to degree
                lng_range = radius / (111.0 * math.cos(math.radians(lat)))
                
                queryset = queryset.filter(
                    latitude__gte=lat - lat_range,
                    latitude__lte=lat + lat_range,
                    longitude__gte=lng - lng_range,
                    longitude__lte=lng + lng_range
                )
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def analytics(self, request):
        """Analytics endpoint for admin dashboard"""
        
        # Basic stats
        total_reports = Report.objects.count()
        
        # Reports by status
        reports_by_status = dict(
            Report.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        
        # Reports by category
        reports_by_category = dict(
            Report.objects.values('category').annotate(count=Count('id')).values_list('category', 'count')
        )
        
        # Average response time (days from created to resolved)
        resolved_reports = Report.objects.filter(
            status='resolved', 
            resolved_at__isnull=False
        )
        
        if resolved_reports.exists():
            avg_response_time = resolved_reports.aggregate(
                avg_time=Avg(
                    ExpressionWrapper(
                        F('resolved_at') - F('created_at'), 
                        output_field=DurationField()
                    )
                )
            )['avg_time']
            avg_response_time_days = (avg_response_time.total_seconds() / 86400) if avg_response_time else 0
        else:
            avg_response_time_days = 0
        
        # Hotspots - areas with multiple reports
        hotspots = []
        reports_with_coords = Report.objects.exclude(latitude__isnull=True, longitude__isnull=True)
        
        # Simple clustering by rounding coordinates (for demo purposes)
        hotspot_data = {}
        for report in reports_with_coords:
            # Round to 3 decimal places (~100m precision)
            lat_key = round(float(report.latitude), 3)
            lng_key = round(float(report.longitude), 3)
            coord_key = (lat_key, lng_key)
            
            if coord_key not in hotspot_data:
                hotspot_data[coord_key] = {
                    'latitude': lat_key,
                    'longitude': lng_key,
                    'count': 0,
                    'categories': []
                }
            
            hotspot_data[coord_key]['count'] += 1
            hotspot_data[coord_key]['categories'].append(report.category)
        
        # Filter hotspots with multiple reports
        hotspots = [
            data for data in hotspot_data.values() 
            if data['count'] > 1
        ]
        
        # Recent activity
        recent_reports = Report.objects.order_by('-created_at')[:10]
        recent_activity = [
            {
                'id': report.id,
                'title': report.title,
                'category': report.category,
                'status': report.status,
                'created_at': report.created_at,
                'reported_by': str(report.reported_by)
            }
            for report in recent_reports
        ]
        
        # Monthly trends
        now = timezone.now()
        monthly_trends = []
        for i in range(6):  # Last 6 months
            month_start = now.replace(day=1) - timedelta(days=30 * i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end - timedelta(days=month_end.day)
            
            month_reports = Report.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            
            monthly_trends.insert(0, {
                'month': month_start.strftime('%Y-%m'),
                'count': month_reports
            })
        
        analytics_data = {
            'total_reports': total_reports,
            'reports_by_status': reports_by_status,
            'reports_by_category': reports_by_category,
            'avg_response_time_days': avg_response_time_days,
            'hotspots': hotspots,
            'recent_activity': recent_activity,
            'monthly_trends': monthly_trends
        }
        
        serializer = AnalyticsSerializer(analytics_data)
        return Response(serializer.data)


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Department CRUD operations"""
    
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminUser]
    
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['name']


# Session-based API endpoints for frontend compatibility
@csrf_exempt
@require_http_methods(["POST"])
def create_report_session(request):
    """Create a report using session authentication"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        import json
        
        # Get form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        address = request.POST.get('address')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        priority = request.POST.get('priority', 'medium')
        image = request.FILES.get('image')
        
        print(f"Received data: title={title}, category={category}, lat={latitude}, lng={longitude}")
        
        # Validate required fields
        if not all([title, description, category, address, latitude, longitude]):
            missing_fields = []
            if not title: missing_fields.append('title')
            if not description: missing_fields.append('description')
            if not category: missing_fields.append('category')
            if not address: missing_fields.append('address')
            if not latitude: missing_fields.append('latitude')
            if not longitude: missing_fields.append('longitude')
            return JsonResponse({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)
        
        # Validate latitude and longitude
        try:
            lat_val = float(latitude)
            lng_val = float(longitude)
            if not (-90 <= lat_val <= 90):
                return JsonResponse({'error': 'Invalid latitude value'}, status=400)
            if not (-180 <= lng_val <= 180):
                return JsonResponse({'error': 'Invalid longitude value'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid coordinate values'}, status=400)
        
        # Validate category
        valid_categories = ['pothole', 'trash', 'streetlight', 'water', 'drainage', 'road', 'other']
        if category not in valid_categories:
            return JsonResponse({'error': 'Invalid category'}, status=400)
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if priority not in valid_priorities:
            priority = 'medium'
        
        # Create report
        report = Report.objects.create(
            title=title,
            description=description,
            category=category,
            address=address,
            latitude=lat_val,
            longitude=lng_val,
            priority=priority,
            reported_by=request.user,
            image=image
        )
        
        print(f"Report created successfully: ID={report.id}")
        
        return JsonResponse({
            'id': report.id,
            'message': 'Report created successfully'
        }, status=201)
        
    except Exception as e:
        import traceback
        print(f"Error creating report: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
def get_user_reports(request):
    """Get reports for the current user"""
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=401)
    
    reports = Report.objects.filter(reported_by=request.user).order_by('-created_at')
    serializer = ReportListSerializer(reports, many=True)
    return Response(serializer.data)