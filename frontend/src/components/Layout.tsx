import React from 'react';
import { useTheme } from '../context/ThemeContext';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isDarkMode, isTransitioning } = useTheme();

  return (
    <div 
      className={`min-h-screen w-full ${isDarkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-800'} ${
        isTransitioning ? 'theme-transitioning' : ''
      }`}
    >
      <main className="w-full">{children}</main>
    </div>
  );
};

export default Layout; 