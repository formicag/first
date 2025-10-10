from flask import Flask, render_template, request, jsonify
import os
import shutil
from pathlib import Path
from file_scanner import FileScanner
from stats_tracker import StatsTracker
from directory_analyzer import DirectoryAnalyzer

app = Flask(__name__)

# Store scan results
scan_results = {
    'files': [],
    'duplicates': {},
    'ai_analysis': {}
}

# Initialize stats tracker
stats_tracker = StatsTracker()


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/disk-space', methods=['GET'])
def get_disk_space():
    """Get hard drive disk space information."""
    try:
        # Get disk usage for home directory (will show the main disk)
        home_path = os.path.expanduser('~')
        usage = shutil.disk_usage(home_path)

        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        used_percent = (usage.used / usage.total) * 100

        return jsonify({
            'success': True,
            'disk': {
                'total_bytes': usage.total,
                'used_bytes': usage.used,
                'free_bytes': usage.free,
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'used_percent': round(used_percent, 1)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyze-sizes', methods=['POST'])
def analyze_directory_sizes():
    """Analyze directory and subdirectory sizes."""
    data = request.json
    directory = data.get('directory', '~')

    # Expand user path
    directory = os.path.expanduser(directory)

    try:
        analyzer = DirectoryAnalyzer(directory)
        summary = analyzer.get_summary()

        return jsonify({
            'success': True,
            'analysis': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/count', methods=['POST'])
def count_files():
    """Count files in a directory without scanning them."""
    data = request.json
    directory = data.get('directory', '../Test')

    # Expand user path
    directory = os.path.expanduser(directory)

    try:
        directory_path = Path(directory)

        if not directory_path.exists():
            return jsonify({
                'success': False,
                'error': f'Directory does not exist: {directory}'
            }), 404

        if not directory_path.is_dir():
            return jsonify({
                'success': False,
                'error': f'Path is not a directory: {directory}'
            }), 400

        # Count files
        recursive = data.get('recursive', False)
        if recursive:
            file_paths = [f for f in directory_path.rglob('*') if f.is_file()]
        else:
            file_paths = [f for f in directory_path.iterdir() if f.is_file()]

        return jsonify({
            'success': True,
            'file_count': len(file_paths)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scan', methods=['POST'])
def scan_directory():
    """Scan a directory for files."""
    data = request.json
    directory = data.get('directory', '../Test')

    # Expand user path (e.g., ~/Documents -> /Users/username/Documents)
    directory = os.path.expanduser(directory)

    try:
        # Scan directory
        scanner = FileScanner(directory)
        files = scanner.scan_directory(recursive=data.get('recursive', False))

        # Get exact duplicates by hash
        exact_duplicates = scanner.group_by_hash()

        # Store results
        scan_results['files'] = files
        scan_results['exact_duplicates'] = exact_duplicates

        return jsonify({
            'success': True,
            'files_count': len(files),
            'exact_duplicates_count': len(exact_duplicates),
            'files': files,
            'exact_duplicates': {h: [f['file_path'] for f in files_list]
                                 for h, files_list in exact_duplicates.items()}
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/stats', methods=['GET'])
def get_deletion_stats():
    """Get deletion statistics."""
    return jsonify({
        'success': True,
        'stats': stats_tracker.get_stats()
    })


@app.route('/api/delete', methods=['POST'])
def delete_file():
    """Delete a file."""
    data = request.json
    file_path = data.get('file_path')

    if not file_path:
        return jsonify({
            'success': False,
            'error': 'File path required'
        }), 400

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        # Get file size before deleting
        file_size = os.path.getsize(file_path)

        # Delete the file
        os.remove(file_path)

        # Record deletion in stats
        stats_tracker.record_deletion(file_path, file_size)

        # Remove from scan results
        scan_results['files'] = [f for f in scan_results['files'] if f['file_path'] != file_path]

        # Update exact duplicates
        for hash_val, files_list in list(scan_results.get('exact_duplicates', {}).items()):
            updated_list = [f for f in files_list if f['file_path'] != file_path]
            if len(updated_list) < 2:
                # Remove group if less than 2 files remain
                del scan_results['exact_duplicates'][hash_val]
            else:
                scan_results['exact_duplicates'][hash_val] = updated_list

        # Get updated stats
        current_stats = stats_tracker.get_stats()

        return jsonify({
            'success': True,
            'message': f'File deleted: {file_path}',
            'stats': current_stats
        })

    except PermissionError:
        return jsonify({
            'success': False,
            'error': 'Permission denied'
        }), 403
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
