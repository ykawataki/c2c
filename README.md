# c2c

A Python package that converts a directory structure into a single text file, preserving file contents and directory hierarchy while respecting `.gitignore` rules. Perfect for sharing codebase context with AI language models or creating project snapshots.

## Features

- **Smart Directory Scanning**: 
  - Recursively scans directories and outputs contents as a single well-formatted text file
  - Clear delimiters between files for unambiguous parsing
  - Memory-efficient streaming output for large codebases

- **Git-Aware File Filtering**: 
  - Built on top of the high-performance gitignore-filter library
  - Fully respects `.gitignore` rules at both root and subdirectory levels
  - Supports advanced patterns including negation and directory-specific rules

- **Intelligent File Handling**:
  - Automatic binary file detection and exclusion
  - UTF-8 encoding support with robust error handling
  - Unique, collision-free delimiters for file separation
  - Efficient streaming I/O for large files

- **Flexible Configuration**:
  - Custom exclude patterns using gitignore syntax
  - Debug mode for troubleshooting pattern matches
  - Simple CLI and Python API integration

- **AI-Ready Output**: 
  - Generates output optimized for AI language models
  - Preserves directory structure and file relationships
  - Clear metadata and file boundaries

## Installation

Install from PyPI:
```bash
pip install c2c
```

Or install from source:
```bash
git clone https://github.com/ykawataki/c2c.git
cd c2c
pip install .
```

## Usage

### Command Line Interface

Basic usage - scan current directory:
```bash
c2c .
```

Scan specific directory:
```bash
c2c /path/to/directory
```

Exclude specific patterns using gitignore format:
```bash
# Exclude all log files
c2c . -e "*.log"

# Exclude temp directory
c2c . -e "temp/"

# Complex patterns
c2c . -e "*.log" -e "!important.log" -e "debug/**/*.tmp"
```

Supported pattern formats:
- Simple patterns: `*.log`, `*.tmp`
- Directory patterns: `temp/`, `build/`
- Negative patterns: `!important.log`
- Path-specific patterns: `src/*.log`
- Nested patterns: `**/*.log`

Enable debug mode to see pattern matching details:
```bash
c2c . --debug
```

Save output to file:
```bash
c2c . > project_snapshot.txt
```

### Python API

The package provides a simple Python API for integration into your tools:

```python
from c2c import scan_directory, create_delimiter

# Generate a unique delimiter
delimiter = create_delimiter()

# Basic usage
with open('output.txt', 'w', encoding='utf-8') as output_file:
    scan_directory(
        directory=".",
        exclude_patterns=[".git"],  # Default exclude pattern
        delimiter=delimiter,
        output_file=output_file
    )

# With custom patterns
with open('output.txt', 'w', encoding='utf-8') as output_file:
    scan_directory(
        directory="/path/to/project",
        exclude_patterns=[
            ".git",
            "*.log",
            "temp/*",
            "!important.log"
        ],
        delimiter=delimiter,
        output_file=output_file,
        debug=True
    )
```

### Using with AI Language Models

1. Generate a project snapshot:
```bash
c2c . > context.txt
```

2. Use in your prompts:
```
Here's my project structure and contents:

[paste contents of context.txt]

Could you help me understand the code structure and suggest improvements?
```

The output format is designed for optimal use with AI models:
- Clear file boundaries with unique delimiters
- Preserved directory structure and relationships
- Metadata about excluded files and patterns
- UTF-8 encoded text content only

## Output Format

The generated output follows this structure:

```
# Project Directory Contents
# Format: Files are separated by a delimiter line starting with "### FILE_[uuid]"
# Each delimiter line is followed by the file path, then the file contents.
# Note: Binary files and patterns matching any .gitignore are excluded.

# DELIMITER=### FILE_[uuid]

### FILE_[uuid] src/main.py
[contents of main.py]

### FILE_[uuid] src/utils/helper.py
[contents of helper.py]
```

## Default Behavior

By default, c2c:
- Excludes `.git` directories and Git-related files
- Excludes binary files (automatically detected)
- Respects all `.gitignore` patterns
- Uses UTF-8 encoding for file reading/writing
- Streams output for memory efficiency

## Implementation Details

### Pattern Matching

Built on the gitignore-filter library, c2c supports:
- Full gitignore pattern syntax
- Multiple `.gitignore` files with proper precedence
- Pattern negation with `!`
- Directory-specific patterns
- Path-based pattern scoping

### File Processing

- Binary detection through UTF-8 decoding attempt
- Streaming file I/O for memory efficiency
- Proper resource cleanup
- Robust error handling

### Performance Optimization

- Memory-efficient file processing
- Streaming output generation
- Minimal memory footprint
- High-performance pattern matching through gitignore-filter

## Contributing

Contributions are welcome! Here's how you can help:
- Submit bug reports and feature requests
- Improve documentation and examples
- Share use cases and ideas
- Submit pull requests

Please feel free to open issues or submit pull requests on GitHub.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.