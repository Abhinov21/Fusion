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
