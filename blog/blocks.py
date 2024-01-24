from django.utils.translation import gettext_lazy as _
from wagtail  import blocks
from wagtail.blocks import CharBlock
from wagtail.embeds.blocks import EmbedBlock



class InlineVideoBlock(blocks.StructBlock):
    video = EmbedBlock(label=_("Video"))
    caption = CharBlock(required=False, label=_("Caption"))
    float = blocks.ChoiceBlock(
        required=False,
        choices=[('right', _("Right")), ('left', _("Left")), ('center', _("Center"))],
        default='right',
        label=_("Float"),
    )
    size = blocks.ChoiceBlock(
        required=False,
        choices=[('small', _("Small")), ('medium', _("Medium")), ('large', _("Large"))],
        default='small',
        label=_("Size"),
    )

    class Meta:
        icon = 'media'