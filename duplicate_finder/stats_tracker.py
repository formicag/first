import json
import os
from datetime import datetime
from pathlib import Path


class StatsTracker:
    """Track deletion statistics persistently."""

    def __init__(self, stats_file='deletion_stats.json'):
        self.stats_file = stats_file
        self.stats = self.load_stats()

    def load_stats(self):
        """Load stats from file, or create new if doesn't exist."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading stats: {e}")
                return self._default_stats()
        return self._default_stats()

    def _default_stats(self):
        """Return default stats structure."""
        return {
            'total_files_deleted': 0,
            'total_bytes_saved': 0,
            'deletions': [],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }

    def save_stats(self):
        """Save stats to file."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def record_deletion(self, file_path, file_size):
        """Record a file deletion."""
        self.stats['total_files_deleted'] += 1
        self.stats['total_bytes_saved'] += file_size
        self.stats['last_updated'] = datetime.now().isoformat()

        # Add to deletion history
        self.stats['deletions'].append({
            'file_path': file_path,
            'size_bytes': file_size,
            'deleted_at': datetime.now().isoformat()
        })

        # Keep only last 1000 deletions to prevent file from growing too large
        if len(self.stats['deletions']) > 1000:
            self.stats['deletions'] = self.stats['deletions'][-1000:]

        self.save_stats()

    def get_stats(self):
        """Get current stats."""
        return {
            'total_files_deleted': self.stats['total_files_deleted'],
            'total_bytes_saved': self.stats['total_bytes_saved'],
            'total_space_saved_human': self._human_readable_size(self.stats['total_bytes_saved']),
            'created_at': self.stats['created_at'],
            'last_updated': self.stats['last_updated']
        }

    def _human_readable_size(self, size_bytes):
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def reset_stats(self):
        """Reset all stats."""
        self.stats = self._default_stats()
        self.save_stats()


if __name__ == "__main__":
    # Test the tracker
    tracker = StatsTracker()

    print("Current stats:")
    print(json.dumps(tracker.get_stats(), indent=2))

    # Simulate a deletion
    tracker.record_deletion('/test/file.txt', 1024 * 1024)  # 1 MB

    print("\nAfter deletion:")
    print(json.dumps(tracker.get_stats(), indent=2))
