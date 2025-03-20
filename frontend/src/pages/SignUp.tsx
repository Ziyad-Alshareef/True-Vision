import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import logo from "./assets/whitefont-transpa.png";
import { GreenCircle } from '../components/GreenCircle';

import api from "../api";

interface FormData {
  username: string;
  email: string;
  password: string;
}

export const SignUp = () => {
    const [formData, setFormData] = useState<FormData>({
        username: '',
        email: '',
        password: ''
    });
    const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
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
    <div className="min-h-screen bg-neutral-950 flex items-center justify-center p-4">
        <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2" style={{ zIndex: 0 }}>
        <GreenCircle />
      </div>
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          
          <img
            src={logo}
            alt="True Vision Logo"
            className="mx-auto w-21 h-21 mb-8"
          />
          <h1 className="text-3xl font-semibold text-white mb-2">
            Welcome to <span className="text-[#097F4D]">True Vision</span>
          </h1>
          <h2 className="mt-4 text-2xl font-medium text-white">Create an account</h2>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <Input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="bg-[#333333] border-none text-white placeholder:text-gray-400"
              />
            </div>
            <div>
              <Input
                type="text"
                placeholder="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="bg-[#333333] border-none text-white placeholder:text-gray-400"
              />
            </div>
            <div>
              <Input
                type="password"
                placeholder="Password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="bg-[#333333] border-none text-white placeholder:text-gray-400"
              />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full bg-[#097F4D] hover:bg-[#076b41] text-white"
          >
            Sign up
          </Button>

          <div className="text-center text-sm">
            <span className="text-gray-400">Already have an account? </span>
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