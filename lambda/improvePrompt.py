"""
Lambda function to improve AI prompts based on natural language feedback.

This function uses Amazon Bedrock to understand user feedback and enhance
the custom prompt instructions for item categorization.
"""

import json
import boto3
import logging
import re

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name='eu-west-1')

# Bedrock model configuration
BEDROCK_MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'


def lambda_handler(event, context):
    """
    Improve prompt based on natural language feedback.

    Expected input:
    {
        "currentPrompt": "existing custom instructions",
        "contextItems": [{"term": "Flash", "meaning": "bleach cleaner"}],
        "feedback": "Flash means bleach bathroom cleaner, not camera flash"
    }

    Returns:
        dict: Response with improved prompt and extracted context items
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event

        current_prompt = body.get('currentPrompt', '')
        context_items = body.get('contextItems', [])
        feedback = body.get('feedback', '')

        if not feedback:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Feedback is required'
                })
            }

        logger.info(f"Improving prompt with feedback: {feedback}")

        # Use AI to process feedback
        result = improve_prompt_with_ai(current_prompt, context_items, feedback)

        logger.info(f"Prompt improved successfully")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'improvedPrompt': result['improvedPrompt'],
                'newContextItems': result['newContextItems'],
                'explanation': result['explanation']
            })
        }

    except Exception as e:
        logger.error(f"Error improving prompt: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to improve prompt',
                'message': str(e)
            })
        }


def improve_prompt_with_ai(current_prompt, context_items, feedback):
    """
    Use Amazon Bedrock to improve prompt based on feedback.

    Args:
        current_prompt: Current custom instructions
        context_items: List of {term, meaning} dictionaries
        feedback: Natural language feedback from user

    Returns:
        dict: Dictionary with 'improvedPrompt', 'newContextItems', 'explanation'
    """
    # Build context summary
    context_summary = "\n".join([f"- {item['term']}: {item['meaning']}" for item in context_items]) if context_items else "None yet"

    # Create prompt for Claude
    ai_prompt = f"""You are helping to improve an AI prompt for a UK shopping list application.

CURRENT CUSTOM INSTRUCTIONS:
{current_prompt if current_prompt else "(No custom instructions yet)"}

EXISTING CONTEXT ITEMS (household-specific meanings):
{context_summary}

USER FEEDBACK:
"{feedback}"

YOUR TASK:
1. Analyze the user feedback
2. Extract any new context items (word/brand meanings specific to this household)
3. Improve the custom instructions to incorporate the feedback
4. Keep instructions clear, concise, and focused on UK shopping context

IMPORTANT RULES:
- If feedback mentions a word/brand meaning (like "Flash means bleach cleaner"), extract it as a context item
- Don't duplicate existing context items
- Keep custom instructions under 500 characters
- Focus on UK English, product recognition, and categorization preferences
- Write instructions in imperative form (e.g., "Always use...", "Treat...as...")

Return ONLY valid JSON in this format:
{{
  "improvedPrompt": "Updated custom instructions here (or empty string if no general instructions needed)",
  "newContextItems": [
    {{"term": "Word", "meaning": "what it means to this household"}},
    {{"term": "Brand", "meaning": "specific product type"}}
  ],
  "explanation": "Brief explanation of changes made"
}}

Examples of good context items:
- {{"term": "Flash", "meaning": "bleach bathroom cleaner"}}
- {{"term": "Bounty", "meaning": "kitchen paper towels"}}
- {{"term": "Milk", "meaning": "semi-skimmed milk (default)"}}

Examples of good instructions:
- "Always use UK English spelling and product names"
- "Prioritize putting items in their specific product category rather than generic categories"
- "When brand names are ambiguous, use household context to determine the actual product"
"""

    # Prepare request for Claude
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.3,  # Slightly creative but mostly deterministic
        "messages": [
            {
                "role": "user",
                "content": ai_prompt
            }
        ]
    }

    try:
        # Invoke Bedrock model
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        # Parse response
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text'].strip()

        logger.info(f"AI response: {response_text}")

        # Parse JSON response
        try:
            result = json.loads(response_text)

            # Validate structure
            improved_prompt = result.get('improvedPrompt', '')
            new_context_items = result.get('newContextItems', [])
            explanation = result.get('explanation', 'Prompt updated based on feedback')

            # Validate new context items
            validated_items = []
            for item in new_context_items:
                if isinstance(item, dict) and 'term' in item and 'meaning' in item:
                    # Check not already in existing context
                    term_lower = item['term'].lower()
                    if not any(existing['term'].lower() == term_lower for existing in context_items):
                        validated_items.append({
                            'term': item['term'].strip(),
                            'meaning': item['meaning'].strip()
                        })

            return {
                'improvedPrompt': improved_prompt.strip(),
                'newContextItems': validated_items,
                'explanation': explanation
            }

        except json.JSONDecodeError as je:
            logger.error(f"Invalid JSON from AI: {response_text}")

            # Fallback: try to extract context items manually from feedback
            new_items = extract_context_from_feedback(feedback, context_items)

            return {
                'improvedPrompt': current_prompt,  # Keep existing
                'newContextItems': new_items,
                'explanation': 'Added context items based on your feedback'
            }

    except Exception as e:
        logger.error(f"Error calling Bedrock: {str(e)}")

        # Fallback: try to extract context items manually
        new_items = extract_context_from_feedback(feedback, context_items)

        return {
            'improvedPrompt': current_prompt,  # Keep existing
            'newContextItems': new_items,
            'explanation': 'Context items extracted from feedback'
        }


def extract_context_from_feedback(feedback, existing_context):
    """
    Manual extraction of context items from feedback as fallback.

    Args:
        feedback: User feedback text
        existing_context: List of existing context items

    Returns:
        list: New context items extracted
    """
    new_items = []

    # Pattern: "X means Y" or "X is Y"
    patterns = [
        r'["\']?(\w+)["\']?\s+means?\s+([^,\.]+)',
        r'["\']?(\w+)["\']?\s+is\s+(?:a |an )?([^,\.]+)',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, feedback, re.IGNORECASE)
        for match in matches:
            term = match.group(1).strip()
            meaning = match.group(2).strip()

            # Check not already exists
            term_lower = term.lower()
            if not any(item['term'].lower() == term_lower for item in existing_context):
                new_items.append({
                    'term': term.capitalize(),
                    'meaning': meaning
                })

    return new_items
