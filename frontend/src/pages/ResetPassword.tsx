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

export const ResetPassword = () => {
  const [email, setEmail] = useState('');
  
  const [message, setMessage] = useState<string>('');
  const { isDarkMode, isTransitioning } = useTheme();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        const response = await api.post('/api/reset-password/', email);
        if (response.status === 200) {
          setMessage('Password reset instructions sent to your email.');
        }
      } catch (error) {
        console.error('Reset password error:', error);
        setMessage('Error sending reset instructions. Please try again.');
      }
    // TODO: Implement """"real""either in backend or frontend whatevers right""" password reset logic
  };

  return (
    <div className={`min-h-screen w-full ${isDarkMode ? 'bg-neutral-950' : 'bg-gray-50'} flex items-center justify-center p-4 ${
      isTransitioning ? 'theme-transitioning' : ''
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
          <img
            src={isDarkMode ? whiteLogo : darkLogo}
            alt="True Vision Logo"
            className="mx-auto w-21 h-21 mb-8"
          />
          <h2 className={`mt-8 text-2xl font-medium ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>Reset your Password</h2>
          <p className={`mt-4 text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Enter your Email address and we will send you instructions to reset your password.
          </p>
        </div>
        {message && (
        <div className="mb-4 p-2 bg-green-600 text-white rounded">
          {message}
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
            />
          </div>

          <Button
            type="submit"
            className="w-full bg-[#097F4D] hover:bg-[#076b41] text-white"
          >
            Reset password
          </Button>

          <div className="text-center">
            <Link to="/" className="text-[#097F4D] text-sm hover:text-[#076b41]">
              Back to Home page
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};
export default ResetPassword;
/*
import React, { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';
import api from "../api";

interface FormData {
  email: string;
}

const ResetPassword: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    email: ''
  });
  const [message, setMessage] = useState<string>('');

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      const response = await api.post('/api/reset-password/', formData);
      if (response.status === 200) {
        setMessage('Password reset instructions sent to your email.');
      }
    } catch (error) {
      console.error('Reset password error:', error);
      setMessage('Error sending reset instructions. Please try again.');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-gray-800 rounded-lg">
      <h2 className="text-2xl font-bold mb-6 text-white">Reset Password</h2>
      {message && (
        <div className="mb-4 p-2 bg-green-600 text-white rounded">
          {message}
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <input
            type="email"
            placeholder="Email"
            className="w-full p-2 rounded bg-gray-700 text-white"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
          />
        </div>
        <button
          type="submit"
          className="w-full bg-green-600 text-white p-2 rounded hover:bg-green-700"
        >
          Send Reset Instructions
        </button>
      </form>
      <div className="mt-4 text-center text-gray-400">
        Remember your password?{' '}
        <Link to="/login" className="text-green-500 hover:text-green-400">
          Sign In
        </Link>
      </div>
    </div>
  );
};

export default ResetPassword; */