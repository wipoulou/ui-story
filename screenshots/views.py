from django.shortcuts import get_object_or_404, render
from itertools import groupby
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Branch, Project, Screenshot
from .serializers import (
    BranchSerializer,
    ProjectSerializer,
    ScreenshotSerializer,
    ScreenshotUploadSerializer,
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_screenshot(request):
    """API endpoint to upload a screenshot with metadata."""
    serializer = ScreenshotUploadSerializer(data=request.data)
    if serializer.is_valid():
        screenshot = serializer.save()
        return Response(
            ScreenshotSerializer(screenshot).data, status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing and retrieving projects."""

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class BranchViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing and retrieving branches."""

    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class ScreenshotViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing and retrieving screenshots."""

    queryset = Screenshot.objects.all()
    serializer_class = ScreenshotSerializer


# Template views
def project_list(request):
    """View to list all projects."""
    projects = Project.objects.all()
    return render(request, 'screenshots/project_list.html', {'projects': projects})


def project_detail(request, project_id):
    """View to show branches for a project."""
    project = get_object_or_404(Project, id=project_id)
    branches = project.branches.all()
    return render(
        request,
        'screenshots/project_detail.html',
        {'project': project, 'branches': branches},
    )


def branch_detail(request, project_id, branch_id):
    """View to show screenshots grouped by timestamp for a branch."""
    project = get_object_or_404(Project, id=project_id)
    branch = get_object_or_404(Branch, id=branch_id, project=project)

    # Get screenshots grouped by timestamp
    screenshots = branch.screenshots.all()

    # Group screenshots by timestamp
    grouped_screenshots = []
    for timestamp, group in groupby(screenshots, key=lambda x: x.timestamp):
        grouped_screenshots.append({'timestamp': timestamp, 'screenshots': list(group)})

    return render(
        request,
        'screenshots/branch_detail.html',
        {
            'project': project,
            'branch': branch,
            'grouped_screenshots': grouped_screenshots,
        },
    )


def screenshot_comparison(request, project_id, branch_id, page_name):
    """View to compare a screenshot with the same page on the default branch."""
    project = get_object_or_404(Project, id=project_id)
    branch = get_object_or_404(Branch, id=branch_id, project=project)

    # Get the latest screenshot for this page on this branch
    current_screenshot = (
        Screenshot.objects.filter(branch=branch, page_name=page_name)
        .order_by('-timestamp')
        .first()
    )

    # Get the default branch
    default_branch = Branch.objects.filter(
        project=project, name=project.default_branch
    ).first()

    # Get the latest screenshot for this page on the default branch
    default_screenshot = None
    if default_branch:
        default_screenshot = (
            Screenshot.objects.filter(branch=default_branch, page_name=page_name)
            .order_by('-timestamp')
            .first()
        )

    return render(
        request,
        'screenshots/screenshot_comparison.html',
        {
            'project': project,
            'branch': branch,
            'current_screenshot': current_screenshot,
            'default_screenshot': default_screenshot,
            'page_name': page_name,
        },
    )

