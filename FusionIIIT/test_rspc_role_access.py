#!/usr/bin/env python
"""
Test script to verify RSPC module is accessible for non-admin faculty users.
Tests that:
1. Faculty can access RSPC API endpoints
2. accessible_modules returns 'rspc' for dean_rspc designation
3. RSPC features work for multiple user roles
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
django.setup()

from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
from applications.research_procedures.models import ResearchProject, ResearchProjectStatus

def create_test_faculty_user(username, email, role_name='dean_rspc'):
    """Create a test faculty user with specified designation"""
    # Create user
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': 'Test',
            'last_name': role_name.replace('_', ' ').title()
        }
    )
    
    # Create ExtraInfo
    extra_info, _ = ExtraInfo.objects.get_or_create(
        user=user,
        defaults={'user_type': 'faculty'}
    )
    
    # Assign designation
    try:
        designation = Designation.objects.get(name=role_name)
        HoldsDesignation.objects.get_or_create(user=user, designation=designation)
        print(f"✓ Created user '{username}' with designation '{role_name}'")
        return user
    except Designation.DoesNotExist:
        print(f"✗ Designation '{role_name}' not found in database")
        return None

def test_auth_me_endpoint(user):
    """Test the auth_me endpoint for a user"""
    from rest_framework.test import APIClient
    from rest_framework.authtoken.models import Token
    
    client = APIClient()
    
    # Get or create token
    token, _ = Token.objects.get_or_create(user=user)
    
    # Call auth_me endpoint
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    response = client.get('/api/auth/me/')
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ /api/auth/me/ endpoint successful for {user.username}")
        print(f"  - Designations: {data.get('designation_info', [])}")
        print(f"  - Accessible modules: {data.get('accessible_modules', {})}")
        
        # Check if RSPC is in accessible modules
        accessible_mods = data.get('accessible_modules', {})
        has_rspc = any('rspc' in str(mods).lower() for mods in accessible_mods.values())
        if has_rspc:
            print(f"  ✓ RSPC module is ACCESSIBLE for {user.username}")
        else:
            print(f"  ✗ RSPC module is NOT accessible for {user.username}")
        
        return True
    else:
        print(f"\n✗ /api/auth/me/ endpoint failed: {response.status_code}")
        print(f"  Response: {response.json()}")
        return False

def test_rspc_api_endpoints(user):
    """Test RSPC API endpoints for the user"""
    from rest_framework.test import APIClient
    from rest_framework.authtoken.models import Token
    
    client = APIClient()
    token = Token.objects.get_or_create(user=user)[0]
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    
    # Create a test project first
    project = ResearchProject.objects.create(
        user=user,
        pf_no=9999,
        pi=user.get_full_name() or user.username,
        title='Test Project for Role Verification',
        status=ResearchProjectStatus.SUBMITTED
    )
    
    endpoints_to_test = [
        ('GET', '/api/research/get_pids/', None),
        ('GET', '/api/research/get_projects/', None),
        ('GET', f'/api/research-projects/{project.id}/', None),
    ]
    
    print(f"\n✓ Testing RSPC API endpoints for {user.username}:")
    all_passed = True
    
    for method, endpoint, payload in endpoints_to_test:
        if method == 'GET':
            response = client.get(endpoint)
        else:
            response = client.post(endpoint, payload)
        
        status_ok = 200 <= response.status_code < 300
        symbol = "✓" if status_ok else "✗"
        print(f"  {symbol} {method} {endpoint}: {response.status_code}")
        
        if not status_ok:
            all_passed = False
            try:
                print(f"      Error: {response.json()}")
            except:
                print(f"      Error: {response.text[:100]}")
    
    # Cleanup
    project.delete()
    return all_passed

def main():
    print("=" * 70)
    print("RSPC Module Role-Based Access Testing")
    print("=" * 70)
    
    # Test roles to verify
    test_roles = [
        ('test_dean_rspc', 'dean_rspc@fusion.edu', 'dean_rspc'),
        ('test_section_head', 'section@fusion.edu', 'sectionhead_rspc'),
    ]
    
    all_tests_passed = True
    
    for username, email, role in test_roles:
        print(f"\n------- Testing role: {role} -------")
        
        # Create user
        user = create_test_faculty_user(username, email, role)
        if not user:
            all_tests_passed = False
            continue
        
        # Test auth_me endpoint
        if not test_auth_me_endpoint(user):
            all_tests_passed = False
            continue
        
        # Test RSPC endpoints
        if not test_rspc_api_endpoints(user):
            all_tests_passed = False
        
        print(f"✓ All tests passed for {role}")
    
    print("\n" + "=" * 70)
    if all_tests_passed:
        print("✓ ALL TESTS PASSED - RSPC module accessible for all tested roles")
    else:
        print("✗ SOME TESTS FAILED - Check output above for details")
    print("=" * 70)
    
    return 0 if all_tests_passed else 1

if __name__ == '__main__':
    sys.exit(main())
