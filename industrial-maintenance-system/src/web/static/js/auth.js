/**
 * CMMS Industrial - Authentication & Session Client Library
 * Handles JWT/HMAC token storage, API authorization headers, and route protection.
 */

const AUTH_STORAGE_KEY = 'cmms_auth_session';

const AuthClient = {
  /**
   * Retrieves active session from localStorage.
   */
  getSession() {
    try {
      const raw = localStorage.getItem(AUTH_STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  /**
   * Saves authentication session data.
   */
  setSession(token, user) {
    localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({
        token,
        user,
        timestamp: Date.now(),
      })
    );
  },

  /**
   * Clears session and redirects to login.
   */
  logout() {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    localStorage.removeItem('cmms_active_tech');
    window.location.href = '/login';
  },

  /**
   * Returns current token or empty string.
   */
  getToken() {
    const session = this.getSession();
    return session?.token || '';
  },

  /**
   * Returns current authenticated user object or null.
   */
  getUser() {
    const session = this.getSession();
    return session?.user || null;
  },

  /**
   * Returns true if user is logged in.
   */
  isAuthenticated() {
    return !!this.getToken();
  },

  /**
   * Route Guard: verifies authentication and role.
   * Redirects unauthorized users automatically.
   */
  guardRoute(requiredRole = null) {
    const user = this.getUser();
    if (!user || !this.getToken()) {
      const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.href = `/login?returnUrl=${returnUrl}`;
      return false;
    }

    if (requiredRole && user.role !== requiredRole) {
      if (user.role === 'TECHNICIAN') {
        window.location.href = '/tecnico';
        return false;
      }
    }
    return true;
  },

  /**
   * Authenticated fetch helper that injects Authorization header.
   */
  async fetch(url, options = {}) {
    const token = this.getToken();
    const headers = {
      ...(options.headers || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, { ...options, headers });

    // Handle 401 Unauthorized globally
    if (response.status === 401) {
      this.logout();
      throw new Error('Sesión expirada o no autorizada');
    }

    return response;
  },
};

// Expose globally
window.AuthClient = AuthClient;
