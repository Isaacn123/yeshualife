"""Quick checks for description splitting."""

from django.test import SimpleTestCase

from global_solutions.description_utils import split_description_text


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
