import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import whiteLogo from "./assets/whitefont-transpa.png";
import darkLogo from "./assets/output-onlinepngtoolsblack font transpa.png";
import { GreenCircle } from '../components/GreenCircle';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';
import api from "../api";
import axios from 'axios';
import './Auth.css';
import { Eye, EyeOff } from 'lucide-react';
const PASSWORD_FIELD_OPACITY = 0.9;

interface FormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface ValidationError {
  field: string;
  message: string;
}

export const SignUp = () => {
  const [formData, setFormData] = useState<FormData>({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { isDarkMode, isTransitioning } = useTheme();

  const validateForm = (): boolean => {
    const newErrors: ValidationError[] = [];

    // Username validation
    if (formData.username.length < 5) {
      newErrors.push({ field: 'username', message: 'Username must be at least 5 characters long' });
    }
    if (formData.username.length > 50) {
      newErrors.push({ field: 'username', message: 'Username cannot exceed 50 characters' });
    }

    // Email validation
    if (formData.email.length > 50) {
      newErrors.push({ field: 'email', message: 'Email cannot exceed 50 characters' });
    }
    if (!formData.email.includes('@')) {
      newErrors.push({ field: 'email', message: 'Please enter a valid email address' });
    }

    // Password validation
    if (formData.password.length < 8) {
      newErrors.push({ field: 'password', message: 'Password must be at least 8 characters long' });
    }
    if (formData.password.length > 50) {
      newErrors.push({ field: 'password', message: 'Password cannot exceed 50 characters' });
    }
    if (!/[a-zA-Z]/.test(formData.password)) {
      newErrors.push({ field: 'password', message: 'Password must contain at least one letter' });
    }

    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      newErrors.push({ field: 'confirmPassword', message: 'Passwords do not match' });
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
        email: formData.email.toLowerCase(),
        username: formData.username.toLowerCase()
      };
      
      // Create a new axios instance without auth headers for signup
      const signupApi = axios.create({
        baseURL: api.defaults.baseURL,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const response = await signupApi.post('/api/signup/', dataToSend);
      
      if (response.status === 201) {
        setSuccessMessage('Registration successful! Redirecting to login...');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      }
    } catch (error: any) {
      console.error('Signup error:', error);
      if (error.response?.data) {
        const errorData = error.response.data;
        console.log('Error data:', errorData); // For debugging
        
        // Handle array format validation errors
        if (Array.isArray(errorData.username)) {
          setErrors([{ field: 'username', message: errorData.username[0] }]);
        } 
        // Handle string format validation errors 
        else if (typeof errorData.username === 'string') {
          setErrors([{ field: 'username', message: errorData.username }]);
        }
        // Handle array format email errors
        else if (Array.isArray(errorData.email)) {
          setErrors([{ field: 'email', message: errorData.email[0] }]);
        } 
        // Handle string format email errors
        else if (typeof errorData.email === 'string') {
          setErrors([{ field: 'email', message: errorData.email }]);
        }
        // Handle generic detail error
        else if (errorData.detail) {
          setErrors([{ field: 'general', message: errorData.detail }]);
        }
        // Handle generic error message
        else if (errorData.error) {
          setErrors([{ field: 'general', message: errorData.error }]);
        }
        // Fallback to general error
        else {
          setErrors([{ field: 'general', message: 'Registration failed. Please try again.' }]);
        }
      } else {
        setErrors([{ field: 'general', message: 'Registration failed. Please try again.' }]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getErrorForField = (field: string): string | undefined => {
    return errors.find(error => error.field === field)?.message;
  };

  return (
    <div className={`min-h-screen w-full ${isDarkMode ? 'bg-neutral-950' : 'bg-gray-50'} flex items-center justify-center p-4 ${isTransitioning ? 'theme-transitioning' : ''}`}>
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
          <h1 className={`text-3xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-800'} mb-2`}>
            Welcome to <span className="text-[#097F4D]">True Vision</span>
          </h1>
          <h2 className={`mt-4 text-2xl font-medium ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>Create an account</h2>
        </div>

        {successMessage && (
          <div className="p-4 bg-green-100 text-green-700 rounded-lg">
            {successMessage}
          </div>
        )}

        {getErrorForField('general') && (
          <div className="p-4 bg-red-100 text-red-700 rounded-lg">
            {getErrorForField('general')}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <Input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'} placeholder:text-gray-400`}
                maxLength={50}
              />
              {getErrorForField('email') && (
                <p className="text-red-500 text-sm mt-1">{getErrorForField('email')}</p>
              )}
            </div>
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
            <div>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className={`${isDarkMode ? '!bg-[#3c4336] border-none text-white' : '!bg-[#e2e7da] border border-gray-400 text-gray-800'} placeholder:text-gray-400 pr-10`} // !important to enforce dark bg
                  autoComplete="new-password"
                  maxLength={50}
                  style={{ opacity: PASSWORD_FIELD_OPACITY }}
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
              {getErrorForField('password') && (
                <p className="text-red-500 text-sm mt-1">{getErrorForField('password')}</p>
              )}
            </div>
            <div>
              <div className="relative">
                <Input
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Confirm Password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className={`${isDarkMode ? '!bg-[#3c4336] border-none text-white' : '!bg-[#e2e7da] border border-gray-400 text-gray-800'} placeholder:text-gray-400 pr-10`} // !important to enforce dark bg
                  autoComplete="new-password"
                  maxLength={50}
                  style={{ opacity: PASSWORD_FIELD_OPACITY }}
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
              {getErrorForField('confirmPassword') && (
                <p className="text-red-500 text-sm mt-1">{getErrorForField('confirmPassword')}</p>
              )}
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
                Signing up...
              </div>
            ) : (
              'Sign up'
            )}
          </Button>

          <div className="text-center text-sm">
            <span className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>Already have an account? </span>
            <Link to="/login" className="text-[#097F4D] hover:text-[#076b41]">
              Login
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

export default SignUp;

/*import React, { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from "../api";

interface FormData {
  username: string;
  email: string;
  password: string;
}

const SignUp: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    username: '',
    email: '',
    password: ''
  });
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      const response = await api.post('/api/signup/', formData);
      if (response.status === 201) {
        navigate('/login');
      }
    } catch (error) {
      console.error('Signup error:', error);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-gray-800 rounded-lg">
      <h2 className="text-2xl font-bold mb-6 text-white">Create an account</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <input
            type="text"
            placeholder="Username"
            className="w-full p-2 rounded bg-gray-700 text-white"
            value={formData.username}
            onChange={(e) => setFormData({...formData, username: e.target.value})}
          />
        </div>
        <div className="mb-4">
          <input
            type="email"
            placeholder="Email"
            className="w-full p-2 rounded bg-gray-700 text-white"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
          />
        </div>
        <div className="mb-4">
          <input
            type="password"
            placeholder="Password"
            className="w-full p-2 rounded bg-gray-700 text-white"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
          />
        </div>
        <button
          type="submit"
          className="w-full bg-green-600 text-white p-2 rounded hover:bg-green-700"
        >
          Sign Up
        </button>
      </form>
      <div className="mt-4 text-center text-gray-400">
        Already have an account?{' '}
        <Link to="/login" className="text-green-500 hover:text-green-400">
          Sign In
        </Link>
      </div>
    </div>
  );
};

export default SignUp; */