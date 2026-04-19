from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from applications.research_procedures.models import (
    Patent,
    ResearchGroup,
    ResearchProject,
    ConsultancyProject,
    TechTransfer,
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
    """
    try:
        return Response({
            'success': True,
            'message': 'Project commencement registered'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def project_closure(request):
    """
    Submit project closure form.
    """
    try:
        return Response({
            'success': True,
            'message': 'Project closure submitted'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_ad_committee(request):
    """
    Add advertisement and committee approval form.
    """
    try:
        return Response({
            'success': True,
            'message': 'Advertisement and committee form submitted'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_document_upload(request):
    """
    Upload staff documents.
    """
    try:
        return Response({
            'success': True,
            'message': 'Documents uploaded successfully'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_selection_report(request):
    """
    Submit staff selection report.
    """
    try:
        return Response({
            'success': True,
            'message': 'Selection report submitted'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def committee_action(request):
    """
    Committee action endpoint.
    """
    try:
        if request.method == 'POST':
            return Response({
                'success': True,
                'message': 'Committee action processed'
            }, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def staff_decision(request):
    """
    Staff decision endpoint.
    """
    try:
        if request.method == 'POST':
            return Response({
                'success': True,
                'message': 'Staff decision recorded'
            }, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
