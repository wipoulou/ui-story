from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200, unique=True)
    default_branch = models.CharField(max_length=100, default="main")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Branch(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="branches"
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["project", "name"]
        ordering = ["project", "name"]

    def __str__(self):
        return f"{self.project.name}/{self.name}"

    def is_default(self):
        return self.name == self.project.default_branch


class Screenshot(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="screenshots"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="screenshots"
    )
    page_name = models.CharField(max_length=200)
    viewport_size = models.CharField(max_length=50)
    image = models.ImageField(upload_to="screenshots/%Y/%m/%d/")
    pipeline_url = models.URLField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp", "page_name"]
        indexes = [
            models.Index(fields=["project", "branch", "timestamp"]),
            models.Index(fields=["page_name"]),
        ]

    def __str__(self):
        return f"{self.project.name}/{self.branch.name}/{self.page_name} - {self.timestamp}"
