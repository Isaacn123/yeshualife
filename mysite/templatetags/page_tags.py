from django import template
from blog.models import BlogPage

register = template.Library()

@register.simple_tag
def get_page_posts(page_id,default_image_url=None):
    try:
        page = BlogPage.objects.get(id=2)
        image_url = page.image if page.image else default_image_url
        return {
            'title':page.title,
            'description':page.intro,
            'image_url': image_url

        }
    except BlogPage.DoesNotExist:
        return None