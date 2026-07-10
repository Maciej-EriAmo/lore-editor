"""Testy treści pomocy."""

import unittest

from lore import __version__
from lore.help_topics import DEFAULT_TOPIC, get_topic, topic_titles


class TestHelpTopics(unittest.TestCase):
    def test_has_core_topics(self):
        titles = topic_titles()
        for name in (
            "Przewodnik pisarza",
            "Skróty klawiszowe",
            "Czcionki i wygląd",
            "Wydruk i eksport",
            "Panel Lore",
            "Pliki i Lore Pack",
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


if __name__ == "__main__":
    unittest.main()