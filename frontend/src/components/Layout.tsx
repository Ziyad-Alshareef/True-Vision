import React from 'react';
import { useTheme } from '../context/ThemeContext';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isDarkMode, isTransitioning } = useTheme();

  return (
    <div 
      className={`min-h-screen w-full flex flex-col ${
        isDarkMode ? 'bg-gray-900 text-white dark' : 'bg-gray-50 text-gray-800 light'
      } ${isTransitioning ? 'theme-transitioning' : ''}`}
      style={{
        backgroundColor: isDarkMode ? 'rgb(17, 24, 39)' : 'rgb(249, 250, 251)',
        color: isDarkMode ? 'white' : 'rgb(31, 41, 55)'
      }}
    >
      <div className="p-0 m-0 w-full h-full flex-grow">
        <main className="w-full h-full">{children}</main>
      </div>
    </div>
  );
};

export default Layout; 