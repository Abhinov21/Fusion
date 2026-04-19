from rest_framework.routers import DefaultRouter
from applications.research_procedures.api.views import (
    PatentViewSet,
    ResearchGroupViewSet,
    ResearchProjectViewSet,
    ConsultancyProjectViewSet,
    TechTransferViewSet,
)

router = DefaultRouter()
router.register(r'patent', PatentViewSet, basename='patent')
router.register(r'research-group', ResearchGroupViewSet, basename='research-group')
router.register(r'research-project', ResearchProjectViewSet, basename='research-project')
router.register(r'consultancy-project', ConsultancyProjectViewSet, basename='consultancy-project')
router.register(r'tech-transfer', TechTransferViewSet, basename='tech-transfer')

urlpatterns = router.urls
