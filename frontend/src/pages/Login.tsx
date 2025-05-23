import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';
import api from "../api";
import whiteLogo from "./assets/whitefont-transpa.png";
import darkLogo from "./assets/output-onlinepngtoolsblack font transpa.png";
import { GreenCircle } from '../components/GreenCircle';
import './Auth.css';
import { Eye, EyeOff } from 'lucide-react';

interface FormData {
  username: string;
  password: string;
}

interface ValidationError {
  field: string;
  message: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
}

export const Login = () => {
  const navigate = useNavigate();
  const { isDarkMode, isTransitioning } = useTheme();
  const [formData, setFormData] = useState<FormData>({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const validateForm = (): boolean => {
    const newErrors: ValidationError[] = [];

    // Username validation
    if (formData.username.length > 50) {
      newErrors.push({ field: 'username', message: 'Username cannot exceed 50 characters' });
    }
    if (formData.username.length === 0) {
      newErrors.push({ field: 'username', message: 'Username is required' });
    }

    // Password validation
    if (formData.password.length > 50) {
      newErrors.push({ field: 'password', message: 'Password cannot exceed 50 characters' });
    }
    if (formData.password.length === 0) {
      newErrors.push({ field: 'password', message: 'Password is required' });
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      const dataToSend = {
        ...formData,
        username: formData.username.toLowerCase()
      };
      const response = await api.post<LoginResponse>('/api/token/', dataToSend);
      if (response.status === 200) {
        const data = response.data;
        localStorage.setItem('access', data.access);
        localStorage.setItem('refresh', data.refresh);
        localStorage.setItem('username', formData.username.toLowerCase());
        login();
        // Navigate to dashboard with a state flag to auto-start detection
        navigate('/dashboard', { state: { autoStartDetection: true } });
      }
    } catch (error) {
      console.error('Login error:', error);
      setErrors([{ field: 'general', message: 'Invalid username or password' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const getErrorForField = (field: string): string | undefined => {
    return errors.find(error => error.field === field)?.message;
  };

  return (
    <div className={`min-h-screen w-full ${isDarkMode ? 'bg-neutral-950' : 'bg-gray-50'} flex items-center justify-center p-4 relative overflow-hidden ${isTransitioning ? 'theme-transitioning' : ''}`}>
      {/* Theme Toggle Button - Fixed Position */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2" style={{ zIndex: 0 }}>
        <GreenCircle />
      </div>
      <div className="w-full max-w-md space-y-8 relative z-10">
        <div className="text-center">
          <Link to="/">
            <img
              src={isDarkMode ? whiteLogo : darkLogo}
              alt="True Vision Logo"
              className="mx-auto w-21 h-21 mb-8"
            />
          </Link>
          <h1 className={`text-3xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-800'} mb-2`}>Welcome back</h1>

          <h2 className={`mt-4 text-2xl font-medium ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>Sign in</h2>
        </div>

        {getErrorForField('general') && (
          <div className="p-4 bg-red-100 text-red-700 rounded-lg">
            {getErrorForField('general')}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <Input
                type="text"
                placeholder="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'} placeholder:text-gray-400`}
                maxLength={50}
              />
              {getErrorForField('username') && (
                <p className="text-red-500 text-sm mt-1">{getErrorForField('username')}</p>
              )}
            </div>
            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'} placeholder:text-gray-400 pr-10`}
                maxLength={50}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
              {getErrorForField('password') && (
                <p className="text-red-500 text-sm mt-1">{getErrorForField('password')}</p>
              )}
            </div>
          </div>

          <div className="text-right">
            <Link to="/reset-password" className="text-[#097F4D] text-sm hover:text-[#076b41]">
              Forgot Password?
            </Link>
          </div>

          <Button
            type="submit"
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Logging in...
              </div>
            ) : (
              'Login'
            )}
          </Button>

          <div className="text-center text-sm">
            <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>Don't have an account? </span>
            <Link to="/signup" className="text-[#097F4D] hover:text-[#076b41]">
              Sign Up
            </Link>
          </div>

          <div className="text-center">
            <Link to="/privacy-policy" className="text-[#097F4D] text-sm hover:text-[#076b41]">
              Privacy Policy
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;

