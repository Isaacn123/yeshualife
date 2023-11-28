from django.db import models

# Create your models here.

from django.db import models
from wagtail.models import Page,Orderable
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.search import index
from modelcluster.fields import ParentalKey
from wagtail.images.blocks import ImageChooserBlock
# from wagtail.admin import StreamFieldPanel
from wagtail.fields import StreamField
from wagtail import blocks
# Create your models here.

class VideoBlock(blocks.StructBlock):
    video_url = blocks.URLBlock(label='Video URL',required=False)
    title = blocks.CharBlock(required=False, label='Title')
    caption = blocks.CharBlock(required=False, label='Caption')

class ImageBlogListBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=False)
    title = blocks.CharBlock(required=False)
    caption = blocks.CharBlock(required=False, label="Caption")

class CarouselBlock(blocks.StructBlock):
    image = ImageChooserBlock()

    class Meta:
        icon = 'image'

class karamojaResponseIndexPage(Page):
    intro = models.CharField(max_length=200)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
    FieldPanel('intro'),
    FieldPanel('body')
    ]

 


class karamojaResponsePage(Page):
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

    carousel = StreamField([
        ('carousel_item', CarouselBlock()),
    ],use_json_field=True, blank=True)

    body_content = StreamField([
           ('section', blocks.StructBlock([
            ('images', blocks.ListBlock(ImageBlogListBlock(required=False))),
            ('videos', blocks.ListBlock(VideoBlock(),label='Videos',required=False,))

           ])),
    ],use_json_field=True,blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        FieldPanel('body'),
        FieldPanel('image'),
        FieldPanel('caption'),
        FieldPanel("body_content"),
        FieldPanel('carousel')
        # InlinePanel('gallery_images', label="Gallery images")
    ]

