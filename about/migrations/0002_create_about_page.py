from django.db import migrations

LEAD = (
    "Yeshua Life is a Ugandan organization based in Kampala. We work in the "
    "Karamoja region to reduce hunger through food relief, crop production, "
    "irrigation, and food processing."
)

BODY = (
    "<p>Karamoja faces repeated drought, failed harvests, and food shortages. "
    "Households have at times had little to eat beyond wild leaves. Yeshua Life "
    "was established to respond to that need, first with relief and then with "
    "farming that can continue after the emergency.</p>"
    "<p>The work is practical. We support planting and harvest, irrigation, land "
    "preparation, livestock, and training for women and young people in "
    "agriculture. Processing and machinery are part of the same effort, so food "
    "produced in the region can be kept and used.</p>"
    "<p>The organization is led by its founder, Robert Kayanja, and operates from "
    "Rubaga Road, off Nabunya, in Kampala.</p>"
)

ADDRESS = "Rubaga Road, off Nabunya\nKampala, Uganda"

AREAS = [
    (
        "Karamoja",
        "The food crisis in the region, and why the work is based there.",
        "/karamoja",
    ),
    (
        "Relief",
        "Food and direct support for households facing acute shortage.",
        "/response",
    ),
    (
        "Farming",
        "Crop production, irrigation, and community cultivation meant to last beyond a single season.",
        "/solution",
    ),
    (
        "Production",
        "Machinery, agro-processing, and food value addition.",
        "/production",
    ),
    (
        "Land preparation",
        "Clearing and opening ground so farms can be established.",
        "/landclearing",
    ),
    (
        "Field media",
        "Video from the programs, published under Global Solutions.",
        "/global-solutions/",
    ),
]


def create_about_page(apps, schema_editor):
    # Live models so the page tree, revision, and publish step stay valid.
    from about.models import AboutPage, AboutWorkArea
    from wagtail.models import Site

    if AboutPage.objects.exists():
        return

    site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
    if site is None:
        return

    parent = site.root_page
    if parent.get_children().filter(slug="about").exists():
        return

    page = AboutPage(
        title="About",
        slug="about",
        show_in_menus=False,
        organization_name="Yeshua Life Limited",
        lead=LEAD,
        image_alt="Agricultural work supported by Yeshua Life in Karamoja",
        image_caption="Karamoja, Uganda",
        organization_heading="The organization",
        body=BODY,
        work_heading="Areas of work",
        office_heading="Office",
        address=ADDRESS,
        phone="+256 740 769 952",
        email="info@yeshualifeug.com",
        primary_label="Contact",
        primary_url="/contact/",
        secondary_label="Pay online",
        secondary_url="/payments",
    )
    parent.add_child(instance=page)

    for index, (title, summary, url) in enumerate(AREAS):
        page.work_areas.add(
            AboutWorkArea(
                sort_order=index,
                title=title,
                summary=summary,
                url=url,
            )
        )
    page.save()
    page.save_revision().publish(log_action=False, skip_permission_checks=True)


def remove_about_page(apps, schema_editor):
    from about.models import AboutPage

    AboutPage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("about", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_about_page, remove_about_page),
    ]
