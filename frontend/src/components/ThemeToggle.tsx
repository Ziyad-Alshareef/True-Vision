import React, { useState } from 'react';
import { SunIcon, MoonIcon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { Button } from './ui/button';

interface ThemeToggleProps {
  variant?: 'default' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  variant = 'ghost',
  size = 'md',
  className = ''
}) => {
  const { isDarkMode, toggleTheme } = useTheme();
  const [isAnimating, setIsAnimating] = useState(false);
  
  const getSize = () => {
    switch (size) {
      case 'sm': return 'h-4 w-4';
      case 'lg': return 'h-6 w-6';
      default: return 'h-5 w-5';
    }
  };
  
  const iconSize = getSize();
  const buttonSize = size === 'sm' ? 'p-1' : size === 'lg' ? 'p-3' : 'p-2';
  
  const handleToggle = () => {
    if (isAnimating) return; // Prevent multiple clicks during animation
    
    setIsAnimating(true);
    toggleTheme();
    setTimeout(() => setIsAnimating(false), 300);
  };
  
  return (
    <Button
      variant={variant}
      className={`rounded-full ${buttonSize} ${className} overflow-hidden relative`}
      onClick={handleToggle}
      title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
    >
      <div className={`${isAnimating ? 'icon-animate' : ''}`}>
        {isDarkMode ? (
          <SunIcon className={iconSize} />
        ) : (
          <MoonIcon className={iconSize} />
        )}
      </div>
    </Button>
  );
}; 