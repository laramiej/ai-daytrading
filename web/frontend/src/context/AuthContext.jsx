import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('auth_token'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Verify token on mount and when token changes
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await axios.get(`${API_BASE_URL}/api/auth/verify`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(response.data.username);
        setError(null);
      } catch (err) {
        console.error('Token verification failed:', err);
        // Token is invalid or expired
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    verifyToken();
  }, [token]);

  const login = useCallback(async (username, password) => {
    setError(null);
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        username,
        password
      });

      const { access_token } = response.data;
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);
      setUser(username);
      return true;
    } catch (err) {
      console.error('Login failed:', err);
      const message = err.response?.data?.detail || 'Login failed. Please try again.';
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      if (token) {
        await axios.post(`${API_BASE_URL}/api/auth/logout`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
    }
  }, [token]);

  const value = {
    user,
    token,
    loading,
    error,
    isAuthenticated: !!user && !!token,
    login,
    logout,
    clearError: () => setError(null)
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
