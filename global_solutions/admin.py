from django.contrib import admin

from .models import (
    Creator,
    GlobalSolutionsBlock,
    GlobalSolutionsSettings,
    GlobalSolutionsVideo,
    SolutionCategory,
)


@admin.register(SolutionCategory)
class SolutionCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "show_on_home", "is_active", "sort_order")
    list_filter = ("is_active", "show_on_home")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")


@admin.register(Creator)
class CreatorAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "bio")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")


@admin.register(GlobalSolutionsSettings)
class GlobalSolutionsSettingsAdmin(admin.ModelAdmin):
    list_display = ("page_title", "updated_at")

    def has_add_permission(self, request):
        # Enforce single record by convention (simple + safe).
        if GlobalSolutionsSettings.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(GlobalSolutionsBlock)
class GlobalSolutionsBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "sort_order", "updated_at")
    list_filter = ("category", "is_active")
    search_fields = ("title", "body")
    ordering = ("category", "sort_order", "-updated_at")


@admin.register(GlobalSolutionsVideo)
class GlobalSolutionsVideoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "creator",
        "featured",
        "views",
        "status",
        "is_active",
        "published_at",
    )
    list_filter = ("category", "status", "is_active", "featured")
    search_fields = ("title", "slug", "description", "tags", "original_b2_key", "hls_master_manifest_key")
    ordering = ("-published_at", "category", "sort_order")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "hls_master_manifest_url",
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

