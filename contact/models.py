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
from .blocks import InlineVideoBlock
from wagtailcodeblock.blocks import CodeBlock
from django.contrib.syndication.views import Feed
from django.urls import reverse

# Create your models here.

class VideoBlock(blocks.StructBlock):
    video_url = blocks.URLBlock(label='Video URL',required=False)
    caption = blocks.CharBlock(required=False, label='Caption')

class ImageBlogListBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=False)
    title = blocks.CharBlock(required=False)
    caption = blocks.CharBlock(required=False, label="Caption")

class ContactIndexPage(Page):
    intro = models.CharField(max_length=200)
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.PROTECT, related_name='+',blank=True,null=True
    )
    body_content = StreamField([

            ('section', blocks.StructBlock([
            ('images', blocks.ListBlock(ImageBlogListBlock(),label='Images', required=False)),
            
            ('videos', blocks.ListBlock(VideoBlock(),label='Videos',required=False,))

           ])),

    ],use_json_field=True,blank=True)
    body = RichTextField(blank=True)
    
    content_panels = Page.content_panels + [
    FieldPanel('intro'),
    FieldPanel('body'),
    FieldPanel('image'),
    FieldPanel('body_content')
    ]

class VideoBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    video_url = blocks.URLBlock(required=True)

    class Meta:
        icon = 'media'


class VideoAndRichTextBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    video_url = blocks.URLBlock(required=True)
    rich_text_content = blocks.RichTextBlock()

    class Meta:
        icon = 'media'

class ContactPage(Page):
    date = models.DateField("Post date", null=True)

    body_video = StreamField([
        ('video', InlineVideoBlock()),
    ], blank=True,use_json_field=True)

    body = RichTextField(blank=True)

    combined_content =  StreamField([
        ('combined_content', VideoAndRichTextBlock()),
        # other blocks here
        ], blank=True,use_json_field=True)   

    intro = models.CharField(max_length=200)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body')
    ]

    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.PROTECT, related_name='+',blank=True,null=True
    )

   #secondary_image = models.ManyToManyField(
    secondary_image = models.ForeignKey(
        'wagtailimages.Image',
        related_name='+',
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )

    caption = models.CharField(blank=True, max_length=250)

    # body_content = StreamField([
    #     ('section', ImageBlogListBlock()),
    # ],use_json_field=True,)

    body_content = StreamField([

            ('section', blocks.StructBlock([
            ('images', blocks.ListBlock(ImageBlogListBlock(),label='Images', required=False)),
            
            ('videos', blocks.ListBlock(VideoBlock(),label='Videos',required=False,))

           ])),

    ],use_json_field=True,blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        FieldPanel('body'),
        FieldPanel('image'),
        FieldPanel('caption'),
        FieldPanel('secondary_image'),
        FieldPanel('body_video'),
        FieldPanel('body_content'),            
        # InlinePanel('gallery_images', label="Gallery images")
    ]
