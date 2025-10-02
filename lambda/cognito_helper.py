"""
Helper function to extract userId from Cognito JWT token claims.
"""

def get_user_id_from_claims(event):
    """
    Extract userId from Cognito authorizer claims.

    Priority:
    1. custom:displayName attribute
    2. First part of email address

    Args:
        event: Lambda event object from API Gateway

    Returns:
        str: User ID or None if not found
    """
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})

    # Try custom displayName first
    user_id = claims.get('custom:displayName')

    # Fallback to email username
    if not user_id:
        email = claims.get('email', '')
        if email:
            user_id = email.split('@')[0]

    return user_id
