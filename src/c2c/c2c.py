#!/usr/bin/env python3
import os
import sys
import fnmatch
import argparse
import uuid
from typing import List, Dict, Set
from dataclasses import dataclass
from pathlib import Path

@dataclass
class GitignoreRule:
    pattern: str
    base_dir: str
    is_negation: bool = False  # 否定パターンかどうか
    
    def __post_init__(self):
        # 初期化時に否定パターンをチェック
        if self.pattern.startswith('!'):
            self.is_negation = True
            self.pattern = self.pattern[1:]
    
    def matches(self, path: str, is_dir: bool = False) -> bool:
        """パスがこのルールにマッチするかチェック"""
        # パスの正規化
        path = path.replace(os.sep, '/')
        if path.startswith('./'):
            path = path[2:]
        
        # 空パターンは無視
        if not self.pattern:
            return False
        
        # サブディレクトリの.gitignoreルールの場合のスコープチェック
        if self.base_dir != '.':
            if not path.startswith(f"{self.base_dir}/") and path != self.base_dir:
                return False
            rel_to_base = path[len(self.base_dir) + 1:] if path != self.base_dir else ''
        else:
            rel_to_base = path

        # パターンマッチングのロジック
        matches = False
        
        # パターンが / で始まる場合
        if self.pattern.startswith('/'):
            pattern = self.pattern.lstrip('/')
            matches = fnmatch.fnmatch(rel_to_base, pattern)
        else:
            # ディレクトリパターンの処理
            if self.pattern.endswith('/'):
                if not is_dir:
                    return False
                pattern = self.pattern.rstrip('/')
            else:
                pattern = self.pattern
            
            # ベースネームでのマッチング
            basename = os.path.basename(path)
            matches = fnmatch.fnmatch(basename, pattern)
            
            # パス全体でのマッチング
            if not matches:
                matches = fnmatch.fnmatch(rel_to_base, pattern) or \
                         fnmatch.fnmatch(rel_to_base, f"**/{pattern}")
        
        # 否定パターンの場合は結果を反転しない
        # 呼び出し側で適切に処理する
        return matches

class GitignoreHandler:
    def __init__(self, root_dir: str, debug: bool = False):
        self.rules: List[GitignoreRule] = []
        self.root_dir = root_dir
        self.debug = debug
    
    def should_ignore(self, path: str, is_dir: bool = False) -> bool:
        """
        パスが無視すべきかどうかを判定
        否定パターンを考慮して判定を行う
        """
        if self.debug:
            print(f"\nChecking path: '{path}' (is_dir={is_dir})", file=sys.stderr)
        
        ignored = False
        
        # ルールを順番に適用
        for rule in self.rules:
            matches = rule.matches(path, is_dir)
            
            if matches:
                if rule.is_negation:
                    # 否定パターンにマッチした場合は、それまでの除外を上書き
                    ignored = False
                    if self.debug:
                        print(f"  Unignored by rule: pattern='!{rule.pattern}', "
                              f"base_dir='{rule.base_dir}'", file=sys.stderr)
                else:
                    # 通常パターンにマッチした場合は除外
                    ignored = True
                    if self.debug:
                        print(f"  Matched rule: pattern='{rule.pattern}', "
                              f"base_dir='{rule.base_dir}'", file=sys.stderr)
        
        return ignored

    def add_rules_from_file(self, gitignore_path: str) -> None:
        """指定された.gitignoreファイルからルールを読み込む"""
        rel_dir = os.path.relpath(os.path.dirname(gitignore_path), self.root_dir)
        base_dir = '.' if rel_dir == '.' else rel_dir.replace(os.sep, '/')
            
        try:
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # **/ パターンを正規化
                        line = line.replace('**/', '')
                        self.rules.append(GitignoreRule(line, base_dir))
                        if self.debug:
                            prefix = '!' if line.startswith('!') else ''
                            pattern = line[1:] if prefix else line
                            print(f"Added rule: pattern='{prefix}{pattern}', "
                                  f"base_dir='{base_dir}'", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Error reading {gitignore_path}: {e}", file=sys.stderr)

def create_delimiter() -> str:
    """一意の区切り文字列を生成
    Returns a unique delimiter in the format: ### FILE_abc123 
    where abc123 is a 6-character random hex string"""
    unique_id = str(uuid.uuid4()).split('-')[0][:6]  # 最初の6文字を使用
    return f"### FILE_{unique_id} "

def create_header(delimiter: str) -> str:
    """説明文とヘッダー情報を生成"""
    return f"""# Project Directory Contents
# Format: Files are separated by a delimiter line starting with "{delimiter.strip()}"
# Each delimiter line is followed by the file path, then the file contents.
# Note: Binary files and patterns matching any .gitignore are excluded.

# DELIMITER={delimiter.strip()}

"""

def is_binary_file(file_path: str) -> bool:
    """ファイルがバイナリかどうかをチェック"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
            return False
    except UnicodeDecodeError:
        return True

def find_all_gitignores(start_dir: str) -> List[str]:
    """指定ディレクトリ以下の全ての.gitignoreファイルを見つける"""
    gitignores = []
    for root, _, files in os.walk(start_dir):
        if '.gitignore' in files:
            gitignores.append(os.path.join(root, '.gitignore'))
    return gitignores

def scan_directory(directory: str, exclude_patterns: List[str], delimiter: str, debug: bool = False) -> None:
    """ディレクトリをスキャンしてテキスト形式で出力"""
    directory = os.path.abspath(directory)
    
    # Gitignoreハンドラーの初期化
    gitignore_handler = GitignoreHandler(directory, debug=debug)
    
    # デフォルトの除外パターンを追加
    for pattern in exclude_patterns:
        gitignore_handler.rules.append(GitignoreRule(pattern, '.'))
    
    # すべての.gitignoreファイルを読み込む
    for gitignore_path in find_all_gitignores(directory):
        gitignore_handler.add_rules_from_file(gitignore_path)
    
    # ヘッダー情報を出力
    print(create_header(delimiter))
    
    # ディレクトリ走査
    for root, dirs, files in os.walk(directory):
        # .gitディレクトリは常に除外
        if '.git' in dirs:
            dirs.remove('.git')
        
        # ディレクトリの相対パスを計算
        rel_root = os.path.relpath(root, directory)
        if rel_root == '.':
            rel_root = ''
        
        # ディレクトリの除外判定
        dirs[:] = [d for d in dirs 
                  if not gitignore_handler.should_ignore(
                      os.path.join(rel_root, d) if rel_root else d,
                      is_dir=True
                  )]
        
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, directory)
            
            # 除外判定
            if gitignore_handler.should_ignore(rel_path):
                continue
            
            # バイナリファイルはスキップ
            if is_binary_file(abs_path):
                continue
            
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                print(f"{delimiter}{rel_path}")
                print(content)
                
            except Exception as e:
                print(f"[error reading file: {str(e)}]")

def main():
    parser = argparse.ArgumentParser(description='Convert directory contents to text format')
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('-e', '--exclude', action='append', default=[],
                      help='Additional exclude pattern (glob format)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug output')
    args = parser.parse_args()
    
    default_excludes = [
        '.git',
    ]
    
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    try:
        delimiter = create_delimiter()
        scan_directory(args.directory, default_excludes + args.exclude, delimiter, debug=args.debug)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()