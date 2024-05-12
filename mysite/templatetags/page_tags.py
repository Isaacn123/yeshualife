from django import template
from blog.models import BlogPage
from wagtail.images.models import Image

register = template.Library()

@register.simple_tag
def get_page_posts(page_id,default_image_url=None):
    try:
        page = BlogPage.objects.get(page_ptr_id=page_id)
        image = Image.objects.get(id=page.image_id)
        image_url = image if image else default_image_url
        return {
            'title':page.title,
            'description':page.intro,
            'image_url': 'media/{{image.file}}'

        }
    except BlogPage.DoesNotExist as e:
        return {
            "Error":e
        }