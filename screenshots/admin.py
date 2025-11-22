from django.contrib import admin

from .models import Branch, Project, Screenshot


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "default_branch", "created_at"]
    search_fields = ["name"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["project", "name", "created_at"]
    list_filter = ["project"]
    search_fields = ["name", "project__name"]


@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ["project", "branch", "page_name", "viewport_size", "timestamp"]
    list_filter = ["project", "branch", "timestamp"]
    search_fields = ["page_name", "project__name", "branch__name"]
    readonly_fields = ["created_at"]
