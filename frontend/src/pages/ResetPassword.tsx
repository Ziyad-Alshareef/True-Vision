import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import api from "../api";
import whiteLogo from "./assets/whitefont-transpa.png";
import darkLogo from "./assets/output-onlinepngtoolsblack font transpa.png";
import { GreenCircle } from '../components/GreenCircle';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';
import './Auth.css';

export const ResetPassword = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const { isDarkMode, isTransitioning } = useTheme();

  const validateEmail = (email: string) => {
    return email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Reset previous messages
    setError(null);
    setMessage(null);

    // Validate email
    if (!email) {
      setError('Email is required');
      return;
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      // Try both API path prefixes to handle deployment differences
      let response;
      try {
        response = await api.post('/reset-password/request/', { email });
      } catch (prefixError) {
        console.log('Trying alternative path with /api prefix');
        response = await api.post('/api/reset-password/request/', { email });
      }

      setMessage(response.data.message || 'Password reset instructions sent to your email.');
    } catch (error: any) {
      console.error('Reset password error:', error);
      setError(error.response?.data?.error || 'Error sending reset instructions. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`min-h-screen w-full ${isDarkMode ? 'bg-neutral-950' : 'bg-gray-50'} flex items-center justify-center p-4 ${isTransitioning ? 'theme-transitioning' : ''
      }`}>
      {/* Theme Toggle Button - Fixed Position */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2" style={{ zIndex: 0 }}>
        <GreenCircle />
      </div>
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <Link to="/">
            <img
              src={isDarkMode ? whiteLogo : darkLogo}
              alt="True Vision Logo"
              className="mx-auto w-21 h-21 mb-8"
            />
          </Link>
          <h2 className={`mt-8 text-2xl font-medium ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>Reset your Password</h2>
          <p className={`mt-4 text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Enter your email address and we will send you instructions to reset your password.
          </p>
        </div>

        {message && (
          <div className="mb-4 p-4 bg-green-600 text-white rounded-md">
            {message}
          </div>
        )}

        {error && (
          <div className="mb-4 p-4 bg-red-600 text-white rounded-md">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div>
            <Input
              type="email"
              placeholder="Email@gmail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'} placeholder:text-gray-400`}
              disabled={isLoading}
            />
          </div>

          <Button
            type="submit"
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Sending...
              </div>
            ) : (
              'Reset password'
            )}
          </Button>

          <div className="flex justify-between text-center">
            <Link to="/login" className="text-[#097F4D] text-sm hover:text-[#076b41]">
              Back to Login
            </Link>
            <Link to="/" className="text-[#097F4D] text-sm hover:text-[#076b41]">
              Home page
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;