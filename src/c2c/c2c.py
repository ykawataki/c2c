#!/usr/bin/env python3
import argparse
import logging
import os
import sys
import tempfile
import uuid
from typing import List, TextIO

from gitignore_filter import git_ignore_filter


def setup_logger(debug: bool = False) -> logging.Logger:
    """Set up the logger configuration"""
    logger = logging.getLogger("c2c")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Standard output handler (INFO and below)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)
    stdout_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(stdout_handler)

    # Error output handler (WARNING and above)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(stderr_handler)

    # Debug handler if debug mode is enabled
    if debug:
        debug_handler = logging.StreamHandler(sys.stderr)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(logging.Formatter('DEBUG: %(message)s'))
        debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
        logger.addHandler(debug_handler)

    return logger


def create_delimiter() -> str:
    """Create a unique delimiter for separating files in output"""
    unique_id = str(uuid.uuid4()).split('-')[0][:6]
    return f"### FILE_{unique_id} "


def create_header(delimiter: str) -> str:
    """Create the header text for the output file"""
    return f"""# Project Directory Contents
# Format: Files are separated by a delimiter line starting with "{delimiter.strip()}"
# Each delimiter line is followed by the file path, then the file contents.
# Note: Binary files and patterns matching any .gitignore are excluded.

# DELIMITER={delimiter.strip()}

"""


def is_binary_file(file_path: str) -> bool:
    """Check if a file is binary by attempting to read it as UTF-8"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
            return False
    except UnicodeDecodeError:
        return True


def scan_directory(directory: str, exclude_patterns: List[str], delimiter: str,
                   output_file: TextIO, debug: bool = False) -> None:
    """Scan directory and write contents to output file, respecting gitignore rules"""
    logger = logging.getLogger("c2c")
    directory = os.path.abspath(directory)

    # Get filtered files using gitignore-filter
    files = git_ignore_filter(
        directory,
        custom_patterns=exclude_patterns,
        log_level='DEBUG' if debug else 'WARNING'
    )

    # Write header
    print(create_header(delimiter), file=output_file)

    # Process each file
    for rel_path in files:
        abs_path = os.path.join(directory, rel_path)

        # Skip binary files
        if is_binary_file(abs_path):
            logger.debug(f"Skipping binary file: {rel_path}")
            continue

        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"{delimiter}{rel_path}", file=output_file)
            print(content, file=output_file)

        except Exception as e:
            logger.error(f"Error reading file {rel_path}: {e}")


def main():
    """Main entry point for the command line interface"""
    parser = argparse.ArgumentParser(
        description='Convert directory contents to text format'
    )
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument(
        '-e', '--exclude',
        action='append',
        default=[],
        help='''Additional exclude pattern (gitignore format). Examples:
            - "*.log" excludes all .log files
            - "temp/" excludes temp directories
            - "!important.txt" negates previous patterns
            - "debug/**/*.log" excludes log files in debug directory and subdirectories'''
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        logger = logging.getLogger("c2c")
        logger.error(f"'{args.directory}' is not a directory")
        sys.exit(1)

    try:
        setup_logger(args.debug)
        delimiter = create_delimiter()

        # Create temporary file for output
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as temp_file:
            temp_path = temp_file.name
            scan_directory(
                args.directory,
                args.exclude,
                delimiter,
                temp_file,
                debug=args.debug
            )

        # Read and output temporary file contents in chunks
        with open(temp_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(8192)  # Read 8KB at a time
                if not chunk:
                    break
                sys.stdout.write(chunk)

        # Clean up temporary file
        os.unlink(temp_path)

    except Exception as e:
        logger = logging.getLogger("c2c")
        logger.error(f"Unexpected error: {e}")
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
