from django.db.models import QuerySet
from wagtail import hooks

from .models import GlobalSolutionsVideo


@hooks.register("construct_snippet_listing_queryset")
def hide_similar_clips_from_snippet_index(model, queryset: QuerySet) -> QuerySet:
    """Main video list shows only top-level entries; similar clips are edited on the parent."""
    if model is GlobalSolutionsVideo:
        return queryset.filter(parent_video__isnull=True)
    return queryset
