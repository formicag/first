import os
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class FileScanner:
    """Scans directories and extracts file metadata for duplicate detection."""

    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.files_info: List[Dict[str, Any]] = []

    def compute_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """Compute hash of file contents."""
        hash_func = hashlib.new(algorithm)
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            print(f"Error hashing {file_path}: {e}")
            return None

    def get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract comprehensive metadata from a file."""
        try:
            stat = file_path.stat()

            # Read file content for text files
            content = ""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(10000)  # Read first 10KB for analysis
            except (UnicodeDecodeError, PermissionError):
                content = "[Binary or unreadable file]"

            metadata = {
                'file_path': str(file_path.absolute()),
                'file_name': file_path.name,
                'file_extension': file_path.suffix,
                'size_bytes': stat.st_size,
                'size_human': self._human_readable_size(stat.st_size),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'sha256_hash': self.compute_file_hash(file_path),
                'content_preview': content[:500] if content else "",
                'full_content': content
            }
            return metadata
        except Exception as e:
            print(f"Error getting metadata for {file_path}: {e}")
            return None

    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def scan_directory(self, recursive: bool = False) -> List[Dict[str, Any]]:
        """Scan directory and collect file metadata."""
        self.files_info = []

        if not self.directory.exists():
            raise ValueError(f"Directory does not exist: {self.directory}")

        if not self.directory.is_dir():
            raise ValueError(f"Path is not a directory: {self.directory}")

        # Get all files
        if recursive:
            file_paths = [f for f in self.directory.rglob('*') if f.is_file()]
        else:
            file_paths = [f for f in self.directory.iterdir() if f.is_file()]

        print(f"Found {len(file_paths)} files in {self.directory}")

        for file_path in file_paths:
            metadata = self.get_file_metadata(file_path)
            if metadata:
                self.files_info.append(metadata)

        return self.files_info

    def group_by_hash(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group files by their hash value (exact duplicates)."""
        hash_groups = {}
        for file_info in self.files_info:
            file_hash = file_info.get('sha256_hash')
            if file_hash:
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                hash_groups[file_hash].append(file_info)

        # Only return groups with more than one file (actual duplicates)
        return {h: files for h, files in hash_groups.items() if len(files) > 1}

    def export_metadata(self, output_file: str = None) -> str:
        """Export file metadata to JSON."""
        if output_file is None:
            output_file = 'file_metadata.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.files_info, f, indent=2)

        return output_file


if __name__ == "__main__":
    # Example usage
    scanner = FileScanner("../Test")
    files = scanner.scan_directory()

    print(f"\nScanned {len(files)} files:")
    for file in files:
        print(f"  - {file['file_name']} ({file['size_human']}) - Hash: {file['sha256_hash'][:16]}...")

    # Check for exact duplicates by hash
    duplicates = scanner.group_by_hash()
    if duplicates:
        print(f"\nFound {len(duplicates)} groups of exact duplicates:")
        for hash_val, files in duplicates.items():
            print(f"\n  Hash: {hash_val[:16]}...")
            for file in files:
                print(f"    - {file['file_path']}")
    else:
        print("\nNo exact duplicates found by hash.")

    # Export metadata
    output = scanner.export_metadata('file_metadata.json')
    print(f"\nMetadata exported to: {output}")
