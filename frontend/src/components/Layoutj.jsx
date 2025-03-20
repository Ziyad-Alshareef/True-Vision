import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Layout = ({ children }) => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
    
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <nav className="p-4">
        <div className="container mx-auto flex justify-between items-center">
          <Link to="/" className="text-2xl font-bold text-green-500">True Vision</Link>
          <div className="space-x-4">
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="text-gray-300 hover:text-green-500">Dashboard</Link>
                <button 
                  onClick={handleLogout}
                  className="text-gray-300 hover:text-green-500"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-gray-300 hover:text-green-500">Login</Link>
                <Link to="/signup" className="bg-green-600 px-4 py-2 rounded-md hover:bg-green-700">
                  New account
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <main className="container mx-auto px-4">{children}</main>
    </div>
  );
};

export default Layout;