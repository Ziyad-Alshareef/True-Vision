/*import React from 'react';
import UploadArea from '../components/UploadArea';
import '../app.css';
import api from "../api";

const Home: React.FC = () => {
  const handleUpload = async (file: File): Promise<void> => {
    const formData = new FormData();
    formData.append('video', file);
    
    try {
      const response = await api.post('/api/detect/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log(response.data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-12">
      <h1 className="text-4xl font-bold mb-2">Welcome to True Vision tsx</h1>
      <p className="text-gray-400 mb-8">Detect the fake, defend the real</p>
      
      <UploadArea onUpload={handleUpload} />
      
      <div className="grid grid-cols-3 gap-8 mt-12">
        <div className="text-center">
          <div className="text-green-500 mb-4">
            {/* Icon */ /*}
          </div>
          <h3 className="font-semibold mb-2">Accurate Detection</h3>
          <p className="text-gray-400">Ensuring precise identification of manipulated content.</p>
        </div>
      </div>
    </div>
  );
};

export default Home; */
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import logo from "./assets/whitefont-transpa.png";
import { GreenCircle } from '../components/GreenCircle';

export const Home = () => {
  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col">
        <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2" style={{ zIndex: 0 }}>
        <GreenCircle />
      </div>
      {/* Header */}
      <header className="p-6">
        <div className="flex items-center">
          <img
            src={logo}
            alt="True Vision Logo"
            className="h-[90px] w-auto"
          />
          {/*<span className="text-white ml-2">TRUE VISION</span>*/}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex items-center justify-center p-6">
        <div className="flex flex-col md:flex-row items-center max-w-6xl mx-auto gap-12">
          {/* Left side - Image */}
          <div className="w-full md:w-1/2">
            <div className="rounded-lg overflow-hidden bg-black">{/*//////////////////////////ALI put the figma photo here please /////////////////////////////*/}
              <img
                src="/deep-fake-hero.png"
                alt="Deep Fake Detection"
                
                className="w-full h-auto"
              />
            </div>
          </div>

          {/* Right side - Content */}
          <div className="w-full md:w-1/2 text-center md:text-left">
            <h1 className="text-4xl font-bold mb-4">
              <span className="text-white">True</span>{' '}
              <span className="text-[#097F4D]">Vision</span>
            </h1>
            <p className="text-gray-400 mb-8">
              Enabling you to easily identify deepfake videos using AI algorithms.
            </p>
            <div className="flex gap-4 justify-center md:justify-start">
              <Button
                asChild
                className="bg-[#097F4D] hover:bg-[#076b41] text-white px-6"
              >
                <Link to="/signup">New account</Link>
              </Button>
              <Button
                asChild
                variant="outline"
                className="border-[#097F4D] text-[#097F4D] hover:bg-[#097F4D] hover:text-white px-6"
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
};export default Home;