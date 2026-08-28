"""Quick checks for description splitting."""

from django.test import SimpleTestCase

from global_solutions.description_utils import (
    has_richtext_media,
    split_description_for_detail,
    split_description_text,
)


class SplitDescriptionTextTests(SimpleTestCase):
    def test_short_text_stays_in_lead(self):
        lead, rest = split_description_text("one two three", 60)
        self.assertEqual(lead, "one two three")
        self.assertEqual(rest, "")

    def test_splits_after_sixty_words(self):
        words = ["word"] * 65
        text = " ".join(words)
        lead, rest = split_description_text(text, 60)
        self.assertEqual(len(lead.split()), 60)
        self.assertEqual(len(rest.split()), 5)

    def test_exactly_sixty_words_has_no_rest(self):
        text = " ".join(["word"] * 60)
        lead, rest = split_description_text(text, 60)
        self.assertEqual(lead, text)
        self.assertEqual(rest, "")

    def test_strips_html_before_splitting(self):
        text = "<p>" + " ".join(["word"] * 65) + "</p>"
        lead, rest = split_description_text(text, 60)
        self.assertEqual(len(lead.split()), 60)
        self.assertEqual(len(rest.split()), 5)
        self.assertNotIn("<p>", lead)


class SplitDescriptionForDetailTests(SimpleTestCase):
    def test_plain_text_uses_sidebar_and_body_split(self):
        words = ["word"] * 65
        text = " ".join(words)
        lead, rest, is_richtext = split_description_for_detail(text)
        self.assertEqual(len(lead.split()), 60)
        self.assertEqual(len(rest.split()), 5)
        self.assertFalse(is_richtext)

    def test_image_description_renders_full_richtext_in_body(self):
        source = '<p>Intro</p><embed embedtype="image" format="fullwidth" id="1" alt="Field photo">'
        lead, rest, is_richtext = split_description_for_detail(source)
        self.assertEqual(lead, "Intro")
        self.assertEqual(rest, "")
        self.assertTrue(is_richtext)

    def test_has_richtext_media_detects_embeds(self):
        self.assertTrue(has_richtext_media('<embed embedtype="image" id="1">'))
        self.assertFalse(has_richtext_media("Plain farming tips only."))
