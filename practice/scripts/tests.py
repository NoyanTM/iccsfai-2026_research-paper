import unittest
import pathlib
import json
import random

from .utils import normalize_version, generate_version, match_version

# @TODO: combine to single function because of duplicate logic
class TestVersionNormalization(unittest.TestCase):
    def setUp(self):
        CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config.json"
        try:
            with open(str(CONFIG_PATH), "r") as file:
                config = json.load(file)
        except OSError:
            raise
        random.seed(config["tests"]["random_seed"])
        self.config = config["tests"]["test_version_normalization"]

    def test_major_specifier(self):
        test_config = self.config["test_major_specifier"]
        versions = [
            generate_version(
                test_config["major_versions"],
            )
            for i in range(test_config["versions"])
        ]
        for index, version in enumerate(versions):
            with self.subTest(index):
                normalized_version = normalize_version(version)
                self.assertEqual(normalized_version, f"{version}.0.0")
                self.assertEqual(len(normalized_version.split(".")), 3)

    def test_major_and_minor_specifier(self):
        test_config = self.config["test_major_and_minor_specifier"]
        versions = [
            generate_version(
                test_config["major_versions"],
                test_config["minor_versions"],
            )
            for i in range(test_config["versions"])
        ]
        for index, version in enumerate(versions):
            with self.subTest(index):
                normalized_version = normalize_version(version)
                self.assertEqual(normalized_version, f"{version}.0")
                self.assertEqual(len(normalized_version.split(".")), 3)
        
    def test_major_minor_patch_specifiers(self):
        test_config = self.config["test_major_minor_patch_specifiers"]
        versions = [
            generate_version(
                test_config["major_versions"],
                test_config["minor_versions"],
                test_config["patch_versions"],
            )
            for i in range(test_config["versions"])
        ]
        for index, version in enumerate(versions):
            with self.subTest(index):
                normalized_version = normalize_version(version)
                self.assertEqual(normalized_version, version)
                self.assertEqual(len(normalized_version.split(".")), 3)


# @TODO: export other test data to parametrized format into config.json
class TestVersionMatching(unittest.TestCase):
    def setUp(self):
        CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config.json"
        try:
            with open(str(CONFIG_PATH), "r") as file:
                config = json.load(file)
        except OSError:
            raise
        random.seed(config["tests"]["random_seed"])
        self.config = config["tests"]["test_version_matching"]
        self.ranges = [tuple(r) for r in self.config["ranges"]]
    
    def test_in_first_range(self):
        versions = [
            "0.0.3", "0.0.4", "0.0.9", "0.1.0", "0.2.2",
            "0.3.5", "0.4.0", "0.5.0", "0.5.1", "0.5.4"
        ]
        expected = ("0.0.3", "0.5.5")
        for v in versions:
            with self.subTest(version=v):
                self.assertEqual(match_version(v, self.ranges), expected)

    def test_in_one_of_ranges(self):
        versions = [
            "3.0.5", "3.0.6", "3.1.0", "3.2.5", "3.5.0",
            "3.8.9", "4.0.0", "4.1.0", "4.1.5", "4.1.9"
        ]
        expected = ("3.0.5", "4.2.0")
        for v in versions:
            with self.subTest(version=v):
                self.assertEqual(match_version(v, self.ranges), expected)

    def test_in_last_range(self):
        versions = [
            "7.0.0", "7.1.1", "7.5.0", "7.9.9", "8.0.0",
            "8.2.3", "8.5.0", "8.8.8", "8.9.0", "8.9.9"
        ]
        expected = ("7.0.0", "9.0.0")
        for v in versions:
            with self.subTest(version=v):
                self.assertEqual(match_version(v, self.ranges), expected)

    def test_below_any_range(self):
        versions = [
            "0.0.0", "0.0.1", "0.0.2", "0.0.0", "0.0.1",
            "0.0.2", "0.0.0", "0.0.1", "0.0.0", "0.0.2"
        ]
        for v in versions:
            with self.subTest(version=v):
                self.assertIsNone(match_version(v, self.ranges))

    def test_upper_any_range(self):
        versions = [
            "9.0.0", "9.0.1", "9.1.0", "9.5.5", "9.9.9",
            "9.0.0", "9.2.2", "9.3.0", "9.8.7", "9.9.0"
        ]
        for v in versions:
            with self.subTest(version=v):
                self.assertIsNone(match_version(v, self.ranges))

if __name__ == "__main__":
    unittest.main()
