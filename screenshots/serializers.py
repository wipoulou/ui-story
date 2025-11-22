from rest_framework import serializers

from .models import Branch, Project, Screenshot


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'default_branch', 'created_at', 'updated_at']


class BranchSerializer(serializers.ModelSerializer):
    is_default = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = ['id', 'project', 'name', 'is_default', 'created_at', 'updated_at']

    def get_is_default(self, obj):
        return obj.is_default()


class ScreenshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screenshot
        fields = [
            'id',
            'project',
            'branch',
            'page_name',
            'viewport_size',
            'image',
            'pipeline_url',
            'metadata',
            'timestamp',
            'created_at',
        ]


class ScreenshotUploadSerializer(serializers.Serializer):
    project = serializers.CharField(max_length=200)
    branch = serializers.CharField(max_length=100)
    page_name = serializers.CharField(max_length=200)
    viewport_size = serializers.CharField(max_length=50)
    image = serializers.ImageField()
    pipeline_url = serializers.URLField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False, default=dict)
    timestamp = serializers.DateTimeField()

    def create(self, validated_data):
        project_name = validated_data.pop('project')
        branch_name = validated_data.pop('branch')

        # Get or create project
        project, _ = Project.objects.get_or_create(name=project_name)

        # Get or create branch
        branch, _ = Branch.objects.get_or_create(project=project, name=branch_name)

        # Create screenshot
        screenshot = Screenshot.objects.create(
            project=project, branch=branch, **validated_data
        )

        return screenshot
