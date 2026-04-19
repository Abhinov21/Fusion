from rest_framework import serializers
from applications.research_procedures.models import (
    Patent,
    ResearchGroup,
    ResearchProject,
    ConsultancyProject,
    TechTransfer,
    PatentStatus,
    ResearchProjectStatus,
    ConsultancyProjectStatus,
)
from applications.globals.models import ExtraInfo
from django.contrib.auth.models import User


class ExtraInfoSerializer(serializers.ModelSerializer):
    """Serializer for ExtraInfo related to patents."""
    user = serializers.StringRelatedField()

    class Meta:
        model = ExtraInfo
        fields = ['id', 'user', 'user_type']
        read_only_fields = ['id', 'user', 'user_type']


class PatentSerializer(serializers.ModelSerializer):
    """
    Serializer for Patent model with explicit field declaration.
    Includes validation for status transitions and required fields.
    """
    faculty_id = ExtraInfoSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Patent
        fields = [
            'application_id',
            'faculty_id',
            'title',
            'ipd_form',
            'project_details',
            'ipd_form_file',
            'project_details_file',
            'status',
            'status_display',
        ]
        read_only_fields = ['application_id', 'faculty_id', 'ipd_form_file', 'project_details_file']

    def get_status_display(self, obj):
        """Get human-readable status display."""
        return obj.get_status_display()

    def validate_title(self, value):
        """Validate that title is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_status(self, value):
        """Validate that status is one of the allowed choices."""
        valid_statuses = [choice[0] for choice in PatentStatus.choices]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return value

    def validate(self, data):
        """Validate the entire patent object."""
        if 'title' not in self.initial_data or not self.initial_data.get('title'):
            raise serializers.ValidationError({
                'title': 'Title is required.'
            })
        return data


class ResearchGroupSerializer(serializers.ModelSerializer):
    """Serializer for ResearchGroup model."""
    faculty_count = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = ResearchGroup
        fields = [
            'id',
            'name',
            'faculty_under_group',
            'students_under_group',
            'description',
            'faculty_count',
            'student_count',
        ]
        read_only_fields = ['id']

    def get_faculty_count(self, obj):
        """Get count of faculty members."""
        return obj.faculty_under_group.count()

    def get_student_count(self, obj):
        """Get count of student members."""
        return obj.students_under_group.count()

    def validate_name(self, value):
        """Validate that group name is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Group name cannot be empty.")
        return value

    def validate_description(self, value):
        """Validate that description is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value


class ResearchProjectSerializer(serializers.ModelSerializer):
    """Serializer for ResearchProject model."""
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = ResearchProject
        fields = [
            'id',
            'user',
            'pf_no',
            'ptype',
            'pi',
            'co_pi',
            'title',
            'funding_agency',
            'financial_outlay',
            'status',
            'status_display',
            'start_date',
            'finish_date',
            'date_submission',
            'date_entry',
        ]
        read_only_fields = ['id', 'user', 'date_entry']

    def get_status_display(self, obj):
        """Get human-readable status display."""
        return obj.get_status_display()

    def validate_title(self, value):
        """Validate that title is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Project title cannot be empty.")
        return value

    def validate_status(self, value):
        """Validate status is one of the allowed choices."""
        valid_statuses = [choice[0] for choice in ResearchProjectStatus.choices]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return value

    def validate(self, data):
        """Validate date ranges."""
        start_date = data.get('start_date')
        finish_date = data.get('finish_date')

        if start_date and finish_date and start_date > finish_date:
            raise serializers.ValidationError(
                "Start date cannot be after finish date."
            )
        return data


class ConsultancyProjectSerializer(serializers.ModelSerializer):
    """Serializer for ConsultancyProject model."""
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = ConsultancyProject
        fields = [
            'id',
            'user',
            'pf_no',
            'consultants',
            'title',
            'client',
            'financial_outlay',
            'start_date',
            'end_date',
            'duration',
            'status',
            'status_display',
            'remarks',
            'date_entry',
        ]
        read_only_fields = ['id', 'user', 'date_entry']

    def get_status_display(self, obj):
        """Get human-readable status display."""
        return obj.get_status_display()

    def validate_title(self, value):
        """Validate that title is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Project title cannot be empty.")
        return value

    def validate_status(self, value):
        """Validate status is one of the allowed choices."""
        valid_statuses = [choice[0] for choice in ConsultancyProjectStatus.choices]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return value

    def validate(self, data):
        """Validate date ranges."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "Start date cannot be after end date."
            )
        return data


class TechTransferSerializer(serializers.ModelSerializer):
    """Serializer for TechTransfer model."""

    class Meta:
        model = TechTransfer
        fields = [
            'id',
            'user',
            'pf_no',
            'details',
        ]
        read_only_fields = ['id', 'user']

    def validate_details(self, value):
        """Validate that details are not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Details cannot be empty.")
        return value
