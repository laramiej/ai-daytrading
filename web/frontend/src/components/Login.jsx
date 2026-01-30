import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { LockClosedIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, error, clearError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) return;

    setIsSubmitting(true);
    await login(username, password);
    setIsSubmitting(false);
  };

  const handleInputChange = (setter) => (e) => {
    clearError();
    setter(e.target.value);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
            <LockClosedIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-white">
            AI Day Trading
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Sign in to access your trading dashboard
          </p>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="bg-slate-800 rounded-lg p-6 space-y-4 border border-slate-700">
            {/* Error Message */}
            {error && (
              <div className="bg-red-900/50 border border-red-500 rounded-md p-3 flex items-center gap-2">
                <ExclamationCircleIcon className="h-5 w-5 text-red-500 flex-shrink-0" />
                <span className="text-sm text-red-200">{error}</span>
              </div>
            )}

            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-slate-300">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={handleInputChange(setUsername)}
                className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your username"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={handleInputChange(setPassword)}
                className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your password"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || !username || !password}
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </div>
        </form>

        {/* Footer */}
        <p className="text-center text-xs text-slate-500">
          Secure authentication required for trading operations
        </p>
      </div>
    </div>
  );
}

export default Login;
