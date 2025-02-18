/*import Form from "../components/Form"

function Login() {
    return <Form route="/api/token/" method="login" />
}

export default Login


*/

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from "../api";
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/api/token/', formData);
      if (response.status === 200) {
        const data = response.data;
        localStorage.setItem('access', data.access);
        localStorage.setItem('refresh', data.refresh);
        login();
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-gray-800 rounded-lg">
      <h2 className="text-2xl font-bold mb-6 text-white">Sign in</h2>
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
          Login
        </button>
      </form>
      <div className="mt-4 text-center text-gray-400">
        <Link to="/reset-password" className="hover:text-green-500">
          Forgot Password?
        </Link>
      </div>
      <div className="mt-4 text-center text-gray-400">
        Don't have an account?{' '}
        <Link to="/signup" className="text-green-500 hover:text-green-400">
          Sign Up
        </Link>
      </div>
    </div>
  );
};
export default Login;