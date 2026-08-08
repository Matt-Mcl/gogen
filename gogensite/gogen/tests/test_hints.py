"""The automatic hints that get written into the notes box.

A hint line lists the letters that sit next to a letter in one of the clue
strings, which on the grid means they have to be its neighbours.
"""

from django.contrib.auth.models import User
from django.test import TestCase

from gogen.helpers.views_helper import apply_notes_settings
from gogen.models import *


# CAB gives A the neighbours C and B; DUO gives U the neighbours D and O
WORDS = ["CAB", "DUO"]


def hint_lines(notes):
    """The notes as a {letter: hinted letters} mapping, order ignored."""
    lines = {}
    for line in notes.strip().split("\n"):
        letter, _, hints = line.partition(": ")
        lines[letter.strip()] = set(hints.strip())

    return lines


class HintSettingTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.settings = Settings.objects.create(user=self.user)

    def notes(self, fill_hints, notes="", preset=None):
        self.settings.fill_hints = fill_hints
        self.settings.preset_notes = preset

        return apply_notes_settings(WORDS, notes, self.settings)

    def test_off_writes_nothing(self):
        self.assertEqual(self.notes('N'), "")

    def test_vowels_only_covers_vowels(self):
        lines = hint_lines(self.notes('V'))

        self.assertEqual(lines, {"A": {"C", "B"}, "U": {"D", "O"}, "O": {"U"}})

    def test_all_covers_consonants_too(self):
        lines = hint_lines(self.notes('A'))

        # The consonants next to a vowel now get their own lines
        self.assertEqual(lines["C"], {"A"})
        self.assertEqual(lines["B"], {"A"})
        self.assertEqual(lines["D"], {"U"})
        # and the vowel lines are still there
        self.assertEqual(lines["A"], {"C", "B"})

    def test_all_never_hints_a_letter_against_itself(self):
        for letter, hints in hint_lines(self.notes('A')).items():
            self.assertNotIn(letter, hints)

    def test_only_letters_that_have_a_neighbour_get_a_line(self):
        """Letters absent from the clues have nothing to say."""
        lines = hint_lines(self.notes('A'))

        self.assertNotIn("Z", lines)
        self.assertNotIn("Q", lines)

    def test_an_unknown_setting_is_treated_as_off(self):
        self.assertEqual(self.notes('?'), "")


class HintPresetTestCase(TestCase):
    """Presets are scaffolds like "A: \\nE: ", so hints fill the lines in."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.settings = Settings.objects.create(user=self.user)

    def fill(self, fill_hints, template):
        preset = NoteTemplate.objects.create(name="test", template=template)
        self.settings.fill_hints = fill_hints
        self.settings.preset_notes = preset

        return apply_notes_settings(WORDS, "", self.settings)

    def test_hints_merge_into_the_presets_lines(self):
        notes = self.fill('V', "A: \nU: \n")
        lines = hint_lines(notes)

        self.assertEqual(lines["A"], {"C", "B"})
        self.assertEqual(lines["U"], {"D", "O"})
        # Merged in place rather than appended, so no line is duplicated
        self.assertEqual(notes.count("A: "), 1)

    def test_letters_missing_from_the_preset_are_appended(self):
        lines = hint_lines(self.fill('A', "A: \n"))

        self.assertEqual(lines["A"], {"C", "B"})
        self.assertEqual(lines["C"], {"A"})

    def test_notes_the_user_has_edited_are_left_alone(self):
        preset = NoteTemplate.objects.create(name="test", template="A: \n")
        self.settings.fill_hints = 'A'
        self.settings.preset_notes = preset

        notes = apply_notes_settings(WORDS, "my own working", self.settings)

        self.assertEqual(notes, "my own working")


class SettingsViewHintsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

    def post(self, data):
        self.client.post("/settings/", data)

        return Settings.objects.get(user=self.user).fill_hints

    def test_each_choice_can_be_saved(self):
        for choice, _ in Settings.HINT_CHOICES:
            self.assertEqual(self.post({"notes_enabled": "on", "fill_hints": choice}), choice)

    def test_a_missing_choice_means_off(self):
        """The radios are disabled when the notes box is off, so nothing posts."""
        self.post({"notes_enabled": "on", "fill_hints": "A"})

        self.assertEqual(self.post({"notes_enabled": "on"}), 'N')

    def test_an_invalid_choice_is_rejected(self):
        self.assertEqual(self.post({"notes_enabled": "on", "fill_hints": "Invalid"}), 'N')

    def test_the_settings_page_shows_the_current_choice(self):
        self.post({"notes_enabled": "on", "fill_hints": "A"})

        response = self.client.get("/settings/")

        self.assertContains(response, 'id="fill_hints_A" name="fill_hints" value="A" checked')
        self.assertContains(response, "Automatic hints in notes:")
