#!/usr/bin/env python3
import argparse
import fnmatch
import logging
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List


def setup_logger(debug: bool = False) -> logging.Logger:
    """ロガーの初期設定を行う"""
    logger = logging.getLogger("c2c")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # 既存のハンドラをクリア
    logger.handlers.clear()

    # 標準出力用のハンドラ（INFO以上）
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)
    stdout_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(stdout_handler)

    # エラー出力用のハンドラ（WARNING以上）
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(stderr_handler)

    # デバッグモード時のデバッグ出力用ハンドラ
    if debug:
        debug_handler = logging.StreamHandler(sys.stderr)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(logging.Formatter('DEBUG: %(message)s'))
        debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
        logger.addHandler(debug_handler)

    return logger


@dataclass
class GitignoreRule:
    pattern: str
    base_dir: str
    is_negation: bool = False

    def __post_init__(self):
        if self.pattern.startswith('!'):
            self.is_negation = True
            self.pattern = self.pattern[1:]

    def matches(self, path: str, is_dir: bool = False) -> bool:
        path = path.replace(os.sep, '/')
        if path.startswith('./'):
            path = path[2:]

        if not self.pattern:
            return False

        if self.base_dir != '.':
            if not path.startswith(f"{self.base_dir}/") and path != self.base_dir:
                return False
            rel_to_base = path[len(self.base_dir) +
                               1:] if path != self.base_dir else ''
        else:
            rel_to_base = path

        matches = False

        if self.pattern.startswith('/'):
            pattern = self.pattern.lstrip('/')
            matches = fnmatch.fnmatch(rel_to_base, pattern)
        else:
            if self.pattern.endswith('/'):
                if not is_dir:
                    return False
                pattern = self.pattern.rstrip('/')
            else:
                pattern = self.pattern

            basename = os.path.basename(path)
            matches = fnmatch.fnmatch(basename, pattern)

            if not matches:
                matches = fnmatch.fnmatch(rel_to_base, pattern) or \
                    fnmatch.fnmatch(rel_to_base, f"**/{pattern}")

        return matches


class GitignoreHandler:
    def __init__(self, root_dir: str, debug: bool = False):
        self.rules: List[GitignoreRule] = []
        self.root_dir = root_dir
        self.logger = logging.getLogger("c2c")

    def should_ignore(self, path: str, is_dir: bool = False) -> bool:
        self.logger.debug(f"Checking path: '{path}' (is_dir={is_dir})")

        ignored = False

        for rule in self.rules:
            matches = rule.matches(path, is_dir)

            if matches:
                if rule.is_negation:
                    ignored = False
                    self.logger.debug(
                        f"Unignored by rule: pattern='!{rule.pattern}', "
                        f"base_dir='{rule.base_dir}'"
                    )
                else:
                    ignored = True
                    self.logger.debug(
                        f"Matched rule: pattern='{rule.pattern}', "
                        f"base_dir='{rule.base_dir}'"
                    )

        return ignored

    def add_rules_from_file(self, gitignore_path: str) -> None:
        rel_dir = os.path.relpath(
            os.path.dirname(gitignore_path), self.root_dir)
        base_dir = '.' if rel_dir == '.' else rel_dir.replace(os.sep, '/')

        try:
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        line = line.replace('**/', '')
                        self.rules.append(GitignoreRule(line, base_dir))

                        prefix = '!' if line.startswith('!') else ''
                        pattern = line[1:] if prefix else line
                        self.logger.debug(
                            f"Added rule: pattern='{prefix}{pattern}', "
                            f"base_dir='{base_dir}'"
                        )
        except Exception as e:
            self.logger.warning(f"Error reading {gitignore_path}: {e}")


def create_delimiter() -> str:
    unique_id = str(uuid.uuid4()).split('-')[0][:6]
    return f"### FILE_{unique_id} "


def create_header(delimiter: str) -> str:
    return f"""# Project Directory Contents
# Format: Files are separated by a delimiter line starting with "{delimiter.strip()}"
# Each delimiter line is followed by the file path, then the file contents.
# Note: Binary files and patterns matching any .gitignore are excluded.

# DELIMITER={delimiter.strip()}

"""


def is_binary_file(file_path: str) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
            return False
    except UnicodeDecodeError:
        return True


def find_all_gitignores(start_dir: str) -> List[str]:
    return [
        os.path.join(root, '.gitignore')
        for root, _, files in os.walk(start_dir)
        if '.gitignore' in files
    ]


def scan_directory(directory: str, exclude_patterns: List[str], delimiter: str, debug: bool = False) -> None:
    logger = logging.getLogger("c2c")
    directory = os.path.abspath(directory)

    gitignore_handler = GitignoreHandler(directory)

    for pattern in exclude_patterns:
        gitignore_handler.rules.append(GitignoreRule(pattern, '.'))

    for gitignore_path in find_all_gitignores(directory):
        gitignore_handler.add_rules_from_file(gitignore_path)

    print(create_header(delimiter))

    for root, dirs, files in os.walk(directory):
        if '.git' in dirs:
            dirs.remove('.git')

        rel_root = os.path.relpath(root, directory)
        if rel_root == '.':
            rel_root = ''

        dirs[:] = [d for d in dirs
                   if not gitignore_handler.should_ignore(
                       os.path.join(rel_root, d) if rel_root else d,
                       is_dir=True
                   )]

        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, directory)

            if gitignore_handler.should_ignore(rel_path):
                continue

            if is_binary_file(abs_path):
                logger.debug(f"Skipping binary file: {rel_path}")
                continue

            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                print(f"{delimiter}{rel_path}")
                print(content)

            except Exception as e:
                logger.error(f"Error reading file {rel_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert directory contents to text format')
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('-e', '--exclude', action='append', default=[],
                        help='Additional exclude pattern (glob format)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug output')
    args = parser.parse_args()

    default_excludes = ['.git']

    if not os.path.isdir(args.directory):
        logger = logging.getLogger("c2c")
        logger.error(f"'{args.directory}' is not a directory")
        sys.exit(1)

    try:
        setup_logger(args.debug)
        delimiter = create_delimiter()
        scan_directory(args.directory, default_excludes +
                       args.exclude, delimiter, debug=args.debug)
    except Exception as e:
        logger = logging.getLogger("c2c")
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
