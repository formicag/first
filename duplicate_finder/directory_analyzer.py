import os
from pathlib import Path
from typing import Dict, List, Any


class DirectoryAnalyzer:
    """Analyze directory sizes and subdirectories."""

    def __init__(self, directory: str):
        self.directory = Path(directory)

    def get_directory_size(self, path: Path) -> int:
        """Calculate total size of a directory and all its contents."""
        total_size = 0
        try:
            for entry in path.iterdir():
                # Skip symlinks and mount points to avoid cloud storage
                if entry.is_symlink():
                    continue

                if entry.is_file():
                    try:
                        total_size += entry.stat().st_size
                    except (PermissionError, FileNotFoundError):
                        pass
                elif entry.is_dir():
                    # Skip CloudStorage and other mount points
                    if entry.name in ['CloudStorage', 'Mobile Documents']:
                        continue
                    total_size += self.get_directory_size(entry)
        except (PermissionError, FileNotFoundError):
            pass
        return total_size

    def analyze_subdirectories(self, max_depth: int = 1) -> List[Dict[str, Any]]:
        """
        Analyze subdirectories and return their sizes.

        Args:
            max_depth: How many levels deep to analyze (1 = direct children only)
        """
        if not self.directory.exists():
            raise ValueError(f"Directory does not exist: {self.directory}")

        if not self.directory.is_dir():
            raise ValueError(f"Path is not a directory: {self.directory}")

        subdirs = []

        # Analyze direct subdirectories
        try:
            for entry in self.directory.iterdir():
                # Skip symlinks and mount points
                if entry.is_symlink():
                    continue

                if entry.is_dir():
                    # Skip CloudStorage and other cloud mount points
                    if entry.name in ['CloudStorage', 'Mobile Documents']:
                        subdirs.append({
                            'name': entry.name + ' (cloud/skipped)',
                            'path': str(entry.absolute()),
                            'size_bytes': 0,
                            'size_human': '0 B (Cloud Storage)'
                        })
                        continue

                    size_bytes = self.get_directory_size(entry)

                    subdirs.append({
                        'name': entry.name,
                        'path': str(entry.absolute()),
                        'size_bytes': size_bytes,
                        'size_human': self._human_readable_size(size_bytes)
                    })
        except PermissionError:
            raise PermissionError(f"Permission denied accessing: {self.directory}")

        # Sort by size (largest first)
        subdirs.sort(key=lambda x: x['size_bytes'], reverse=True)

        return subdirs

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of directory including total size and subdirectory breakdown."""
        total_size = self.get_directory_size(self.directory)
        subdirs = self.analyze_subdirectories()

        return {
            'directory': str(self.directory.absolute()),
            'total_size_bytes': total_size,
            'total_size_human': self._human_readable_size(total_size),
            'subdirectory_count': len(subdirs),
            'subdirectories': subdirs
        }

    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


if __name__ == "__main__":
    import sys

    directory = sys.argv[1] if len(sys.argv) > 1 else "."

    analyzer = DirectoryAnalyzer(directory)
    summary = analyzer.get_summary()

    print(f"\nDirectory: {summary['directory']}")
    print(f"Total Size: {summary['total_size_human']}")
    print(f"\nSubdirectories ({summary['subdirectory_count']}):")
    print("-" * 80)

    for subdir in summary['subdirectories'][:20]:  # Show top 20
        print(f"{subdir['size_human']:>12} - {subdir['name']}")
