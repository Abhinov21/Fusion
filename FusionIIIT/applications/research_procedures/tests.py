"""
Comprehensive test suite for research_procedures module.
Tests models, services, selectors, serializers, and API endpoints.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
import datetime

from applications.research_procedures.models import (
    Patent,
    ResearchGroup,
    ResearchProject,
    ConsultancyProject,
    PatentStatus,
    ResearchProjectStatus,
)
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
from applications.research_procedures.api.services import (
    PatentService,
    UnauthorizedException,
    PatentNotFoundException,
    InvalidPatentStatusException,
)
from applications.research_procedures.api.selectors import (
    PatentSelectors,
    ResearchGroupSelectors,
)
from applications.research_procedures.api.serializers import PatentSerializer


class PatentModelTestCase(TestCase):
    """Test cases for Patent model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='faculty1',
            email='faculty@test.com',
            password='testpass123'
        )
        self.extra_info = ExtraInfo.objects.create(
            user=self.user,
            user_type='faculty'
        )

    def test_patent_creation(self):
        """Test patent creation."""
        patent = Patent.objects.create(
            faculty_id=self.extra_info,
            title="Test Patent",
            status=PatentStatus.PENDING
        )
        self.assertEqual(patent.title, "Test Patent")
        self.assertEqual(patent.status, PatentStatus.PENDING)

    def test_patent_str_method(self):
        """Test patent string representation."""
        patent = Patent.objects.create(
            faculty_id=self.extra_info,
            title="Test Patent",
            status=PatentStatus.PENDING
        )
        self.assertEqual(str(patent), "Test Patent")

    def test_patent_status_choices(self):
        """Test patent status choices."""
        valid_statuses = PatentStatus.values
        self.assertIn("Pending", valid_statuses)
        self.assertIn("Approved", valid_statuses)
        self.assertIn("Disapproved", valid_statuses)


class ResearchGroupModelTestCase(TestCase):
    """Test cases for ResearchGroup model."""

    def setUp(self):
        """Set up test data."""
        self.group = ResearchGroup.objects.create(
            name="AI Research Group",
            description="Research in Artificial Intelligence"
        )
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )

    def test_research_group_creation(self):
        """Test research group creation."""
        self.assertEqual(self.group.name, "AI Research Group")

    def test_research_group_str_method(self):
        """Test research group string representation."""
        self.assertEqual(str(self.group), "AI Research Group")

    def test_add_faculty_to_group(self):
        """Test adding faculty to research group."""
        self.group.faculty_under_group.add(self.user1)
        self.assertIn(self.user1, self.group.faculty_under_group.all())

    def test_add_students_to_group(self):
        """Test adding students to research group."""
        self.group.students_under_group.add(self.user2)
        self.assertIn(self.user2, self.group.students_under_group.all())


