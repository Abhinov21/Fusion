from django.contrib import admin
from applications.research_procedures.models import (
    Patent,
    ResearchGroup,
    ResearchProject,
    ConsultancyProject,
    TechTransfer,
)
from django.utils.html import format_html


class PatentAdmin(admin.ModelAdmin):
    """Admin configuration for Patent model."""
    list_filter = ('status',)
    search_fields = ['title', 'application_id']
    readonly_fields = ['application_id']
    list_display = ["faculty_id", "title", "_status"]

    def _status(self, obj):
        """Display status with color coding."""
        color = "orange"
        if obj.status == "Approved":
            color = "green"
        elif obj.status == "Disapproved":
            color = "red"
        return format_html(
            '<span style="color: %s"><b>%s</b></span>' % (color, obj.status)
        )

    _status.short_description = "Status"


class ResearchGroupAdmin(admin.ModelAdmin):
    """Admin configuration for ResearchGroup model."""
    list_display = ["name", "description", "faculty_count", "student_count"]
    search_fields = ['name', 'description']
    filter_horizontal = ['faculty_under_group', 'students_under_group']

    def faculty_count(self, obj):
        """Display count of faculty in group."""
        return obj.faculty_under_group.count()

    def student_count(self, obj):
        """Display count of students in group."""
        return obj.students_under_group.count()

    faculty_count.short_description = "Faculty Members"
    student_count.short_description = "Student Members"


class ResearchProjectAdmin(admin.ModelAdmin):
    """Admin configuration for ResearchProject model."""
    list_filter = ('status', 'ptype')
    search_fields = ['title', 'pi', 'pf_no']
    list_display = ["pf_no", "pi", "title", "status"]
    readonly_fields = ['date_entry']


class ConsultancyProjectAdmin(admin.ModelAdmin):
    """Admin configuration for ConsultancyProject model."""
    list_filter = ('status',)
    search_fields = ['title', 'client', 'pf_no']
    list_display = ["pf_no", "consultants", "title", "client", "status"]
    readonly_fields = ['date_entry']


class TechTransferAdmin(admin.ModelAdmin):
    """Admin configuration for TechTransfer model."""
    list_display = ["pf_no", "details"]
    search_fields = ['details', 'pf_no']


# Register models with admin
admin.site.register(Patent, PatentAdmin)
admin.site.register(ResearchGroup, ResearchGroupAdmin)
admin.site.register(ResearchProject, ResearchProjectAdmin)
admin.site.register(ConsultancyProject, ConsultancyProjectAdmin)
admin.site.register(TechTransfer, TechTransferAdmin)
