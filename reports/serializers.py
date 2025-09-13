from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Report, Department

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with role information"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for report listing"""
    reported_by = serializers.StringRelatedField()
    assigned_department = serializers.StringRelatedField()
    assigned_to = serializers.StringRelatedField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    days_since_submitted = serializers.IntegerField(read_only=True)
    location_coordinates = serializers.ReadOnlyField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'title', 'category', 'category_display', 'status', 'status_display',
            'priority', 'priority_display', 'latitude', 'longitude', 'location_coordinates',
            'address', 'reported_by', 'assigned_department', 'assigned_to',
            'created_at', 'updated_at', 'resolved_at', 'days_since_submitted', 'image'
        ]


class ReportDetailSerializer(serializers.ModelSerializer):
    """Full serializer for report details"""
    reported_by = UserSerializer(read_only=True)
    assigned_department = DepartmentSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    days_since_submitted = serializers.IntegerField(read_only=True)
    location_coordinates = serializers.ReadOnlyField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'title', 'description', 'category', 'category_display',
            'status', 'status_display', 'priority', 'priority_display',
            'latitude', 'longitude', 'location_coordinates', 'address',
            'image', 'reported_by', 'assigned_department', 'assigned_to',
            'created_at', 'updated_at', 'resolved_at', 'days_since_submitted'
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new reports"""
    
    class Meta:
        model = Report
        fields = [
            'title', 'description', 'category', 'latitude', 'longitude',
            'address', 'image', 'priority'
        ]
        extra_kwargs = {
            'latitude': {'required': True},
            'longitude': {'required': True}
        }
    
    def create(self, validated_data):
        # Automatically set the reporting user
        validated_data['reported_by'] = self.context['request'].user
        return super().create(validated_data)


class ReportUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating report status and assignment (admin only)"""
    
    class Meta:
        model = Report
        fields = ['status', 'assigned_department', 'assigned_to', 'priority']
        
    def validate_assigned_to(self, value):
        """Ensure assigned_to user is an admin"""
        if value and not value.is_admin():
            raise serializers.ValidationError("Reports can only be assigned to admin users.")
        return value
    
    def update(self, instance, validated_data):
        # If status is being changed to resolved, set resolved_at timestamp
        if validated_data.get('status') == 'resolved' and instance.status != 'resolved':
            from django.utils import timezone
            validated_data['resolved_at'] = timezone.now()
        
        return super().update(instance, validated_data)


class AnalyticsSerializer(serializers.Serializer):
    """Serializer for analytics data"""
    total_reports = serializers.IntegerField()
    reports_by_status = serializers.DictField()
    reports_by_category = serializers.DictField()
    avg_response_time_days = serializers.FloatField()
    hotspots = serializers.ListField(
        child=serializers.DictField()
    )
    recent_activity = serializers.ListField(
        child=serializers.DictField()
    )
    monthly_trends = serializers.ListField(
        child=serializers.DictField()
    )