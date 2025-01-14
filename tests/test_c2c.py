import os
import shutil
import tempfile
import unittest
from pathlib import Path

from c2c.c2c import (GitignoreHandler, GitignoreRule, create_delimiter,
                     create_header, find_all_gitignores, is_binary_file,
                     scan_directory)


class TestGitignoreRule(unittest.TestCase):
    def test_basic_pattern_matching(self):
        rule = GitignoreRule("*.txt", ".")
        self.assertTrue(rule.matches("test.txt"))
        self.assertTrue(rule.matches("dir/test.txt"))
        self.assertFalse(rule.matches("test.py"))

    def test_directory_pattern(self):
        rule = GitignoreRule("temp/", ".")
        self.assertTrue(rule.matches("temp", is_dir=True))
        self.assertTrue(rule.matches("dir/temp", is_dir=True))
        self.assertFalse(rule.matches("temp.txt"))
        self.assertFalse(rule.matches("temp", is_dir=False))

    def test_negation_pattern(self):
        rule = GitignoreRule("!important.txt", ".")
        self.assertTrue(rule.matches("important.txt"))
        self.assertFalse(rule.matches("other.txt"))
        self.assertTrue(rule.is_negation)

    def test_base_directory_scoping(self):
        rule = GitignoreRule("*.txt", "src")
        self.assertTrue(rule.matches("src/test.txt"))
        self.assertFalse(rule.matches("test.txt"))
        self.assertTrue(rule.matches("src/subdir/test.txt"))

    def test_root_pattern(self):
        rule = GitignoreRule("/root.txt", ".")
        self.assertTrue(rule.matches("root.txt"))
        self.assertFalse(rule.matches("dir/root.txt"))


class TestGitignoreHandler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.handler = GitignoreHandler(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_basic_ignore(self):
        self.handler.rules.append(GitignoreRule("*.txt", "."))
        self.assertTrue(self.handler.should_ignore("test.txt"))
        self.assertFalse(self.handler.should_ignore("test.py"))

    def test_negation_override(self):
        self.handler.rules.extend([
            GitignoreRule("*.txt", "."),
            GitignoreRule("!important.txt", ".")
        ])
        self.assertTrue(self.handler.should_ignore("test.txt"))
        self.assertFalse(self.handler.should_ignore("important.txt"))

    def test_directory_rules(self):
        self.handler.rules.append(GitignoreRule("temp/", "."))
        self.assertTrue(self.handler.should_ignore("temp", is_dir=True))
        self.assertFalse(self.handler.should_ignore("temp.txt"))

    def test_multiple_gitignores(self):
        # Create test directory structure
        src_dir = os.path.join(self.temp_dir, "src")
        os.makedirs(src_dir)

        # Create root .gitignore
        with open(os.path.join(self.temp_dir, ".gitignore"), "w") as f:
            f.write("*.txt\n")

        # Create src/.gitignore
        with open(os.path.join(src_dir, ".gitignore"), "w") as f:
            f.write("!important.txt\n")

        handler = GitignoreHandler(self.temp_dir)
        for gitignore in find_all_gitignores(self.temp_dir):
            handler.add_rules_from_file(gitignore)

        self.assertTrue(handler.should_ignore("test.txt"))
        self.assertFalse(handler.should_ignore("src/important.txt"))


class TestFileOperations(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_is_binary_file(self):
        # Test text file
        text_path = os.path.join(self.temp_dir, "text.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write("Hello, World!")
        self.assertFalse(is_binary_file(text_path))

        # Test binary file
        binary_path = os.path.join(self.temp_dir, "binary.bin")
        with open(binary_path, "wb") as f:
            f.write(bytes([0, 255, 128]))
        self.assertTrue(is_binary_file(binary_path))

    def test_create_delimiter(self):
        delimiter = create_delimiter()
        self.assertTrue(delimiter.startswith("### FILE_"))
        self.assertEqual(len(delimiter), len("### FILE_xxxxxx "))

    def test_create_header(self):
        delimiter = create_delimiter()
        header = create_header(delimiter)
        self.assertIn(delimiter.strip(), header)
        self.assertIn("Project Directory Contents", header)


class TestDirectoryScanning(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        # Create test directory structure
        self.create_test_structure()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def create_test_structure(self):
        # Create directories
        os.makedirs(os.path.join(self.temp_dir, "src"))
        os.makedirs(os.path.join(self.temp_dir, "docs"))

        # Create text files
        files = {
            "src/main.py": "print('Hello, World!')",
            "src/util.py": "def helper(): pass",
            "docs/readme.txt": "Documentation",
            ".gitignore": "*.txt\n!docs/*.txt"
        }

        for path, content in files.items():
            full_path = os.path.join(self.temp_dir, path)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    def test_scan_directory(self):
        # Redirect stdout to capture output
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            delimiter = create_delimiter()
            scan_directory(self.temp_dir, [".git"], delimiter)

            output = captured_output.getvalue()

            # Verify header
            self.assertIn("Project Directory Contents", output)

            # Verify files are included/excluded correctly
            self.assertIn("src/main.py", output)
            self.assertIn("src/util.py", output)
            self.assertIn("docs/readme.txt", output)
            self.assertIn("print('Hello, World!')", output)

        finally:
            sys.stdout = sys.__stdout__

    def test_find_all_gitignores(self):
        # Create additional .gitignore in src directory
        src_gitignore = os.path.join(self.temp_dir, "src", ".gitignore")
        with open(src_gitignore, "w") as f:
            f.write("*.pyc\n")

        gitignores = find_all_gitignores(self.temp_dir)
        self.assertEqual(len(gitignores), 2)
        self.assertTrue(any(p.endswith("src/.gitignore") for p in gitignores))
        self.assertTrue(any(p.endswith("/.gitignore") for p in gitignores))


if __name__ == "__main__":
    unittest.main()
