from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
import json

User = get_user_model()


# Authentication Views
def login_view(request):
    """Render login page"""
    if request.user.is_authenticated:
        if request.user.is_admin():
            return redirect('/management/dashboard/')
        else:
            return redirect('/citizen/dashboard/')
    return render(request, 'auth/login.html')


def register_view(request):
    """Render registration page"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'auth/register.html')


@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """API endpoint for user registration"""
    data = request.data.copy()
    data['role'] = 'citizen'  # Force citizen role for public registration
    
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone_number=data.get('phone_number', ''),
            role='citizen'
        )
        return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_profile_api(request):
    """API endpoint to get current user profile"""
    if not request.user.is_authenticated:
        return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


def logout_view(request):
    """Handle user logout"""
    auth_logout(request)
    return redirect('/login/')


# Dashboard Views
@login_required
def home_view(request):
    """Redirect to appropriate dashboard based on user role"""
    if request.user.is_admin():
        return redirect('/management/dashboard/')
    else:
        return redirect('/citizen/dashboard/')


@login_required
def citizen_dashboard(request):
    """Citizen dashboard - shows user's reports"""
    if request.user.is_admin():
        return redirect('/management/dashboard/')
    return render(request, 'citizen/dashboard.html', {
        'user': request.user
    })


@login_required
def citizen_submit_report(request):
    """Citizen report submission form"""
    if request.user.is_admin():
        return redirect('/management/dashboard/')
    return render(request, 'citizen/submit_report.html', {
        'user': request.user
    })


@login_required
def admin_dashboard(request):
    """Admin dashboard - overview of all reports"""
    if not request.user.is_admin():
        return redirect('/citizen/dashboard/')
    return render(request, 'admin/dashboard.html', {
        'user': request.user
    })


@login_required
def admin_reports(request):
    """Admin reports management page"""
    if not request.user.is_admin():
        return redirect('/citizen/dashboard/')
    return render(request, 'admin/reports.html', {
        'user': request.user
    })


@login_required
def admin_analytics(request):
    """Admin analytics dashboard"""
    if not request.user.is_admin():
        return redirect('/citizen/dashboard/')
    return render(request, 'admin/analytics.html', {
        'user': request.user
    })


@login_required
def admin_map_view(request):
    """Admin map view of all reports"""
    if not request.user.is_admin():
        return redirect('/citizen/dashboard/')
    return render(request, 'admin/map.html', {
        'user': request.user
    })


# API endpoint for frontend to check auth status
@csrf_exempt
@require_http_methods(["POST"])
def session_login(request):
    """Session-based login endpoint for template views"""
    try:
        data = json.loads(request.body or '{}')
    except Exception:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)
    
    user = authenticate(request, username=data.get('username'), password=data.get('password'))
    if not user:
        return JsonResponse({'detail': 'Invalid credentials'}, status=400)
    
    login(request, user)
    role = getattr(user, 'role', 'citizen')
    return JsonResponse({'ok': True, 'role': role})


@api_view(['GET'])
def auth_status(request):
    """Check authentication status"""
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'user': UserSerializer(request.user).data
        })
    return Response({'authenticated': False})