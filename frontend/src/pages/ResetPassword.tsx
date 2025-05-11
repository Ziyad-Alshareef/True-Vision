import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import api from "../api";
import whiteLogo from "./assets/whitefont-transpa.png";
import darkLogo from "./assets/output-onlinepngtoolsblack font transpa.png";
import { GreenCircle } from '../components/GreenCircle';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';
import './Auth.css';
import { Eye, EyeOff } from 'lucide-react';

export const ResetPassword = () => {
  const [email, setEmail] = useState('');
  const [pin, setPin] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [stage, setStage] = useState('requestPin'); // 'requestPin' or 'resetPassword'
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string>('');
  const { isDarkMode, isTransitioning } = useTheme();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const navigate = useNavigate();

  const handleRequestPin = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation(); // Prevent event bubbling for Safari
    setError('');
    setMessage('');
    setIsLoading(true);
    
    if (!email) {
      setError('Email is required');
      setIsLoading(false);
      return;
    }
    
    try {
      console.log('Sending PIN request for email:', email);
      const response = await api.post('/api/forgot-password/', { email });
      console.log('PIN request response:', response);
      
      if (response.status === 200) {
        setMessage(response.data.message || 'PIN sent to your email.');
        setStage('resetPassword');
      }
    } catch (error: any) {
      console.error('Request PIN error:', error);
      setError(error.response?.data?.error || 'Error sending PIN. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation(); // Prevent event bubbling for Safari
    setError('');
    setMessage('');
    setIsLoading(true);
    
    if (!email || !pin || !newPassword) {
      setError('All fields are required');
      setIsLoading(false);
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }
    
    try {
      console.log('Sending password reset request with data:', { 
        email, 
        pin, 
        new_password_length: newPassword.length 
      });
      
      const response = await api.post('/api/reset-password/', { 
        email,
        pin,
        new_password: newPassword
      });
      
      console.log('Password reset response:', response);
      
      if (response.status === 200) {
        setMessage(response.data.message || 'Password reset successful.');
        // Redirect to login after 2 seconds
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      }
    } catch (error: any) {
      console.error('Reset password error:', error);
      setError(error.response?.data?.error || 'Error resetting password. Please try again.');
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
          <h2 className={`mt-8 text-2xl font-medium ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
            {stage === 'requestPin' ? 'Reset your Password' : 'Enter Reset PIN'}
          </h2>
          <p className={`mt-4 text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            {stage === 'requestPin' 
              ? 'Enter your Email address and we will send you a PIN to reset your password.'
              : 'Enter the PIN sent to your email and your new password.'}
          </p>
        </div>
        
        {message && (
          <div className="mb-4 p-2 bg-green-600 text-white rounded text-center">
            {message}
          </div>
        )}
        
        {error && (
          <div className="mb-4 p-2 bg-red-600 text-white rounded text-center">
            {error}
          </div>
        )}
        
        {stage === 'requestPin' ? (
          <form onSubmit={handleRequestPin} className="mt-8 space-y-6">
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
              disabled={isLoading}
              className="auth-button"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Requesting PIN...
                </div>
              ) : (
                'Request PIN'
              )}
            </Button>

            <div className="text-center">
              <Link to="/login" className="text-[#097F4D] text-sm hover:text-[#076b41]">
                Back to Login
              </Link>
            </div>
          </form>
        ) : (
          <form onSubmit={handleResetPassword} className="mt-8 space-y-6">
            <div className="space-y-4">
            <div className="relative">
              <Input
                type="email"
                placeholder="Email@gmail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'} placeholder:text-gray-400`}
              />
              </div>
              <div className="relative">
              <Input
                type="text"
                placeholder="Enter PIN"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'} placeholder:text-gray-400`}
              /></div>
              <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                placeholder="New Password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'} placeholder:text-gray-400`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 z-20"
                style={{ marginTop: '-1px' }}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button> 
              </div>
              <div className="relative">
              <Input
                type={showConfirmPassword ? "text" : "password"}
                placeholder="Confirm New Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'} placeholder:text-gray-400`}
              />
              <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 z-20"
                  style={{ marginTop: '-1px' }}
                >
                  {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="auth-button"
              disabled={isLoading}
            >
              {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Resetting Password...
              </div>
            ) : (
              'Reset Password'
            )}
            </Button>

            <div className="text-center space-y-2">
              <button 
                type="button" 
                onClick={() => setStage('requestPin')}
                className="text-[#097F4D] text-sm hover:text-[#076b41] block w-full"
              >
                Request new PIN
              </button>
              
              <Link to="/login" className="text-[#097F4D] text-sm hover:text-[#076b41] block">
                Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ResetPassword;