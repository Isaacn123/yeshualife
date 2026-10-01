from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem


@hooks.register("construct_main_menu")
def add_about_menu_item(request, menu_items):
    """Shortcut on the admin menu so the About page can be edited directly."""
    from about.models import AboutPage

    page = AboutPage.objects.order_by("id").first()
    if page is None or not page.permissions_for_user(request.user).can_edit():
        return

    menu_items.append(
        MenuItem(
            "About page",
            reverse("wagtailadmin_pages:edit", args=[page.pk]),
            icon_name="doc-full",
            order=250,
        )
    )
