from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "screenshots"

router = DefaultRouter()
router.register(r"projects", views.ProjectViewSet)
router.register(r"branches", views.BranchViewSet)
router.register(r"screenshots", views.ScreenshotViewSet)

urlpatterns = [
    # Template views
    path("", views.project_list, name="project_list"),
    path("project/<int:project_id>/", views.project_detail, name="project_detail"),
    path(
        "project/<int:project_id>/branch/<int:branch_id>/",
        views.branch_detail,
        name="branch_detail",
    ),
    path(
        "project/<int:project_id>/branch/<int:branch_id>/compare/<str:page_name>/",
        views.screenshot_comparison,
        name="screenshot_comparison",
    ),
    # API endpoints
    path("api/upload/", views.upload_screenshot, name="upload_screenshot"),
]

urlpatterns += router.urls
