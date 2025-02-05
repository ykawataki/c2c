import os
import shutil
import tempfile
import unittest
from pathlib import Path

from c2c.c2c import (create_delimiter, create_text_header, is_binary_file,
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

    def test_create_text_header(self):
        delimiter = create_delimiter()
        header = create_text_header(delimiter)
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
        self.files = {
            "src/main.py": "print('Hello, World!')",
            "src/util.py": "def helper(): pass",
            "docs/readme.txt": "Documentation",
            ".gitignore": "*.txt\n!docs/*.txt"
        }

        for path, content in self.files.items():
            full_path = os.path.join(self.temp_dir, path)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    def test_scan_directory_text_format(self):
        # Redirect stdout to capture output
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            # 一時ファイルにスキャン結果を書き出す
            with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as temp_file:
                temp_path = temp_file.name
                scan_directory(self.temp_dir, [".git"], temp_file)

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

    def test_scan_directory_jsonl_format(self):
        import io
        import json
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as temp_file:
                temp_path = temp_file.name
                scan_directory(
                    self.temp_dir,
                    [".git"],
                    temp_file,
                    format="jsonl"
                )

            with open(temp_path, 'r', encoding='utf-8') as f:
                captured_output.write(f.read())

            os.unlink(temp_path)

            output = captured_output.getvalue()

            # Verify header is present
            self.assertIn("Project Source Code (JSONL Format)", output)
            self.assertIn("Schema:", output)

            # Split output into lines and filter out header comments
            lines = [line for line in output.split(
                '\n') if line and not line.startswith('#') and line.startswith('{') and line.endswith('}')]

            # Parse each line as JSON and verify
            parsed_files = {}
            for line in lines:
                file_data = json.loads(line)
                self.assertIn("path", file_data)
                self.assertIn("content", file_data)
                parsed_files[file_data["path"]] = file_data["content"]

            # Verify all expected files are present with correct content
            for path, expected_content in self.files.items():
                self.assertIn(path, parsed_files)
                self.assertEqual(parsed_files[path], expected_content)

            # Verify JSON structure
            sample_line = json.loads(lines[0])
            self.assertIsInstance(sample_line["path"], str)
            self.assertIsInstance(sample_line["content"], str)

        finally:
            sys.stdout = sys.__stdout__