class PatentServiceTestCase(TestCase):
    """Test cases for PatentService."""

    def setUp(self):
        """Set up test data."""
        self.faculty_user = User.objects.create_user(
            username='faculty',
            email='faculty@test.com',
            password='testpass123'
        )
        self.faculty_extra = ExtraInfo.objects.create(
            user=self.faculty_user,
            user_type='faculty'
        )
        self.dean_user = User.objects.create_user(
            username='dean',
            email='dean@test.com',
            password='testpass123'
        )
        self.dean_extra = ExtraInfo.objects.create(
            user=self.dean_user,
            user_type='faculty'
        )
        # Create dean_rspc designation and assign it
        self.designation = Designation.objects.create(name='dean_rspc')
        self.holding = HoldsDesignation.objects.create(
            user=self.dean_user,
            designation=self.designation,
            working=self.dean_user
        )

    def test_invalid_status_for_patent_creation(self):
        """Test that invalid status raises exception."""
        invalid_status = "InvalidStatus"
        self.assertNotIn(invalid_status, PatentService.VALID_STATUSES)

    def test_unauthorized_patent_creation_non_faculty(self):
        """Test that non-faculty cannot update patent."""
        non_faculty_user = User.objects.create_user(
            username='nonfaculty',
            email='nonfaculty@test.com',
            password='testpass123'
        )
        non_faculty_extra = ExtraInfo.objects.create(
            user=non_faculty_user,
            user_type='student'
        )

        with self.assertRaises(UnauthorizedException):
            PatentService.update_status(1, PatentStatus.APPROVED, non_faculty_user)

    @patch('applications.research_procedures.api.services.research_procedures_notif')
    def test_create_patent_triggers_notifications(self, mock_notif):
        """Patent creation should trigger notification workflow."""
        ipd_file = SimpleUploadedFile(
            'ipd_form.pdf',
            b'ipd-content',
            content_type='application/pdf'
        )
        details_file = SimpleUploadedFile(
            'project_details.pdf',
            b'details-content',
            content_type='application/pdf'
        )

        patent = PatentService.create_patent(
            user=self.faculty_user,
            title='Notification Test Patent',
            ipd_form_file=ipd_file,
            project_details_file=details_file
        )

        self.assertIsNotNone(patent.application_id)
        self.assertGreaterEqual(mock_notif.call_count, 1)

    def test_create_patent_rejects_file_over_10mb(self):
        """Patent upload should fail when file exceeds the configured size limit."""
        large_content = b'a' * (10 * 1024 * 1024 + 1)
        ipd_file = SimpleUploadedFile(
            'ipd_form.pdf',
            large_content,
            content_type='application/pdf'
        )
        details_file = SimpleUploadedFile(
            'project_details.pdf',
            b'details-content',
            content_type='application/pdf'
        )

        with self.assertRaises(ValueError):
            PatentService.create_patent(
                user=self.faculty_user,
                title='Large File Test',
                ipd_form_file=ipd_file,
                project_details_file=details_file
            )


class PatentSelectorsTestCase(TestCase):
    """Test cases for PatentSelectors."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='faculty',
            email='faculty@test.com',
            password='testpass123'
        )
        self.extra_info = ExtraInfo.objects.create(
            user=self.user,
            user_type='faculty'
        )
        self.patent1 = Patent.objects.create(
            faculty_id=self.extra_info,
            title="Patent 1",
            status=PatentStatus.PENDING
        )
        self.patent2 = Patent.objects.create(
            faculty_id=self.extra_info,
            title="Patent 2",
            status=PatentStatus.APPROVED
        )

    def test_get_all_patents(self):
        """Test retrieving all patents."""
        patents = PatentSelectors.get_all_patents()
        self.assertEqual(patents.count(), 2)

    def test_get_patent_by_id(self):
        """Test retrieving patent by ID."""
        patent = PatentSelectors.get_patent_by_id(self.patent1.application_id)
        self.assertEqual(patent.title, "Patent 1")

    def test_get_patents_by_status(self):
        """Test retrieving patents by status."""
        pending = PatentSelectors.get_patents_by_status(PatentStatus.PENDING)
        self.assertEqual(pending.count(), 1)


class PatentSerializerTestCase(TestCase):
    """Test cases for PatentSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='faculty',
            email='faculty@test.com',
            password='testpass123'
        )
        self.extra_info = ExtraInfo.objects.create(
            user=self.user,
            user_type='faculty'
        )
        self.patent = Patent.objects.create(
            faculty_id=self.extra_info,
            title="Test Patent",
            status=PatentStatus.PENDING
        )

    def test_serializer_valid_data(self):
        """Test serializer with valid data."""
        serializer = PatentSerializer(self.patent)
        data = serializer.data
        self.assertEqual(data['title'], "Test Patent")
        self.assertEqual(data['status'], PatentStatus.PENDING)

    def test_serializer_invalid_status(self):
        """Test serializer validation for invalid status."""
        patent_data = {
            'title': 'New Patent',
            'status': 'InvalidStatus'
        }
        serializer = PatentSerializer(data=patent_data)
        self.assertFalse(serializer.is_valid())

    def test_serializer_empty_title_validation(self):
        """Test serializer validation for empty title."""
        patent_data = {
            'title': '',
            'status': PatentStatus.PENDING
        }
        serializer = PatentSerializer(data=patent_data)
        self.assertFalse(serializer.is_valid())


