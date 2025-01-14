# c2c

A Python package that converts a directory structure into a single text file, preserving file contents and directory hierarchy while respecting `.gitignore` rules. Perfect for sharing codebase context with AI language models or creating project snapshots.

## Features

- **Smart Directory Scanning**: Recursively scans directories and outputs contents as a single well-formatted text file with clear delimiters between files
- **Git-Aware**: 
  - Fully respects `.gitignore` rules at both root and subdirectory levels
  - Handles negative patterns (patterns starting with `!`) correctly
  - Supports multiple `.gitignore` files in subdirectories, just like Git
- **Intelligent File Handling**:
  - Automatically detects and excludes binary files to maintain output integrity
  - Full UTF-8 encoding support with proper error handling
  - Generates unique, collision-free delimiters to clearly separate files
- **Flexible Configuration**:
  - Custom exclude patterns via command line arguments or Python API
  - Debug mode for troubleshooting pattern matching
  - Easy integration with both CLI and Python applications
- **AI-Ready Output**: 
  - Generates output specifically formatted for optimal use with AI language models
  - Supports large language models like Claude, GPT-4, etc.
  - Preserves directory structure and file relationships for better context

## Installation

Install from PyPI:
```bash
pip install c2c
```

Or install from source:
```bash
git clone https://github.com/kawataki-yoshika/c2c.git
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

Exclude specific patterns:
```bash
c2c . -e "*.log" -e "temp/*"
```

Enable debug mode to see pattern matching details:
```bash
c2c . --debug
```

Save output to file:
```bash
c2c . > project_snapshot.txt
```

### Python API

The package provides a flexible Python API for integration into your tools:

```python
from c2c import scan_directory, create_delimiter

# Generate a unique delimiter
delimiter = create_delimiter()

# Basic usage with default excludes
scan_directory(
    directory=".",
    exclude_patterns=[".git"],  # Default exclude pattern
    delimiter=delimiter
)

# With custom exclude patterns
scan_directory(
    directory="/path/to/project",
    exclude_patterns=[
        ".git",  # Default
        "*.log",
        "temp/*"
    ],
    delimiter=delimiter,
    debug=True
)
```

### Using with AI Language Models

1. Generate a snapshot of your project:
```bash
c2c . > context.txt
```

2. Use in your prompts:
```
Here's my project structure and contents:

[paste contents of context.txt]

Could you help me understand the code structure and suggest improvements?
```

The output format is specifically designed to help AI models understand:
- Project structure and hierarchical relationships
- File contents with clear, unambiguous boundaries
- Complete directory hierarchy and organization
- Metadata about excluded files and patterns

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

## Default Excludes

By default, c2c excludes:
- `.git` directories and all Git-related files
- Binary files (automatically detected)
- Files matching any `.gitignore` patterns

You can add additional patterns using the `-e` flag or through the Python API.

## Advanced Features

### GitignoreRule Handling

The GitignoreRule system provides full Git-compatible pattern matching:
- Base directory-specific patterns for scoped ignores
- Negative patterns with `!` for pattern negation
- Path matching with `/` prefix for root-relative patterns
- Directory-only patterns (ending with `/`)
- Pattern normalization and `**/` pattern support

### Binary File Detection

- Smart UTF-8 decoding attempt to detect binary files
- Configurable detection threshold
- Ensures output integrity by excluding non-text content
- Proper handling of various text encodings

### Gitignore Processing

- Multiple `.gitignore` files support with proper precedence rules
- Pattern processing order matches Git behavior
- Scoped rules based on `.gitignore` file location
- Full support for pattern negation and complex rule combinations

## Contributing

We welcome contributions! Here's how you can help:
- Submit pull requests for bug fixes or new features
- Report bugs and suggest improvements
- Improve documentation and examples
- Share use cases and feature ideas

Please feel free to open issues or submit pull requests on GitHub.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.