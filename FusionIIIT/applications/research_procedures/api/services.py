"""
Services layer for research_procedures module.
Handles all business logic for patents, research groups, and research projects.
"""

from django.core.files.storage import FileSystemStorage
from django.db import transaction
from applications.research_procedures.models import (
    Patent,
    ResearchGroup,
    ResearchProject,
    ConsultancyProject,
    TechTransfer,
    PatentStatus,
)
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from notification.views import research_procedures_notif
import datetime


class PatentNotFoundException(Exception):
    """Raised when a patent is not found."""
    pass


class InvalidPatentStatusException(Exception):
    """Raised when an invalid status transition is attempted."""
    pass


class UnauthorizedException(Exception):
    """Raised when user is not authorized to perform an action."""
    pass


class PatentService:
    """
    Service class for Patent-related operations.
    Encapsulates all business logic for patent creation and status updates.
    """

    VALID_STATUSES = [choice[0] for choice in PatentStatus.choices]

    @staticmethod
    @transaction.atomic
    def create_patent(user, title, ipd_form_file, project_details_file):
        """
        Create a new patent filing.

        Args:
            user: The User object filing the patent
            title: Patent title
            ipd_form_file: IPD form file object
            project_details_file: Project details file object

        Returns:
            Patent: The created patent object

        Raises:
            UnauthorizedException: If user is not a faculty
            ValueError: If files are not PDF or required fields missing
        """
        try:
            user_extra_info = ExtraInfo.objects.get(user=user)
        except ExtraInfo.DoesNotExist:
            raise UnauthorizedException("User extra information not found")

        if user_extra_info.user_type != "faculty":
            raise UnauthorizedException("Only faculty members can file patents")

        # Validate files
        if not ipd_form_file.name.endswith('.pdf'):
            raise ValueError("IPD form must be a PDF file")

        if not project_details_file.name.endswith('.pdf'):
            raise ValueError("Project details must be a PDF file")

        # Create patent instance
        patent = Patent(
            faculty_id=user_extra_info,
            title=title,
            status=PatentStatus.PENDING
        )

        # Save files
        file_system = FileSystemStorage()
        ipd_form_name = file_system.save(ipd_form_file.name, ipd_form_file)
        patent.ipd_form = ipd_form_file
        patent.ipd_form_file = file_system.url(ipd_form_name)

        project_details_name = file_system.save(
            project_details_file.name,
            project_details_file
        )
        patent.project_details = project_details_file
        patent.project_details_file = file_system.url(project_details_name)

        patent.save()

        # Create notifications
        try:
            research_procedures_notif(user, user, "submitted")
            dean_rspc_designation = Designation.objects.filter(name='dean_rspc').first()
            if dean_rspc_designation:
                dean_rspc_user = HoldsDesignation.objects.get(
                    designation=dean_rspc_designation
                ).working
                research_procedures_notif(user, dean_rspc_user, "created")
        except Exception:
            # Don't fail patent creation if notifications fail
            pass

        return patent

    @staticmethod
    @transaction.atomic
    def update_status(patent_id, new_status, user):
        """
        Update the status of a patent.

        Args:
            patent_id: ID of the patent to update
            new_status: New status value
            user: User requesting the update (must be dean_rspc)

        Returns:
            Patent: The updated patent object

        Raises:
            PatentNotFoundException: If patent doesn't exist
            InvalidPatentStatusException: If status is invalid
            UnauthorizedException: If user is not dean_rspc
        """
        try:
            patent = Patent.objects.get(application_id=patent_id)
        except Patent.DoesNotExist:
            raise PatentNotFoundException(
                f"Patent with ID {patent_id} not found"
            )

        if new_status not in PatentService.VALID_STATUSES:
            raise InvalidPatentStatusException(
                f"Invalid status: {new_status}. Valid statuses are: "
                f"{', '.join(PatentService.VALID_STATUSES)}"
            )

        # Check authorization
        try:
            user_extra_info = ExtraInfo.objects.get(user=user)
            user_designations = HoldsDesignation.objects.filter(user=user)
            dean_rspc_designation = Designation.objects.filter(
                name='dean_rspc'
            ).first()

            is_dean = (
                user_designations.filter(designation=dean_rspc_designation).exists()
                and user_extra_info.user_type == "faculty"
            )

            if not is_dean:
                raise UnauthorizedException(
                    "Only Dean RSPC can update patent status"
                )
        except ExtraInfo.DoesNotExist:
            raise UnauthorizedException("User extra information not found")

        old_status = patent.status
        patent.status = new_status
        patent.save()

        # Create notification for status change
        try:
            research_procedures_notif(
                user,
                patent.faculty_id.user,
                new_status
            )
        except Exception:
            # Don't fail if notification fails
            pass

        return patent


