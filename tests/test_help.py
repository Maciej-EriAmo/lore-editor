"""Testy treści pomocy."""

import unittest

from lore import __version__
from lore.help_topics import DEFAULT_TOPIC, get_topic, topic_titles
from lore.i18n import discover_and_load, set_locale


class TestHelpTopics(unittest.TestCase):
    def setUp(self) -> None:
        discover_and_load(force=True)
        set_locale("pl", persist=False)

    def test_has_core_topics(self):
        titles = topic_titles()
        for name in (
            "Przewodnik pisarza",
            "Skróty klawiszowe",
            "Czcionki i wygląd",
            "Wydruk i eksport",
            "Panel Lore",
            "Słownik i pisownia",
            "Kontekst czasowy",
            "Zapytania semantyczne",
            "Historia zmian",
            "Pliki i Lore Pack",
            "Sieć: Karmazyn i Cynober DB",
            "O programie",
        ):
            self.assertIn(name, titles)

    def test_default_topic_exists(self):
        title, body = get_topic(DEFAULT_TOPIC)
        self.assertEqual(title, DEFAULT_TOPIC)
        self.assertGreater(len(body), 100)

    def test_version_in_about(self):
        _, body = get_topic("O programie")
        self.assertIn(__version__, body)

    def test_unknown_topic_falls_back(self):
        title, body = get_topic("nie istnieje")
        self.assertEqual(title, DEFAULT_TOPIC)

    def test_english_help_titles(self):
        set_locale("en", persist=False)
        titles = topic_titles()
        self.assertIn("Writer's guide", titles)
        title, body = get_topic("Writer's guide")
        self.assertEqual(title, "Writer's guide")
        self.assertGreater(len(body), 20)


if __name__ == "__main__":
    unittest.main()