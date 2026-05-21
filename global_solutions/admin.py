from django.contrib import admin

from .models import GlobalSolutionsBlock, GlobalSolutionsSettings, GlobalSolutionsVideo


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
    list_display = ("title", "kind", "status", "is_active", "published_at", "updated_at")
    list_filter = ("kind", "status", "is_active")
    search_fields = ("title", "description", "original_b2_key", "hls_master_manifest_key")
    ordering = ("-published_at", "kind", "sort_order")
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

