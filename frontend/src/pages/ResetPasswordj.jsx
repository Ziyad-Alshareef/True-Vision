import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';

const ResetPassword = () => {
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [token, setToken] = useState('');
  const [step, setStep] = useState('request'); // 'request' or 'reset'
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  // Check for token in URL when component mounts
  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tokenFromUrl = params.get('token');
    if (tokenFromUrl) {
      setToken(tokenFromUrl);
      setStep('reset');
    }
  }, [location]);

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    try {
      const response = await fetch('http://localhost:8000/api/request-password-reset/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setMessage('Password reset instructions have been sent to your email.');
      } else {
        const data = await response.json();
        setError(data.detail || 'An error occurred. Please try again.');
      }
    } catch (error) {
      setError('Network error. Please try again later.');
    }
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/reset-password/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token,
          new_password: newPassword,
        }),
      });

      if (response.ok) {
        setMessage('Password has been successfully reset.');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        const data = await response.json();
        setError(data.detail || 'An error occurred. Please try again.');
      }
    } catch (error) {
      setError('Network error. Please try again later.');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-gray-800 rounded-lg">
      <h2 className="text-2xl font-bold mb-6 text-white">
        {step === 'request' ? 'Reset Password' : 'Create New Password'}
      </h2>

      {message && (
        <div className="mb-4 p-3 bg-green-600 text-white rounded">
          {message}
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-600 text-white rounded">
          {error}
        </div>
      )}

      {step === 'request' ? (
        <form onSubmit={handleRequestReset}>
          <div className="mb-4">
            <input
              type="email"
              placeholder="Enter your email"
              className="w-full p-2 rounded bg-gray-700 text-white"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-green-600 text-white p-2 rounded hover:bg-green-700"
          >
            Send Reset Instructions
          </button>
        </form>
      ) : (
        <form onSubmit={handlePasswordReset}>
          <div className="mb-4">
            <input
              type="password"
              placeholder="New password"
              className="w-full p-2 rounded bg-gray-700 text-white"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>
          <div className="mb-4">
            <input
              type="password"
              placeholder="Confirm new password"
              className="w-full p-2 rounded bg-gray-700 text-white"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>
          <button
            type="submit"
            className="w-full bg-green-600 text-white p-2 rounded hover:bg-green-700"
          >
            Reset Password
          </button>
        </form>
      )}

      <div className="mt-4 text-center text-gray-400">
        Remember your password?{' '}
        <Link to="/login" className="text-green-500 hover:text-green-400">
          Sign In
        </Link>
      </div>
    </div>
  );
};

export default ResetPassword;