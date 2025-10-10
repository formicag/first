import boto3
import json
from typing import List, Dict, Any, Tuple
from file_scanner import FileScanner


class DuplicateDetector:
    """Uses AWS Bedrock Claude to intelligently detect duplicate files."""

    def __init__(self, region_name: str = 'us-east-1'):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.model_id = 'anthropic.claude-3-5-sonnet-20241022-v2:0'

    def analyze_files_for_duplicates(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze multiple files to detect potential duplicates.
        Uses Claude to identify similar content even with different filenames.
        """
        # Prepare file information for Claude
        file_summaries = []
        for idx, file in enumerate(files):
            summary = {
                'index': idx,
                'name': file['file_name'],
                'path': file['file_path'],
                'size': file['size_human'],
                'hash': file['sha256_hash'][:16] if file['sha256_hash'] else 'N/A',
                'content_preview': file.get('content_preview', '')[:500]
            }
            file_summaries.append(summary)

        prompt = f"""You are analyzing files to detect duplicates. Files may have different names but contain the same or very similar content.

Files to analyze:
{json.dumps(file_summaries, indent=2)}

Please analyze these files and identify:
1. Exact duplicates (same hash or identical content)
2. Near duplicates (very similar content with minor differences)
3. Potential duplicates (same topic/purpose but different content)

For each group of duplicates found, provide:
- The file indices that are duplicates
- Confidence level (high, medium, low)
- Reason for the match
- Whether they should be considered duplicates

Return your response as a JSON array with this structure:
{{
  "duplicate_groups": [
    {{
      "file_indices": [0, 1],
      "confidence": "high",
      "match_type": "exact|near|potential",
      "reason": "explanation of why these are duplicates",
      "recommendation": "keep|review|delete"
    }}
  ],
  "summary": "overall summary of findings"
}}

Only return the JSON, no additional text."""

        # Call Claude via Bedrock
        try:
            response = self._call_claude(prompt)
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            print(f"Error parsing Claude response: {e}")
            print(f"Response was: {response}")
            return {"duplicate_groups": [], "summary": "Error parsing response"}
        except Exception as e:
            print(f"Error calling Claude: {e}")
            return {"duplicate_groups": [], "summary": f"Error: {str(e)}"}

    def compare_two_files(self, file1: Dict[str, Any], file2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two specific files for similarity."""
        prompt = f"""Compare these two files and determine if they are duplicates:

File 1:
- Name: {file1['file_name']}
- Size: {file1['size_human']}
- Hash: {file1['sha256_hash'][:16] if file1['sha256_hash'] else 'N/A'}
- Content preview:
{file1.get('content_preview', '')}

File 2:
- Name: {file2['file_name']}
- Size: {file2['size_human']}
- Hash: {file2['sha256_hash'][:16] if file2['sha256_hash'] else 'N/A'}
- Content preview:
{file2.get('content_preview', '')}

Respond with JSON:
{{
  "are_duplicates": true/false,
  "confidence": "high|medium|low",
  "match_type": "exact|near|different",
  "similarity_score": 0-100,
  "reason": "explanation",
  "recommendation": "keep_both|keep_one|review"
}}"""

        try:
            response = self._call_claude(prompt)
            return json.loads(response)
        except Exception as e:
            print(f"Error comparing files: {e}")
            return {
                "are_duplicates": False,
                "confidence": "low",
                "match_type": "error",
                "similarity_score": 0,
                "reason": f"Error: {str(e)}",
                "recommendation": "review"
            }

    def _call_claude(self, prompt: str) -> str:
        """Make API call to Claude via Bedrock."""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        }

        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        except Exception as e:
            raise Exception(f"Bedrock API error: {str(e)}")

    def format_duplicate_report(self, analysis: Dict[str, Any], files: List[Dict[str, Any]]) -> str:
        """Format the duplicate analysis into a readable report."""
        report = ["=" * 80]
        report.append("DUPLICATE FILE DETECTION REPORT")
        report.append("=" * 80)
        report.append("")

        if not analysis.get('duplicate_groups'):
            report.append("No duplicates found.")
            return "\n".join(report)

        for idx, group in enumerate(analysis['duplicate_groups'], 1):
            report.append(f"Duplicate Group {idx}:")
            report.append(f"  Confidence: {group['confidence']}")
            report.append(f"  Match Type: {group['match_type']}")
            report.append(f"  Recommendation: {group['recommendation']}")
            report.append(f"  Reason: {group['reason']}")
            report.append(f"  Files:")

            for file_idx in group['file_indices']:
                if file_idx < len(files):
                    file = files[file_idx]
                    report.append(f"    - {file['file_path']}")
                    report.append(f"      Size: {file['size_human']}, Modified: {file['modified_time']}")

            report.append("")

        report.append("Summary:")
        report.append(f"  {analysis.get('summary', 'No summary available')}")
        report.append("")
        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Main execution function."""
    import sys

    # Get directory to scan
    directory = sys.argv[1] if len(sys.argv) > 1 else "../Test"

    print(f"Scanning directory: {directory}")
    print("=" * 80)

    # Step 1: Scan files
    scanner = FileScanner(directory)
    files = scanner.scan_directory()

    print(f"\nFound {len(files)} files")

    # Step 2: Check for exact duplicates by hash
    exact_duplicates = scanner.group_by_hash()
    if exact_duplicates:
        print(f"\nExact duplicates found (same hash): {len(exact_duplicates)} groups")

    # Step 3: Use Claude to detect intelligent duplicates
    print("\nAnalyzing files with AWS Bedrock Claude for intelligent duplicate detection...")
    detector = DuplicateDetector(region_name='eu-west-1')  # Use your preferred region

    analysis = detector.analyze_files_for_duplicates(files)

    # Step 4: Generate report
    report = detector.format_duplicate_report(analysis, files)
    print("\n" + report)

    # Step 5: Export results
    output_file = 'duplicate_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'files_scanned': files,
            'exact_duplicates': {h: [f['file_path'] for f in files_list]
                                 for h, files_list in exact_duplicates.items()},
            'ai_analysis': analysis
        }, f, indent=2)

    print(f"\nFull report saved to: {output_file}")


if __name__ == "__main__":
    main()
