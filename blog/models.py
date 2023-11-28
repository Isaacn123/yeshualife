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
    caption = blocks.CharBlock(required=False, label='Caption')

class ImageBlogListBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=False)
    title = blocks.CharBlock(required=False)
    caption = blocks.CharBlock(required=False, label="Caption")
    # section_content = ImageChooserBlock(label="Image")
    # caption = blocks.CharBlock(required=False, label="Caption"),
    # title = blocks.CharBlock(required=False, label="title")

    # images = blocks.ListBlock(
    #     ImageChooserBlock(label='Image', required=False),
    #     label='Images',
    #     required=False,
    # )
    # videos = blocks.ListBlock(
    #     VideoBlock(),
    #     label='Videos',
    #     required=False,
    # )
    # caption = blocks.CharBlock(required=False, label='Caption')


class BlogIndexPage(Page):
    intro = models.CharField(max_length=200)

    content_panels = Page.content_panels + [
    FieldPanel('intro')
    ]


class BlogPage(Page):
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

        FieldPanel('body_content'),
        # InlinePanel('gallery_images', label="Gallery images")
    ]

# class ImageListPage(Page):
#     body_content = StreamField([
#         ('image_list', ImageBlogListBlock()),
#     ],use_json_field=True)

#     content_panels = Page.content_panels + [
#         FieldPanel('body_content'),

#     ]

# class BlogPageGalleryImage(Orderable):
#     page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='gallery_images')
#     image = models.ForeignKey(
#         'wagtailimages.Image', on_delete=models.PROTECT, related_name='+',blank=True,null=True
#     )
#     caption = models.CharField(blank=True, max_length=250)

#     panels = [
#         FieldPanel('image'),
#         FieldPanel('caption'),
#     ]

