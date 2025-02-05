import os
import shutil
import tempfile
import unittest
from pathlib import Path

from c2c.c2c import (create_delimiter, create_header, is_binary_file,
                     scan_directory)


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
            # 一時ファイルにスキャン結果を書き出す
            with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as temp_file:
                temp_path = temp_file.name
                delimiter = create_delimiter()
                scan_directory(self.temp_dir, [".git"], delimiter, temp_file)

            # 一時ファイルの内容を captured_output に書き出す
            with open(temp_path, 'r', encoding='utf-8') as f:
                captured_output.write(f.read())

            # クリーンアップ
            os.unlink(temp_path)

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


if __name__ == "__main__":
    unittest.main()