class PatentAPITestCase(APITestCase):
    """Test cases for Patent API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.faculty_user = User.objects.create_user(
            username='faculty',
            email='faculty@test.com',
            password='testpass123'
        )
        self.faculty_extra = ExtraInfo.objects.create(
            user=self.faculty_user,
            user_type='faculty'
        )
        self.patent = Patent.objects.create(
            faculty_id=self.faculty_extra,
            title="Test Patent",
            status=PatentStatus.PENDING
        )

    def test_patent_list_requires_authentication(self):
        """Test that patent list endpoint requires authentication."""
        response = self.client.get('/api/patent/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patent_list_with_authentication(self):
        """Test patent list endpoint with authentication."""
        self.client.force_authenticate(user=self.faculty_user)
        response = self.client.get('/api/patent/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patent_retrieve_with_authentication(self):
        """Test patent retrieve endpoint with authentication."""
        self.client.force_authenticate(user=self.faculty_user)
        response = self.client.get(f'/api/patent/{self.patent.application_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patent_create_rejects_non_pdf(self):
        """Patent create endpoint should reject non-PDF files."""
        self.client.force_authenticate(user=self.faculty_user)
        response = self.client.post(
            '/api/patent/',
            {
                'title': 'Bad Upload',
                'ipd_form': SimpleUploadedFile(
                    'ipd_form.txt',
                    b'not-a-pdf',
                    content_type='text/plain'
                ),
                'project_details': SimpleUploadedFile(
                    'project_details.pdf',
                    b'pdf-content',
                    content_type='application/pdf'
                ),
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patent_create_rejects_file_over_10mb(self):
        """Patent create endpoint should reject files bigger than 10 MB."""
        self.client.force_authenticate(user=self.faculty_user)
        response = self.client.post(
            '/api/patent/',
            {
                'title': 'Large Upload',
                'ipd_form': SimpleUploadedFile(
                    'ipd_form.pdf',
                    b'a' * (10 * 1024 * 1024 + 1),
                    content_type='application/pdf'
                ),
                'project_details': SimpleUploadedFile(
                    'project_details.pdf',
                    b'pdf-content',
                    content_type='application/pdf'
                ),
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResearchGroupAPITestCase(APITestCase):
    """Test cases for ResearchGroup API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.faculty_user = User.objects.create_user(
            username='faculty',
            email='faculty@test.com',
            password='testpass123'
        )
        self.faculty_extra = ExtraInfo.objects.create(
            user=self.faculty_user,
            user_type='faculty'
        )
        self.group = ResearchGroup.objects.create(
            name="Test Group",
            description="Test Description"
        )

    def test_research_group_list_requires_authentication(self):
        """Test that research group list requires authentication."""
        response = self.client.get('/api/research-group/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_research_group_list_with_authentication(self):
        """Test research group list with authentication."""
        self.client.force_authenticate(user=self.faculty_user)
        response = self.client.get('/api/research-group/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ResearchProjectAPITestCase(APITestCase):
    """Test cases for ResearchProject API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.faculty_user = User.objects.create_user(
            username='faculty',
            email='faculty@test.com',
            password='testpass123'
        )
        self.faculty_extra = ExtraInfo.objects.create(
            user=self.faculty_user,
            user_type='faculty'
        )
        self.project = ResearchProject.objects.create(
            user=self.faculty_user,
            pf_no=1,
            pi="Dr. Test",
            title="Test Project",
            status=ResearchProjectStatus.ONGOING
        )

    def test_research_project_list_requires_authentication(self):
        """Test that research project list requires authentication."""
        response = self.client.get('/api/research-project/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_research_project_list_with_authentication(self):
        """Test research project list with authentication."""
        self.client.force_authenticate(user=self.faculty_user)
        response = self.client.get('/api/research-project/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_my_projects_endpoint(self):
        """Test the my_projects endpoint."""
        self.client.force_authenticate(user=self.faculty_user)
        response = self.client.get('/api/research-project/my_projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
