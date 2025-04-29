import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import whiteLogo from "./assets/whitefont-transpa.png";
import darkLogo from "./assets/output-onlinepngtoolsblack font transpa.png";
import deepFakeHero from "./assets/deep-fake-hero.png";
import { GreenCircle } from '../components/GreenCircle';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';
import './Home.css';

export const Home = () => {
  const { isDarkMode, isTransitioning } = useTheme();

  return (
    <div className={`min-h-screen w-full ${isDarkMode ? 'bg-neutral-950' : 'bg-gray-50'} flex flex-col ${isTransitioning ? 'theme-transitioning' : ''}`}>
      {/* Theme Toggle Button - Fixed Position */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2" style={{ zIndex: 0 }}>
        <GreenCircle />
      </div>

      {/* Header */}
      <header className="p-6">
        <div className="flex items-center">
          <Link to="/">
            <img
              src={isDarkMode ? whiteLogo : darkLogo}
              alt="True Vision Logo"
              className="h-[90px] w-auto"
            />
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex items-center justify-center p-6">
        <div className="hero-section">
          {/* Left side - Image */}
          <div className="hero-image-wrapper">
            <div className="hero-image-container">
              <img
                src={deepFakeHero}
                alt="Deep Fake Detection"
                className="hero-image"
              />
            </div>
          </div>

          {/* Right side - Content */}
          <div className="hero-content">
            <h1 className="text-4xl md:text-5xl font-bold">
              <span className={isDarkMode ? "text-white" : "text-gray-800"}>True</span>{' '}
              <span className="text-[#097F4D]">Vision</span>
            </h1>
            <p className={`${isDarkMode ? "text-gray-400" : "text-gray-600"} text-lg`}>
              Enabling you to easily identify deepfake videos using AI algorithms.
            </p>
            <div className="flex gap-4">
              <Button
                asChild
                className="bg-[#097F4D] hover:bg-[#076b41] text-white px-6 py-2 text-lg"
              >
                <Link to="/signup">New account</Link>
              </Button>
              <Button
                asChild
                variant="outline"
                className="border-[#097F4D] text-[#097F4D] hover:bg-[#097F4D] hover:text-white px-6 py-2 text-lg"
              >
                <Link to="/login">Login</Link>
              </Button>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6">
        <div className="flex justify-center gap-4 text-sm">
          <Link to="/privacy-policy" className="text-[#097F4D] hover:text-[#076b41]">
            Privacy Policy
          </Link>
          <span className="text-[#097F4D]">|</span>
          <Link to="/contact" className="text-[#097F4D] hover:text-[#076b41]">
            Contact us
          </Link>
        </div>
      </footer>
    </div>
  );
};

export default Home;
