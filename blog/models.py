from itertools import chain
from django.db import models
from django.shortcuts import render
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

# Imports Models
from awards.models import AwardsPage
from harvesting.models import HarvestingPage
from karamoja_response.models import karamojaResponsePage
from landClearing.models import LandClearingPage
from production.models import ProductionPage
from solutions.models import SolutionsPage

# Create your models here.

# class LatestEntriesFeed(Feed):
#     title = "Yeshua Life Latest Posts"
#     link = reverse.lazy("blog:index")
#     description = "Updates on new posts and Articles from Yeshua Life"

#     def items(self):
#         return BlogPage.objects.order_by('-published_date')[:5]
#     def item_title(self,item):
#         return item.title
#     def item_description(self, item):
#         return item.intro
#     def item_link(self,item):
#         return reverse.lazy('blog:detail', args=[item.slug])


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
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.PROTECT, related_name='+',blank=True,null=True
    )
    content_panels = Page.content_panels + [
    FieldPanel('intro'),
    FieldPanel('image'),
    ]
    def get_latest_awards(self):
        latest_awards = AwardsPage.objects.live().order_by('-first_published_at')[:5]
        # latest_karamoja = Karam
        print("Latest awards:", latest_awards) 
        return latest_awards
    
    def get_combined_pages(self):

        #pages initialization
        awards_pages = AwardsPage.objects.live().order_by('-first_published_at')[:2]
        harvesting_page = HarvestingPage.objects.live().order_by('-first_published_at')[:2]
        response_page = karamojaResponsePage.objects.live().order_by('-first_published_at')[:2]
        production_page = ProductionPage.objects.live().order_by('-first_published_at')[:1]
        solution_page = SolutionsPage.objects.live().order_by('-first_published_at')[:1]
        landClearing_page = LandClearingPage.live().order_by('-first_published_at')[:2]


        # combined the querysets
        _combined_pages = sorted(
            chain(awards_pages,landClearing_page,harvesting_page,production_page,solution_page, response_page),
            key=lambda page: page.first_published_at,
            reverse=True
        )

        return _combined_pages

    def serve(self,request):
        context = self.get_context(request=request)
        context['combined_pages'] = self.get_combined_pages()
        return render(request,'blog/blog_index_page.html', context)  

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

class BlogPage(Page):
    date = models.DateField("Post date", null=True)

    # body = StreamField([
    #     # ('video', VideoBlock()),
    #     # ('rich_text', blocks.RichTextBlock())
    #     ('combined', VideoAndRI)
    # ], blank=True)
    

    body_video = StreamField([
        # ('paragraph',  blocks.RichTextBlock(features=['h1','h2', 'h3', 'h4', 'h5', 'bold', 'italic', 'ol','ul' ,'hr', 'link', 'document-link'])),
        # ('code', CodeBlock(label= ('Code'))),
        ('video', InlineVideoBlock()),
        # other blocks here
    ], blank=True,use_json_field=True)

    # video = InlineVideoBlock()
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

def get_latest_awards(self):
    return AwardsPage.objects.live().order_by('-first_published_at')[:5]
