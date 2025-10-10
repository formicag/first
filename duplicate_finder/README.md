# Duplicate File Finder

AI-powered duplicate file detection using AWS Bedrock Claude. This application scans directories for files and uses intelligent analysis to detect duplicates even when filenames differ.

## Features

- **File Scanning**: Extract comprehensive metadata (size, hash, timestamps, content)
- **Exact Duplicate Detection**: Find identical files using SHA-256 hash comparison
- **AI-Powered Analysis**: Use AWS Bedrock Claude to detect similar content with different names
- **Web Interface**: Beautiful, responsive UI to view and manage duplicates
- **Batch Processing**: Analyze entire directories recursively

## Prerequisites

- Python 3.8+
- AWS Account with Bedrock access
- AWS credentials configured (via AWS CLI or environment variables)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials:
```bash
aws configure
```

## Usage

### Command Line

Run the scanner directly:
```bash
cd duplicate_finder
python duplicate_detector.py ../Test
```

### Web Interface

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser to: `http://localhost:5000`

3. Enter a directory path and click "Scan Directory"

4. Click "Analyze with AI" for intelligent duplicate detection

## How It Works

1. **File Scanning**: Scans directory and extracts metadata:
   - File path, name, extension
   - Size (bytes and human-readable)
   - SHA-256 hash
   - Created/modified timestamps
   - Content preview (for text files)

2. **Exact Matching**: Groups files with identical SHA-256 hashes

3. **AI Analysis**: Sends file metadata to AWS Bedrock Claude to detect:
   - Near duplicates (similar content)
   - Potential duplicates (same topic/purpose)
   - Confidence levels (high, medium, low)
   - Recommendations for handling duplicates

## Project Structure

```
duplicate_finder/
├── file_scanner.py       # File scanning and metadata extraction
├── duplicate_detector.py # AWS Bedrock integration for AI analysis
├── app.py               # Flask web application
├── templates/
│   └── index.html       # Web UI
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## AWS Configuration

The app uses AWS Bedrock with Claude 3.5 Sonnet. Ensure:
- Your AWS credentials have Bedrock permissions
- Claude 3.5 Sonnet model access is enabled in your region
- Default region is `eu-west-1` (can be changed in the UI)

## Example Output

```
Scanning directory: ../Test
================================================================================

Found 3 files

Exact duplicates found (same hash): 1 groups

================================================================================
DUPLICATE FILE DETECTION REPORT
================================================================================

Duplicate Group 1:
  Confidence: high
  Match Type: exact
  Recommendation: keep_one
  Reason: These files have identical content (same SHA-256 hash)
  Files:
    - /path/to/document1.txt
      Size: 150 B, Modified: 2025-10-03T12:00:00
    - /path/to/report.txt
      Size: 150 B, Modified: 2025-10-03T12:01:00

================================================================================
```

## API Endpoints

- `POST /api/scan` - Scan a directory
- `POST /api/analyze` - Analyze files with AI
- `GET /api/results` - Get current results
- `POST /api/compare` - Compare two specific files

## License

MIT
