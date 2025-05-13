import './Dashboard.css';
import React from 'react';
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { useTheme } from '../context/ThemeContext';
import { useNavigate } from 'react-router-dom';
import { GreenCircle } from '../components/GreenCircle';

const NotFound: React.FC = () => {
    const { isDarkMode } = useTheme();
    const navigate = useNavigate();

    return (
        <div className={`dashboard-container ${isDarkMode ? '' : 'light'}`}>
            <div className="green-circle-container">
                <GreenCircle />
            </div>
            
            <div className="flex flex-col items-center justify-center w-full min-h-screen p-4">
                <Card className={`max-w-md w-full p-6 ${isDarkMode ? 'bg-neutral-900 text-white' : 'bg-white text-gray-900'}`}>
                    <div className="text-center">
                        <h1 className={`text-4xl font-bold mb-6 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            404
                        </h1>
                        <h2 className={`text-2xl font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            Page Not Found
                        </h2>
                        <p className={`text-lg mb-8 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                            The page you're looking for doesn't exist or has been moved.
                        </p>
                        <Button 
                            className="w-full" 
                            onClick={() => navigate('/')}>
                            Return to Home
                        </Button>
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default NotFound;