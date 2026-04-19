"""
Selectors layer for research_procedures module.
Encapsulates all database queries and read operations.
"""

from django.db.models import QuerySet, Prefetch
from applications.research_procedures.models import (
    Patent,
    ResearchGroup,
    ResearchProject,
    ConsultancyProject,
    TechTransfer,
)


class PatentSelectors:
    """Selector class for Patent queries."""

    @staticmethod
    def get_all_patents() -> QuerySet:
        """
        Get all patents with optimized queries.

        Returns:
            QuerySet: All patent objects with related faculty info prefetched
        """
        return Patent.objects.select_related('faculty_id').all()

    @staticmethod
    def get_patent_by_id(patent_id: int) -> Patent:
        """
        Get a single patent by ID.

        Args:
            patent_id: Patent application ID

        Returns:
            Patent: The patent object

        Raises:
            Patent.DoesNotExist: If patent not found
        """
        return Patent.objects.select_related('faculty_id').get(
            application_id=patent_id
        )

    @staticmethod
    def get_patents_by_faculty(faculty_id: int) -> QuerySet:
        """
        Get all patents filed by a specific faculty.

        Args:
            faculty_id: Faculty extra info ID

        Returns:
            QuerySet: Patents filed by the faculty
        """
        return Patent.objects.select_related('faculty_id').filter(
            faculty_id=faculty_id
        )

    @staticmethod
    def get_patents_by_status(status: str) -> QuerySet:
        """
        Get all patents with a specific status.

        Args:
            status: Patent status

        Returns:
            QuerySet: Patents with the specified status
        """
        return Patent.objects.select_related('faculty_id').filter(status=status)

    @staticmethod
    def get_pending_patents() -> QuerySet:
        """
        Get all pending patents.

        Returns:
            QuerySet: All pending patents
        """
        from applications.research_procedures.models import PatentStatus
        return PatentSelectors.get_patents_by_status(PatentStatus.PENDING)


class ResearchGroupSelectors:
    """Selector class for ResearchGroup queries."""

    @staticmethod
    def get_all_research_groups() -> QuerySet:
        """
        Get all research groups with optimized queries.

        Returns:
            QuerySet: All research group objects with prefetched members
        """
        return ResearchGroup.objects.prefetch_related(
            'faculty_under_group',
            'students_under_group'
        ).all()

    @staticmethod
    def get_research_group_by_id(group_id: int) -> ResearchGroup:
        """
        Get a single research group by ID.

        Args:
            group_id: Research group ID

        Returns:
            ResearchGroup: The research group object

        Raises:
            ResearchGroup.DoesNotExist: If group not found
        """
        return ResearchGroup.objects.prefetch_related(
            'faculty_under_group',
            'students_under_group'
        ).get(id=group_id)

    @staticmethod
    def search_research_groups(query: str) -> QuerySet:
        """
        Search research groups by name or description.

        Args:
            query: Search query string

        Returns:
            QuerySet: Matching research groups
        """
        return ResearchGroup.objects.prefetch_related(
            'faculty_under_group',
            'students_under_group'
        ).filter(
            name__icontains=query
        ) | ResearchGroup.objects.filter(
            description__icontains=query
        )


class ResearchProjectSelectors:
    """Selector class for ResearchProject queries."""

    @staticmethod
    def get_all_research_projects() -> QuerySet:
        """
        Get all research projects with optimized queries.

        Returns:
            QuerySet: All research project objects
        """
        return ResearchProject.objects.select_related('user').all()

    @staticmethod
    def get_research_project_by_id(project_id: int) -> ResearchProject:
        """
        Get a single research project by ID.

        Args:
            project_id: Research project ID

        Returns:
            ResearchProject: The research project object

        Raises:
            ResearchProject.DoesNotExist: If project not found
        """
        return ResearchProject.objects.select_related('user').get(id=project_id)

    @staticmethod
    def get_projects_by_user(user) -> QuerySet:
        """
        Get all research projects created by a user.

        Args:
            user: User object

        Returns:
            QuerySet: Projects created by the user
        """
        return ResearchProject.objects.select_related('user').filter(user=user)

    @staticmethod
    def get_projects_by_status(status: str) -> QuerySet:
        """
        Get all research projects with a specific status.

        Args:
            status: Project status

        Returns:
            QuerySet: Projects with the specified status
        """
        return ResearchProject.objects.select_related('user').filter(status=status)


class ConsultancyProjectSelectors:
    """Selector class for ConsultancyProject queries."""

    @staticmethod
    def get_all_consultancy_projects() -> QuerySet:
        """
        Get all consultancy projects with optimized queries.

        Returns:
            QuerySet: All consultancy project objects
        """
        return ConsultancyProject.objects.select_related('user').all()

    @staticmethod
    def get_consultancy_project_by_id(project_id: int) -> ConsultancyProject:
        """
        Get a single consultancy project by ID.

        Args:
            project_id: Consultancy project ID

        Returns:
            ConsultancyProject: The consultancy project object

        Raises:
            ConsultancyProject.DoesNotExist: If project not found
        """
        return ConsultancyProject.objects.select_related('user').get(id=project_id)

    @staticmethod
    def get_projects_by_user(user) -> QuerySet:
        """
        Get all consultancy projects created by a user.

        Args:
            user: User object

        Returns:
            QuerySet: Projects created by the user
        """
        return ConsultancyProject.objects.select_related('user').filter(user=user)

    @staticmethod
    def get_projects_by_status(status: str) -> QuerySet:
        """
        Get all consultancy projects with a specific status.

        Args:
            status: Project status

        Returns:
            QuerySet: Projects with the specified status
        """
        return ConsultancyProject.objects.select_related('user').filter(status=status)


class TechTransferSelectors:
    """Selector class for TechTransfer queries."""

    @staticmethod
    def get_all_tech_transfers() -> QuerySet:
        """
        Get all technology transfer records.

        Returns:
            QuerySet: All tech transfer objects
        """
        return TechTransfer.objects.select_related('user').all()

    @staticmethod
    def get_tech_transfer_by_id(transfer_id: int) -> TechTransfer:
        """
        Get a single technology transfer record by ID.

        Args:
            transfer_id: Tech transfer ID

        Returns:
            TechTransfer: The tech transfer object

        Raises:
            TechTransfer.DoesNotExist: If record not found
        """
        return TechTransfer.objects.select_related('user').get(id=transfer_id)

    @staticmethod
    def get_transfers_by_user(user) -> QuerySet:
        """
        Get all technology transfer records created by a user.

        Args:
            user: User object

        Returns:
            QuerySet: Records created by the user
        """
        return TechTransfer.objects.select_related('user').filter(user=user)
