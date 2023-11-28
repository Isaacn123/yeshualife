from django.db import models
from wagtail.models import Page,Orderable
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.search import index
from modelcluster.fields import ParentalKey
# Create your models here.

class HarvestingIndexPage(Page):
    intro = models.CharField(max_length=200)

    content_panels = Page.content_panels + [
    FieldPanel('intro')
    ]

 


class HarvestingPage(Page):
    date = models.DateField("Post date", null=True)
    body = RichTextField(blank=True)
    intro = models.CharField(max_length=200)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body')
    ]

    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.PROTECT, related_name='+',blank=True,null=True
    )
    caption = models.CharField(blank=True, max_length=250)

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        FieldPanel('body'),
        FieldPanel('image'),
        FieldPanel('caption'),
        # InlinePanel('gallery_images', label="Gallery images")
    ]

# class HarvestingPageGalleryImage(Orderable):
#     page = ParentalKey(HarvestingPage, on_delete=models.CASCADE, related_name='gallery_images')
#     image = models.ForeignKey(
#         'wagtailimages.Image', on_delete=models.CASCADE, related_name='+',blank=True,
#     )
#     caption = models.CharField(blank=True, max_length=250)

#     panels = [
#         FieldPanel('image'),
#         FieldPanel('caption'),
#     ]

