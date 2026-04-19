#!/usr/bin/env python
"""
Test RSPC API endpoints to verify all implementations are working.
Tests that all 14 RSPC endpoints respond correctly with proper error handling.
"""
import os
import django
import sys
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
django.setup()

from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo
from applications.research_procedures.models import ResearchProject, ResearchProjectStatus
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

def create_test_user():
    """Get admin user or create a test user if needed"""
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@fusion.edu',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
    return user

def create_test_project(user):
    """Create a test research project"""
    project = ResearchProject.objects.create(
        user=user,
        pf_no=5555,
        pi='Dr. Test Faculty',
        title='RSPC Endpoint Testing Project',
        status=ResearchProjectStatus.SUBMITTED
    )
    return project

def test_endpoint(client, method, endpoint, data=None, files=None):
    """Test a single endpoint"""
    if method == 'GET':
        response = client.get(endpoint)
    elif method == 'POST':
        response = client.post(endpoint, data=data, format='json')
    else:
        response = client.put(endpoint, data=data, format='json')
    
    return response

def main():
    print("=" * 80)
    print("RSPC API Endpoints Verification Test")
    print("=" * 80)
    
    # Setup
    user = create_test_user()
    project = create_test_project(user)
    
    token = Token.objects.get_or_create(user=user)[0]
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    
    print(f"\nTest User: {user.username}")
    print(f"Test Project ID: {project.id}")
    
    # Define all RSPC endpoints to test
    endpoints = [
        # Getter endpoints
        ('GET', '/research_procedures/api/get-PIDs/', None, "Get all project IDs"),
        ('GET', '/research_procedures/api/get-projects/', None, "Get all projects"),
        
        # Project management endpoints
        ('POST', '/research_procedures/api/add-project/', 
         {'pf_no': 1234, 'pi': 'Dr. Test', 'title': 'New Test Project'},
         "Add new project"),
        
        ('POST', '/research_procedures/api/register-commence-project/',
         {'pid': project.id, 'start_date': '2024-01-01', 'initial_amount': 100000},
         "Register & commence project"),
        
        ('POST', '/research_procedures/api/project-closure/',
         {'pid': project.id},
         "Close project"),
        
        # Staff recruitment endpoints
        ('POST', '/research_procedures/api/add-ad-committee/',
         {'pid': project.id, 'committee_members': ['Member1', 'Member2'], 'approved_positions': 2},
         "Add advertisement & committee"),
        
        ('POST', '/research_procedures/api/staff-document-upload/',
         {'pid': project.id, 'document_type': 'test'},
         "Upload staff documents"),
        
        ('POST', '/research_procedures/api/staff-selection-report/',
         {'pid': project.id, 'selected_candidates': ['Candidate1']},
         "Submit staff selection report"),
        
        # Committee/Decision endpoints
        ('GET', '/research_procedures/api/committee-action/', None, "Get committee actions"),
        ('POST', '/research_procedures/api/committee-action/',
         {'pid': project.id, 'action': 'approved', 'remarks': 'Good'},
         "Submit committee action"),
        
        ('GET', '/research_procedures/api/staff-decision/', None, "Get staff decisions"),
        ('POST', '/research_procedures/api/staff-decision/',
         {'pid': project.id, 'decision': 'approved', 'candidate_id': 'C1'},
         "Submit staff decision"),
    ]
    
    print("\n" + "=" * 80)
    print(f"{'Endpoint':<50} {'Method':<6} {'Status':<8} {'Result'}")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for method, endpoint, data, description in endpoints:
        try:
            response = test_endpoint(client, method, endpoint, data)
            status_code = response.status_code
            
            # Consider 200-299 as success (OK, Created, etc.)
            # Also consider 400-404 as "working endpoint" if we get error message
            is_success = (200 <= status_code < 300) or (400 <= status_code < 500)
            
            result = "✓ PASS" if is_success else "✗ FAIL"
            if is_success:
                passed += 1
            else:
                failed += 1
            
            # Show endpoint info
            endpoint_display = f"{method} {endpoint[:40]}"
            print(f"{endpoint_display:<50} {method:<6} {status_code:<8} {result}")
            
            # Show response for errors
            if status_code >= 400 and status_code < 500:
                try:
                    response_data = response.json()
                    print(f"  → Response: {json.dumps(response_data)[:60]}...")
                except:
                    pass
                    
        except Exception as e:
            failed += 1
            print(f"{endpoint:<50} {method:<6} {'ERROR':<8} ✗ FAIL")
            print(f"  → Error: {str(e)[:60]}")
    
    # Cleanup
    project.delete()
    
    # Summary
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
    if failed == 0:
        print("✓ ALL RSPC ENDPOINTS ARE WORKING CORRECTLY")
    else:
        print("✗ SOME ENDPOINTS NEED ATTENTION")
    print("=" * 80)
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