class ResearchGroupService:
    """Service class for ResearchGroup-related operations."""

    @staticmethod
    @transaction.atomic
    def create_research_group(name, description, faculty_ids, student_ids, user):
        """
        Create a new research group.

        Args:
            name: Group name
            description: Group description
            faculty_ids: List of faculty user IDs
            student_ids: List of student user IDs
            user: User creating the group (must be faculty)

        Returns:
            ResearchGroup: The created group object

        Raises:
            UnauthorizedException: If user is not faculty
        """
        try:
            user_extra_info = ExtraInfo.objects.get(user=user)
        except ExtraInfo.DoesNotExist:
            raise UnauthorizedException("User extra information not found")

        if user_extra_info.user_type != "faculty":
            raise UnauthorizedException("Only faculty can create research groups")

        group = ResearchGroup.objects.create(
            name=name,
            description=description
        )

        # Add faculty and students
        ResearchGroupService.update_research_group_members(
            group,
            faculty_ids,
            student_ids
        )

        return group

    @staticmethod
    @transaction.atomic
    def update_research_group_members(group, faculty_ids, student_ids):
        """
        Update the Many-to-Many relationships for a research group.

        Args:
            group: ResearchGroup instance
            faculty_ids: List of faculty user IDs
            student_ids: List of student user IDs
        """
        group.faculty_under_group.clear()
        group.students_under_group.clear()

        if faculty_ids:
            group.faculty_under_group.add(*faculty_ids)

        if student_ids:
            group.students_under_group.add(*student_ids)


class ResearchProjectService:
    """Service class for ResearchProject-related operations."""

    @staticmethod
    def parse_date(date_string):
        """
        Parse a date string to a datetime object.

        Args:
            date_string: Date string in format "Month DD, YYYY"

        Returns:
            datetime or None if parsing fails
        """
        if not date_string or date_string == 'None':
            return None

        # Handle September abbreviation variations
        x = date_string
        if x.startswith("Sept."):
            x = "Sep." + x[5:]

        try:
            return datetime.datetime.strptime(x, "%B %d, %Y")
        except ValueError:
            try:
                return datetime.datetime.strptime(x, "%b. %d, %Y")
            except ValueError:
                return None

    @staticmethod
    @transaction.atomic
    def create_research_project(user, pf_no, pi, co_pi, title, funding_agency,
                               financial_outlay, status, start_date, finish_date,
                               date_submission):
        """
        Create a new research project.

        Args:
            user: User creating the project
            pf_no: Project file number
            pi: Principal investigator
            co_pi: Co-investigator
            title: Project title
            funding_agency: Funding agency name
            financial_outlay: Financial outlay amount
            status: Project status
            start_date: Start date string
            finish_date: Finish date string
            date_submission: Submission date string

        Returns:
            ResearchProject: The created project object
        """
        project = ResearchProject(
            user=user,
            pf_no=pf_no,
            pi=pi,
            co_pi=co_pi,
            title=title,
            funding_agency=funding_agency,
            financial_outlay=financial_outlay,
            status=status
        )

        project.start_date = ResearchProjectService.parse_date(start_date)
        project.finish_date = ResearchProjectService.parse_date(finish_date)
        project.date_submission = ResearchProjectService.parse_date(date_submission)

        project.save()
        return project


class ConsultancyProjectService:
    """Service class for ConsultancyProject-related operations."""

    @staticmethod
    @transaction.atomic
    def create_consultancy_project(user, pf_no, consultants, title, client,
                                   financial_outlay, start_date, end_date):
        """
        Create a new consultancy project.

        Args:
            user: User creating the project
            pf_no: Project file number
            consultants: Consultant names
            title: Project title
            client: Client name
            financial_outlay: Financial outlay amount
            start_date: Start date string
            end_date: End date string

        Returns:
            ConsultancyProject: The created project object
        """
        project = ConsultancyProject(
            user=user,
            pf_no=pf_no,
            consultants=consultants,
            title=title,
            client=client,
            financial_outlay=financial_outlay
        )

        project.start_date = ResearchProjectService.parse_date(start_date)
        project.end_date = ResearchProjectService.parse_date(end_date)

        project.save()
        return project


class TechTransferService:
    """Service class for TechTransfer-related operations."""

    @staticmethod
    @transaction.atomic
    def create_tech_transfer(user, pf_no, details):
        """
        Create a new technology transfer record.

        Args:
            user: User creating the record
            pf_no: Project file number
            details: Transfer details

        Returns:
            TechTransfer: The created record object
        """
        tech_transfer = TechTransfer(
            user=user,
            pf_no=pf_no,
            details=details
        )
        tech_transfer.save()
        return tech_transfer
