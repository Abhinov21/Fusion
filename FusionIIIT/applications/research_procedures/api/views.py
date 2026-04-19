from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
import datetime
import json

from applications.research_procedures.models import (
    Patent,
    ResearchGroup,
    ResearchProject,
    ConsultancyProject,
    TechTransfer,
    ResearchProjectStatus,
    ConsultancyProjectStatus,
)
from applications.research_procedures.api.serializers import (
    PatentSerializer,
    ResearchGroupSerializer,
    ResearchProjectSerializer,
    ConsultancyProjectSerializer,
    TechTransferSerializer,
)
from applications.research_procedures.api.selectors import (
    PatentSelectors,
    ResearchGroupSelectors,
    ResearchProjectSelectors,
    ConsultancyProjectSelectors,
    TechTransferSelectors,
)
from applications.research_procedures.api.services import (
    PatentService,
    ResearchGroupService,
    UnauthorizedException,
    PatentNotFoundException,
    InvalidPatentStatusException,
)


class PatentViewSet(ModelViewSet):
    """
    ViewSet for Patent API endpoints.
    Requires authentication for all operations.
    """
    serializer_class = PatentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'application_id'

    def get_queryset(self):
        """
        Use selector layer for optimized queries.
        """
        return PatentSelectors.get_all_patents()

    def create(self, request, *args, **kwargs):
        """Create a patent filing with faculty authorization and file validation."""
        title = request.data.get('title')
        ipd_form_file = request.FILES.get('ipd_form')
        project_details_file = request.FILES.get('project_details')

        if not title:
            return Response(
                {'error': 'Title field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not ipd_form_file or not project_details_file:
            return Response(
                {
                    'error': (
                        'Both ipd_form and project_details files are required.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            patent = PatentService.create_patent(
                user=request.user,
                title=title,
                ipd_form_file=ipd_form_file,
                project_details_file=project_details_file,
            )
            serializer = self.get_serializer(patent)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except UnauthorizedException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_status(self, request, application_id=None):
        """
        Update the status of a patent.
        Only dean_rspc can perform this action.

        Expected request body:
        {
            "status": "Approved" | "Disapproved" | "Pending"
        }
        """
        patent = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {'error': 'Status field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_patent = PatentService.update_status(
                patent.application_id,
                new_status,
                request.user
            )
            serializer = self.get_serializer(updated_patent)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UnauthorizedException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except PatentNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except InvalidPatentStatusException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResearchGroupViewSet(ModelViewSet):
    """
    ViewSet for ResearchGroup API endpoints.
    Requires authentication for all operations.
    """
    serializer_class = ResearchGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Use selector layer for optimized queries with prefetch.
        """
        return ResearchGroupSelectors.get_all_research_groups()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        """
        Search research groups by name or description.

        Query parameters:
            q: Search query string
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        groups = ResearchGroupSelectors.search_research_groups(query)
        serializer = self.get_serializer(groups, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new research group.
        Only faculty members can create groups.
        """
        try:
            faculty_ids = request.data.get('faculty_under_group', [])
            student_ids = request.data.get('students_under_group', [])

            group = ResearchGroupService.create_research_group(
                name=request.data.get('name'),
                description=request.data.get('description'),
                faculty_ids=faculty_ids,
                student_ids=student_ids,
                user=request.user
            )
            serializer = self.get_serializer(group)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except UnauthorizedException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


class ResearchProjectViewSet(ModelViewSet):
    """
    ViewSet for ResearchProject API endpoints.
    Requires authentication for all operations.
    """
    serializer_class = ResearchProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Use selector layer for optimized queries.
        """
        return ResearchProjectSelectors.get_all_research_projects()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_projects(self, request):
        """
        Get all research projects created by the current user.
        """
        projects = ResearchProjectSelectors.get_projects_by_user(request.user)
        serializer = self.get_serializer(projects, many=True)
        return Response(serializer.data)


class ConsultancyProjectViewSet(ModelViewSet):
    """
    ViewSet for ConsultancyProject API endpoints.
    Requires authentication for all operations.
    """
    serializer_class = ConsultancyProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Use selector layer for optimized queries.
        """
        return ConsultancyProjectSelectors.get_all_consultancy_projects()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_projects(self, request):
        """
        Get all consultancy projects created by the current user.
        """
        projects = ConsultancyProjectSelectors.get_projects_by_user(request.user)
        serializer = self.get_serializer(projects, many=True)
        return Response(serializer.data)


class TechTransferViewSet(ModelViewSet):
    """
    ViewSet for TechTransfer API endpoints.
    Requires authentication for all operations.
    """
    serializer_class = TechTransferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Use selector layer for optimized queries.
        """
        return TechTransferSelectors.get_all_tech_transfers()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_transfers(self, request):
        """
        Get all technology transfer records created by the current user.
        """
        transfers = TechTransferSelectors.get_transfers_by_user(request.user)
        serializer = self.get_serializer(transfers, many=True)
        return Response(serializer.data)


# ==================== RSPC Module API Endpoints ====================

from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pids(request):
    """
    Get project IDs based on user role.
    Query params: role (PI, Faculty, etc.)
    """
    try:
        role = request.query_params.get('role')
        projects = ResearchProject.objects.all()
        pids = list(projects.values_list('id', flat=True))
        return Response(pids, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_projects(request):
    """
    Get projects for given PIDs.
    Query params: pids[] (array of project IDs)
    """
    try:
        pids = request.query_params.getlist('pids[]')
        if not pids:
            return Response([], status=status.HTTP_200_OK)
        projects = ResearchProject.objects.filter(id__in=pids)
        serializer = ResearchProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prof_ids(request):
    """
    Get all professor/faculty IDs.
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        faculty = User.objects.filter(groups__name='Faculty')
        prof_ids = list(faculty.values_list('id', flat=True))
        return Response({'profIDs': prof_ids}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_budget(request):
    """
    Get budget for a project.
    Query params: pid (project ID)
    """
    try:
        pid = request.query_params.get('pid')
        if not pid:
            return Response({'error': 'pid required'}, status=status.HTTP_400_BAD_REQUEST)
        project = ResearchProject.objects.get(id=pid)
        return Response({
            'pid': pid,
            'budget': getattr(project, 'budget', 0),
            'status': getattr(project, 'status', 'Active')
        }, status=status.HTTP_200_OK)
    except ResearchProject.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_staff_positions(request):
    """
    Get staff positions available for a project.
    Query params: pid (project ID)
    """
    try:
        pid = request.query_params.get('pid')
        if not pid:
            return Response({'error': 'pid required'}, status=status.HTTP_400_BAD_REQUEST)
        project = ResearchProject.objects.get(id=pid)
        return Response({
            'pid': pid,
            'positions': []
        }, status=status.HTTP_200_OK)
    except ResearchProject.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_staff(request):
    """
    Get staff records.
    Query params: pids[] (array of project IDs), role, type
    """
    try:
        return Response([], status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_project(request):
    """
    Submit new project addition form.
    """
    try:
        serializer = ResearchProjectSerializer(data=request.data)
        if serializer.is_valid():
            project = serializer.save()
            return Response({
                'success': True,
                'message': 'Project added successfully',
                'pid': project.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_commence_project(request):
    """
    Register project commencement.
    Updates project status to Ongoing and saves start date and initial funding.
    """
    try:
        pid = request.data.get('pid')
        start_date = request.data.get('start_date')
        initial_amount = request.data.get('initial_amount')
        
        if not pid:
            return Response(
                {'error': 'Project ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = ResearchProject.objects.get(id=pid, user=request.user)
        except ResearchProject.DoesNotExist:
            return Response(
                {'error': 'Project not found or you are not authorized to update it'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update project status and dates
        project.status = ResearchProjectStatus.ONGOING
        if start_date:
            try:
                project.start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if initial_amount:
            project.financial_outlay = str(initial_amount)
        
        project.save()
        
        serializer = ResearchProjectSerializer(project)
        return Response({
            'success': True,
            'message': 'Project commencement registered',
            'project': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def project_closure(request):
    """
    Submit project closure form.
    Updates project status to Completed and stores end report.
    """
    try:
        pid = request.data.get('pid')
        end_report = request.FILES.get('end_report')
        
        if not pid:
            return Response(
                {'error': 'Project ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = ResearchProject.objects.get(id=pid, user=request.user)
        except ResearchProject.DoesNotExist:
            return Response(
                {'error': 'Project not found or you are not authorized to close it'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update project status to completed
        project.status = ResearchProjectStatus.COMPLETED
        
        # Store end report if provided
        if end_report:
            from django.core.files.storage import FileSystemStorage
            file_system = FileSystemStorage()
            file_name = file_system.save(f'end_report_{pid}_{end_report.name}', end_report)
            # Store file path in a field or as a related record
            project.remarks = file_system.url(file_name)
        
        project.save()
        
        serializer = ResearchProjectSerializer(project)
        return Response({
            'success': True,
            'message': 'Project closure submitted',
            'project': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_ad_committee(request):
    """
    Add advertisement and committee approval form.
    Stores committee composition and approval details for staff recruitment.
    """
    try:
        # Extract request data
        pid = request.data.get('pid')
        committee_members = request.data.get('committee_members', [])
        approved_positions = request.data.get('approved_positions', 0)
        
        if not pid:
            return Response(
                {'error': 'Project ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = ResearchProject.objects.get(id=pid)
        except ResearchProject.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store committee and approval information in remarks or future dedicated fields
        committee_info = {
            'committee_members': committee_members,
            'approved_positions': approved_positions,
            'approved_by': request.user.get_full_name() or request.user.username
        }
        
        project.remarks = json.dumps(committee_info)
        project.save()
        
        return Response({
            'success': True,
            'message': 'Advertisement and committee form submitted',
            'pid': pid
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_document_upload(request):
    """
    Upload staff documents.
    Stores recruitment-related documents in project records.
    """
    try:
        pid = request.data.get('pid')
        document = request.FILES.get('document')
        document_type = request.data.get('document_type', 'general')
        
        if not pid:
            return Response(
                {'error': 'Project ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not document:
            return Response(
                {'error': 'Document file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = ResearchProject.objects.get(id=pid)
        except ResearchProject.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store document
        from django.core.files.storage import FileSystemStorage
        file_system = FileSystemStorage()
        file_name = file_system.save(
            f'staff_doc_{pid}_{document_type}_{document.name}',
            document
        )
        file_url = file_system.url(file_name)
        
        return Response({
            'success': True,
            'message': 'Documents uploaded successfully',
            'file_url': file_url,
            'document_type': document_type
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_selection_report(request):
    """
    Submit staff selection report.
    Stores selection results and recommendations for staff recruitment.
    """
    try:
        pid = request.data.get('pid')
        selected_candidates = request.data.get('selected_candidates', [])
        report_document = request.FILES.get('report_document')
        
        if not pid:
            return Response(
                {'error': 'Project ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = ResearchProject.objects.get(id=pid)
        except ResearchProject.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store selection report information
        selection_info = {
            'selected_candidates': selected_candidates,
            'report_submitted_by': request.user.get_full_name() or request.user.username,
            'submission_timestamp': str(datetime.datetime.now())
        }
        
        # Store report document if provided
        if report_document:
            from django.core.files.storage import FileSystemStorage
            file_system = FileSystemStorage()
            file_name = file_system.save(
                f'selection_report_{pid}_{report_document.name}',
                report_document
            )
            selection_info['report_url'] = file_system.url(file_name)
        
        project.remarks = json.dumps(selection_info)
        project.save()
        
        return Response({
            'success': True,
            'message': 'Selection report submitted',
            'pid': pid,
            'candidate_count': len(selected_candidates)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def committee_action(request):
    """
    Committee action endpoint.
    GET: Retrieve pending committee actions
    POST: Submit committee decision/action
    """
    try:
        if request.method == 'POST':
            pid = request.data.get('pid')
            action = request.data.get('action')
            remarks = request.data.get('remarks', '')
            
            if not pid or not action:
                return Response(
                    {'error': 'Project ID and action are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                project = ResearchProject.objects.get(id=pid)
            except ResearchProject.DoesNotExist:
                return Response(
                    {'error': 'Project not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Store committee action
            action_info = {
                'action': action,
                'remarks': remarks,
                'acted_by': request.user.get_full_name() or request.user.username,
                'action_timestamp': str(datetime.datetime.now())
            }
            project.remarks = json.dumps(action_info)
            project.save()
            
            return Response({
                'success': True,
                'message': 'Committee action processed',
                'pid': pid,
                'action': action
            }, status=status.HTTP_200_OK)
        
        # GET: Return empty list for now (can be extended to fetch pending actions)
        return Response([], status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def staff_decision(request):
    """
    Staff decision endpoint.
    GET: Retrieve pending staff decisions
    POST: Submit staff recruitment decision
    """
    try:
        if request.method == 'POST':
            pid = request.data.get('pid')
            decision = request.data.get('decision')  # 'approved', 'rejected', 'pending'
            candidate_id = request.data.get('candidate_id')
            remarks = request.data.get('remarks', '')
            
            if not pid or not decision:
                return Response(
                    {'error': 'Project ID and decision are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                project = ResearchProject.objects.get(id=pid)
            except ResearchProject.DoesNotExist:
                return Response(
                    {'error': 'Project not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Store staff decision
            decision_info = {
                'decision': decision,
                'candidate_id': candidate_id,
                'remarks': remarks,
                'decided_by': request.user.get_full_name() or request.user.username,
                'decision_timestamp': str(datetime.datetime.now())
            }
            project.remarks = json.dumps(decision_info)
            project.save()
            
            return Response({
                'success': True,
                'message': 'Staff decision recorded',
                'pid': pid,
                'decision': decision
            }, status=status.HTTP_200_OK)
        
        # GET: Return empty list for now (can be extended to fetch pending decisions)
        return Response([], status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
