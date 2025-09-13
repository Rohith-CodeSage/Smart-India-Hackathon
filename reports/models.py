from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Extended User model with role-based permissions"""
    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='citizen',
        help_text="User role for permission management"
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_citizen(self):
        return self.role == 'citizen'


class Department(models.Model):
    """Government departments responsible for handling civic issues"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Report(models.Model):
    """Civic issue reports submitted by citizens"""
    
    CATEGORY_CHOICES = [
        ('pothole', 'Pothole'),
        ('trash', 'Trash/Waste Management'),
        ('streetlight', 'Street Light'),
        ('water', 'Water Supply'),
        ('drainage', 'Drainage'),
        ('road', 'Road Maintenance'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    
    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Location data
    latitude = models.DecimalField(
        max_digits=18, 
        decimal_places=15,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text="Latitude coordinate (-90 to 90)"
    )
    longitude = models.DecimalField(
        max_digits=18, 
        decimal_places=15,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text="Longitude coordinate (-180 to 180)"
    )
    address = models.CharField(max_length=300, blank=True, null=True)
    
    # Image upload
    image = models.ImageField(
        upload_to='reports/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Upload an image of the issue"
    )
    
    # Status and assignment
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='submitted'
    )
    assigned_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_reports'
    )
    
    # Relationships
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_reports'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_reports',
        limit_choices_to={'role': 'admin'}
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    # Additional metadata
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='medium'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['created_at']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def location_coordinates(self):
        """Returns coordinates as a tuple"""
        return (float(self.latitude), float(self.longitude))
    
    def mark_resolved(self):
        """Mark report as resolved and set resolved timestamp"""
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()
    
    def days_since_submitted(self):
        """Calculate days since report was submitted"""
        from django.utils import timezone
        return (timezone.now() - self.created_at).days
