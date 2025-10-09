// ============================================================================
// COGNITO AUTHENTICATION - TEMPORARILY DISABLED
// ============================================================================
// Uncomment the code below to re-enable Cognito authentication

/*
// Cognito Configuration
const COGNITO_CONFIG = {
    userPoolId: 'eu-west-1_IennWZZNL',
    clientId: '421d0dp1uum2guc3g7i5hkdlo4',
    region: 'eu-west-1'
};

// Cognito endpoint
const COGNITO_ENDPOINT = `https://cognito-idp.${COGNITO_CONFIG.region}.amazonaws.com/`;

async function authenticateUser(email, password) {
    const params = {
        AuthFlow: 'USER_PASSWORD_AUTH',
        ClientId: COGNITO_CONFIG.clientId,
        AuthParameters: {
            USERNAME: email,
            PASSWORD: password
        }
    };

    try {
        const response = await fetch(COGNITO_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-amz-json-1.1',
                'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
            },
            body: JSON.stringify(params)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || data.__type || 'Authentication failed');
        }

        return data.AuthenticationResult;
    } catch (error) {
        console.error('Authentication error:', error);
        throw error;
    }
}

function storeTokens(authResult) {
    sessionStorage.setItem('idToken', authResult.IdToken);
    sessionStorage.setItem('accessToken', authResult.AccessToken);
    sessionStorage.setItem('refreshToken', authResult.RefreshToken);

    // Decode ID token to get user info
    const payload = JSON.parse(atob(authResult.IdToken.split('.')[1]));
    sessionStorage.setItem('userId', payload['custom:displayName'] || payload.email.split('@')[0]);
    sessionStorage.setItem('userEmail', payload.email);
}
*/

// ============================================================================
// BYPASS MODE - FOR DEVELOPMENT/TESTING WITHOUT COGNITO
// ============================================================================

/**
 * Mock authentication - bypasses Cognito
 */
async function authenticateUser(email, password) {
    // Simple mock authentication - accepts any credentials
    return {
        IdToken: 'mock-id-token',
        AccessToken: 'mock-access-token',
        RefreshToken: 'mock-refresh-token'
    };
}

/**
 * Store mock tokens - bypasses Cognito
 */
function storeTokens(authResult) {
    sessionStorage.setItem('idToken', 'mock-id-token');
    sessionStorage.setItem('accessToken', 'mock-access-token');
    sessionStorage.setItem('refreshToken', 'mock-refresh-token');

    // Use a default test user
    sessionStorage.setItem('userId', 'TestUser');
    sessionStorage.setItem('userEmail', 'test@example.com');
}

/**
 * Get stored ID token
 */
function getIdToken() {
    return sessionStorage.getItem('idToken');
}

/**
 * Get user ID from session
 */
function getUserId() {
    return sessionStorage.getItem('userId') || 'TestUser';
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    // BYPASS MODE: Always return true (no authentication required)
    // Store default user if not already set
    if (!sessionStorage.getItem('userId')) {
        sessionStorage.setItem('userId', 'TestUser');
        sessionStorage.setItem('userEmail', 'test@example.com');
        sessionStorage.setItem('idToken', 'mock-id-token');
    }
    return true;

    /* COGNITO MODE (commented out):
    const token = getIdToken();
    if (!token) return false;

    // Check token expiration
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expirationTime = payload.exp * 1000; // Convert to milliseconds
        return Date.now() < expirationTime;
    } catch (error) {
        return false;
    }
    */
}

/**
 * Logout user
 */
function logout() {
    sessionStorage.clear();
    window.location.href = 'login.html';
}

/*
// COGNITO REFRESH TOKEN - COMMENTED OUT
async function refreshAuthToken() {
    const refreshToken = sessionStorage.getItem('refreshToken');
    if (!refreshToken) {
        logout();
        return null;
    }

    const params = {
        AuthFlow: 'REFRESH_TOKEN_AUTH',
        ClientId: COGNITO_CONFIG.clientId,
        AuthParameters: {
            REFRESH_TOKEN: refreshToken
        }
    };

    try {
        const response = await fetch(COGNITO_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-amz-json-1.1',
                'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
            },
            body: JSON.stringify(params)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error('Token refresh failed');
        }

        // Update tokens
        sessionStorage.setItem('idToken', data.AuthenticationResult.IdToken);
        sessionStorage.setItem('accessToken', data.AuthenticationResult.AccessToken);

        return data.AuthenticationResult.IdToken;
    } catch (error) {
        console.error('Token refresh error:', error);
        logout();
        return null;
    }
}
*/

/**
 * Mock refresh token - bypasses Cognito
 */
async function refreshAuthToken() {
    // In bypass mode, just return the mock token
    return 'mock-id-token';
}

// Login form handler (only run on login.html)
if (document.getElementById('login-form')) {
    document.getElementById('login-form').addEventListener('submit', async (event) => {
        event.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const loginBtn = document.getElementById('login-btn');
        const errorContainer = document.getElementById('error-container');

        // Clear previous errors
        errorContainer.innerHTML = '';

        // Disable button
        loginBtn.disabled = true;
        loginBtn.textContent = 'Signing in...';

        try {
            const authResult = await authenticateUser(email, password);
            storeTokens(authResult);

            // Redirect to main app
            window.location.href = 'index.html';
        } catch (error) {
            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = `Login failed: ${error.message}`;
            errorContainer.appendChild(errorDiv);

            // Re-enable button
            loginBtn.disabled = false;
            loginBtn.textContent = 'Sign In';
        }
    });
}
