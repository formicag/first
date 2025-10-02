"""
Lambda function to email a shopping list to the user.

This function retrieves all items for a user from DynamoDB and sends
a formatted HTML email via Amazon SES.
"""

import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import logging
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses', region_name='eu-west-1')
table = dynamodb.Table('ShoppingList')

# Email configuration
SENDER_EMAIL = 'gianlucaformica@outlook.com'
RECIPIENT_EMAIL = 'gianlucaformica@outlook.com'


def lambda_handler(event, context):
    """
    Email shopping list to user.

    Expected input:
    {
        "userId": "Gianluca" or "Nicole"
    }

    Returns:
        dict: Response with status code and message
    """
    try:
        # Extract userId from path parameters
        path_params = event.get('pathParameters', {})
        user_id = path_params.get('userId')

        if not user_id:
            logger.error("Missing required parameter: userId")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameter: userId'
                })
            }

        logger.info(f"Fetching shopping list for user: {user_id}")

        # Query DynamoDB for user's items
        response = table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )

        items = response.get('Items', [])

        if not items:
            logger.info(f"No items found for user: {user_id}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'No items to email',
                    'itemCount': 0
                })
            }

        # Separate items into bought and unbought
        unbought_items = [item for item in items if not item.get('bought', False)]
        bought_items = [item for item in items if item.get('bought', False)]

        # Sort by added date (most recent first)
        unbought_items.sort(key=lambda x: x.get('addedDate', ''), reverse=True)
        bought_items.sort(key=lambda x: x.get('addedDate', ''), reverse=True)

        # Generate HTML email
        html_body = generate_email_html(user_id, unbought_items, bought_items)

        # Get current date for subject
        current_date = datetime.utcnow().strftime('%B %d, %Y')
        subject = f"Shopping List for {user_id} - {current_date}"

        # Send email via SES
        logger.info(f"Sending email to {RECIPIENT_EMAIL}")

        ses_response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': [RECIPIENT_EMAIL]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )

        logger.info(f"Email sent successfully. MessageId: {ses_response['MessageId']}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Email sent successfully',
                'itemCount': len(items),
                'unboughtCount': len(unbought_items),
                'boughtCount': len(bought_items),
                'messageId': ses_response['MessageId']
            })
        }

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to send email',
                'message': str(e)
            })
        }


def generate_email_html(user_id, unbought_items, bought_items):
    """
    Generate HTML email body for shopping list.

    Args:
        user_id: User name (Gianluca or Nicole)
        unbought_items: List of items not yet bought
        bought_items: List of items already bought

    Returns:
        str: HTML formatted email body
    """
    current_date = datetime.utcnow().strftime('%B %d, %Y')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
            }}
            .content {{
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-top: none;
                border-radius: 0 0 10px 10px;
                padding: 30px;
            }}
            .section {{
                margin-bottom: 30px;
            }}
            .section h2 {{
                color: #667eea;
                font-size: 20px;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #f0f0f0;
            }}
            .item {{
                padding: 15px;
                margin-bottom: 10px;
                background: #f8f9ff;
                border-left: 4px solid #667eea;
                border-radius: 5px;
            }}
            .item-bought {{
                background: #f5f5f5;
                border-left-color: #999;
                opacity: 0.7;
            }}
            .item-name {{
                font-weight: bold;
                font-size: 16px;
                color: #333;
            }}
            .item-bought .item-name {{
                text-decoration: line-through;
                color: #999;
            }}
            .item-details {{
                font-size: 14px;
                color: #666;
                margin-top: 5px;
            }}
            .item-quantity {{
                font-weight: 600;
                color: #667eea;
            }}
            .item-category {{
                background: #667eea;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
                margin-left: 10px;
            }}
            .empty {{
                text-align: center;
                color: #999;
                padding: 20px;
                font-style: italic;
            }}
            .footer {{
                text-align: center;
                color: #999;
                font-size: 12px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛒 Shopping List</h1>
            <p>{user_id}'s List - {current_date}</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>Items to Buy ({len(unbought_items)})</h2>
    """

    if unbought_items:
        for item in unbought_items:
            quantity = int(item.get('quantity', 1)) if isinstance(item.get('quantity'), Decimal) else item.get('quantity', 1)
            category = item.get('category', '')
            category_html = f'<span class="item-category">{category}</span>' if category else ''

            html += f"""
                <div class="item">
                    <div class="item-name">{item.get('itemName', 'Unknown')}</div>
                    <div class="item-details">
                        <span class="item-quantity">Quantity: {quantity}</span>
                        {category_html}
                    </div>
                </div>
            """
    else:
        html += '<div class="empty">No items to buy! 🎉</div>'

    html += f"""
            </div>

            <div class="section">
                <h2>Already Bought ({len(bought_items)})</h2>
    """

    if bought_items:
        for item in bought_items:
            quantity = int(item.get('quantity', 1)) if isinstance(item.get('quantity'), Decimal) else item.get('quantity', 1)
            category = item.get('category', '')
            category_html = f'<span class="item-category">{category}</span>' if category else ''

            html += f"""
                <div class="item item-bought">
                    <div class="item-name">{item.get('itemName', 'Unknown')}</div>
                    <div class="item-details">
                        <span class="item-quantity">Quantity: {quantity}</span>
                        {category_html}
                    </div>
                </div>
            """
    else:
        html += '<div class="empty">No items bought yet</div>'

    html += """
            </div>

            <div class="footer">
                <p>Generated by Shopping List App</p>
                <p>This is an automated email. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html
