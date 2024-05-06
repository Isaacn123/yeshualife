import json
from django import template
from django.utils.html import mark_safe


register = template.Library()

@register.simple_tag
def json_ld_markup():
    json_ld_data = [
    
    {
        "@context": "http://schema.org",
        "@type": "Article",
        "name": "Yeshua's life support",
        "url": "https://yeshualifeug.com/",
        "image": "https://yeshualifeug.com/media/images/KARAMOJAWEBSITEBUNNER.original.png",
        "description": "Karamoja's anguished cries echo through hunger-stricken lands. Climate change, persistent droughts, and crop failures have spawned famine in this precious region. Families find themselves reduced to consuming leaves for survival."
      },
    {
        "@context": "http://schema.org",
        "@type": "Article",
        "name": "Yeshua's One Elevate lives with our initiative, providing essential attire, bedsheets, and mattresses. Join us in fostering comfort and dignity for those in need.",
        "url": "https://yeshualifeug.com/one-elevate-lives-with-our-initiative-providing-essential-attire-bedsheets-and-mattresses-join-us-in-fostering-comfort-and-dignity-for-those-in-need/",
        "image": "https://yeshualifeug.com/media/images/cause_lack_of_Clothings.width-1080.jpg",
        "description": "In response to critical shortages, our comprehensive initiative addresses essential needs—providing clothing, bedsheets, and mattresses."
      },
    {
        "@context": "http://schema.org",
        "@type": "Article",
        "name": "Yeshua's Agriculture systems Turning Karamoja Dry Land Into Food Bucket",
        "url": "https://yeshualifeug.com/agriculture-systems-turning-karamoja-dry-land-into-food-bucket/",
        "image": "https://yeshualifeug.com/media/images/PHOTO-2023-06-15-22-38-29_kXZPy2r.width-1080.jpg",
        "description": "It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout."
      },
      {
        "@context": "http://schema.org",
        "@type": "Article",
        "name": "Empowering Karamoja Through A Technological Revolution in Agriculture for Sustainable …",
        "url": "https://yeshualifeug.com/empowering-karamoja-through-a-technological-revolution-in-agriculture-for-sustainable-farming/",
        "image": "https://yeshualifeug.com/media/original_images/yeshualife-karamoja-farming.jpg",
        "description": "To address hunger in the Karamoja region, it is crucial to upgrade farming methods by implementing advanced mechanized technologies. yeshua life"
      },
      {
        "@context": "http://schema.org",
        "@type": "Article",
        "name": " Yeshua Life Empowering Communities Through Sustainable Food Production and Environmental Protection",
        "url": "https://yeshualifeug.com/empowering-communities-through-sustainable-food-production-and-environmental-protection/",
        "image": "https://yeshualifeug.com/media/original_images/clearing-the-Fields.jpg",
        "description": "Dedicated to uplifting the community, our initiative focuses on creating substantial employment opportunities for the youth, women, and men."
      }
    ]
    return mark_safe(json.dumps(json_ld_data))
