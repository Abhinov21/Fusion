from rest_framework.routers import DefaultRouter
from applications.research_procedures.api.views import (
    PatentViewSet,
    ResearchGroupViewSet,
    ResearchProjectViewSet,
    ConsultancyProjectViewSet,
    TechTransferViewSet,
    get_pids,
    get_projects,
    get_prof_ids,
    get_budget,
    get_staff_positions,
    get_staff,
    add_project,
    register_commence_project,
    project_closure,
    add_ad_committee,
    staff_document_upload,
    staff_selection_report,
    committee_action,
    staff_decision,
)
from django.urls import path

router = DefaultRouter()
router.register(r'patent', PatentViewSet, basename='patent')
router.register(r'research-group', ResearchGroupViewSet, basename='research-group')
router.register(r'research-project', ResearchProjectViewSet, basename='research-project')
router.register(r'consultancy-project', ConsultancyProjectViewSet, basename='consultancy-project')
router.register(r'tech-transfer', TechTransferViewSet, basename='tech-transfer')

urlpatterns = [
    # RSPC Module specific endpoints
    path('get-PIDs/', get_pids, name='get-pids'),
    path('get-projects/', get_projects, name='get-projects'),
    path('get-profIDs/', get_prof_ids, name='get-prof-ids'),
    path('get-budget/', get_budget, name='get-budget'),
    path('get-staff-positions/', get_staff_positions, name='get-staff-positions'),
    path('get-staff/', get_staff, name='get-staff'),
    path('add-project/', add_project, name='add-project'),
    path('register-commence-project/', register_commence_project, name='register-commence-project'),
    path('project-closure/', project_closure, name='project-closure'),
    path('add-ad-committee/', add_ad_committee, name='add-ad-committee'),
    path('staff-document-upload/', staff_document_upload, name='staff-document-upload'),
    path('staff-selection-report/', staff_selection_report, name='staff-selection-report'),
    path('committee-action/', committee_action, name='committee-action'),
    path('staff-decision/', staff_decision, name='staff-decision'),
] + router.urls
