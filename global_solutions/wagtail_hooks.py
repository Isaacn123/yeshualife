from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import GlobalSolutionsVideo


class GlobalSolutionsVideoViewSet(SnippetViewSet):
    """
    Main Wagtail video list shows only top-level entries.
    Optional similar clips are managed on the parent video edit page.
    """

    model = GlobalSolutionsVideo

    def get_queryset(self, request):
        return self.model._default_manager.filter(parent_video__isnull=True)


register_snippet(GlobalSolutionsVideo, viewset=GlobalSolutionsVideoViewSet)
