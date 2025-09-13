# Civic Reports System

## Overview
A Django-based civic reports application that allows citizens to submit reports about civic issues (potholes, street lights, waste management, etc.) and enables administrators to manage and respond to these reports.

## Project Structure
- **Django Framework**: Backend built with Django 5.2.6
- **Database**: SQLite for development 
- **Authentication**: Custom User model with role-based permissions (citizen/admin)
- **API**: Django REST Framework with JWT authentication
- **Frontend**: HTML templates with JavaScript for dynamic functionality

## Recent Changes
- **2025-09-13**: Successfully imported from GitHub and configured for Replit environment
- **2025-09-13**: Django development server configured on port 5000
- **2025-09-13**: All dependencies installed and database migrations applied
- **2025-09-13**: Deployment configuration added for production

## Project Architecture

### Backend Components
- **Models**: User, Department, Report models with full civic reporting functionality
- **Views**: Both REST API views and template-based frontend views
- **Authentication**: JWT tokens + session-based authentication
- **Permissions**: Role-based access control for citizens and admins

### Frontend Features
- **Citizen Dashboard**: Submit and track civic issue reports
- **Admin Dashboard**: Manage reports, analytics, and map views
- **Authentication**: Login/register pages with JavaScript integration
- **Responsive Design**: CSS styling for mobile and desktop

### Key Features
- Report submission with location (latitude/longitude) and image upload
- Category-based issue tracking (potholes, trash, streetlights, etc.)
- Status management (submitted, in_progress, resolved, rejected)
- Department assignment and priority levels
- Admin analytics and reporting tools

## Configuration
- **ALLOWED_HOSTS**: Configured for Replit proxy (`['*']`)
- **CORS**: Enabled for frontend API calls
- **Static Files**: Configured for development and production
- **Database**: SQLite with proper migrations
- **Media Files**: Image upload support configured

## Usage
1. **Development**: Django server runs on port 5000 via workflow
2. **Registration**: Users can register as citizens through the frontend
3. **Reports**: Citizens can submit civic issue reports with location and photos
4. **Administration**: Admin users can manage reports and view analytics

## Next Steps
- Create admin user via Django admin
- Add more departments and categories as needed
- Consider PostgreSQL migration for production
- Implement email notifications for report status updates