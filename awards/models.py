from django.db import models
from wagtail.models import Page,Orderable
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.search import index
from modelcluster.fields import ParentalKey

from wagtail import blocks
from wagtail.fields import StreamField
# Create your models here.

class AwardsIndexPage(Page):
    intro = models.CharField(max_length=200)
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.PROTECT, related_name='+',blank=True,null=True
    )
    content_panels = Page.content_panels + [
    FieldPanel('intro'),
    FieldPanel('image'),
    ]

 


class AwardsPage(Page):
    date = models.DateField("Post date", null=True)
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', blocks.ChooserBlock()),
        ('video',blocks.EmailBlock())
    ],block_counts={
    'heading': {'min_num': 1},
    'paragraph':{'min_num': 6},
    'image': {'max_num': 5},
    'video':{'max_num': 5},
}
    )
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
        FieldPanel('body'),
        FieldPanel('image'),
        FieldPanel('caption'),
        # InlinePanel('gallery_images', label="Gallery images")
    ]

class AwardsPageGalleryImage(Orderable):
    page = ParentalKey(AwardsPage, on_delete=models.PROTECT, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.PROTECT, related_name='+',blank=True,null=True
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
    ]

