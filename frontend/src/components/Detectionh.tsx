import React, { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { Button } from './ui/button';
import api from '../api';

export const Detection: React.FC = () => {
  const { isDarkMode } = useTheme();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [analysisInProgress, setAnalysisInProgress] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string>('');
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadMessage('');
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setUploadMessage('Please select a file first');
      return;
    }
    
    setUploading(true);
    setUploadMessage('Uploading file...');
    setUploadProgress(0);
    
    // Create form data for upload
    const formData = new FormData();
    formData.append('video', file);
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);
      
      // Upload the file
      const response = await api.post('/api/analysis/create/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (response.status === 201 || response.status === 200) {
        setUploadMessage('Upload complete! Analyzing content...');
        setAnalysisInProgress(true);
        
        // Here you'd typically start polling for analysis results
        // For demo, we'll simulate it
        setTimeout(() => {
          setAnalysisInProgress(false);
          setUploadMessage('Analysis complete! Refresh the page to see results.');
          setUploading(false);
        }, 5000);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadMessage('Error uploading file. Please try again.');
      setUploading(false);
      setUploadProgress(0);
    }
  };
  
  return (
    <div className={`flex-grow ${isDarkMode ? 'bg-[#222222]' : 'bg-gray-50'} p-6`}>
      <div className="max-w-3xl mx-auto">
        <h1 className={`text-2xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-800'} mb-6`}>
          Start a new detection
        </h1>
        
        <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-[#2A2A2A]' : 'bg-white'} shadow-sm`}>
          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label 
                className={`block mb-2 font-medium ${isDarkMode ? 'text-neutral-200' : 'text-gray-700'}`}
              >
                Upload a video or image file
              </label>
              
              <div 
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer ${
                  isDarkMode 
                    ? 'border-[#444444] hover:border-[#666666] bg-[#333333]' 
                    : 'border-gray-300 hover:border-gray-400 bg-gray-50'
                }`}
                onClick={() => document.getElementById('file-upload')?.click()}
              >
                <input
                  type="file"
                  id="file-upload"
                  accept="video/*,image/*"
                  className="hidden"
                  onChange={handleFileChange}
                  disabled={uploading || analysisInProgress}
                />
                
                {file ? (
                  <div className={`${isDarkMode ? 'text-neutral-200' : 'text-gray-800'}`}>
                    <p>Selected file: {file.name}</p>
                    <p className="text-sm mt-1">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div className={`${isDarkMode ? 'text-neutral-400' : 'text-gray-500'}`}>
                    <p>Drag and drop file here or click to browse</p>
                    <p className="text-sm mt-1">
                      Supported formats: MP4, AVI, JPG, PNG
                    </p>
                  </div>
                )}
              </div>
            </div>
            
            {uploadMessage && (
              <div className={`mb-4 ${
                uploadMessage.includes('Error') 
                  ? 'text-red-500' 
                  : uploadMessage.includes('complete') 
                    ? 'text-green-500' 
                    : isDarkMode ? 'text-neutral-200' : 'text-gray-700'
              }`}>
                {uploadMessage}
              </div>
            )}
            
            {(uploading || analysisInProgress) && (
              <div className="mb-4">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-green-600 h-2.5 rounded-full" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}
            
            <Button
              type="submit"
              className="w-full bg-[#097F4D] hover:bg-[#076b41] text-white"
              disabled={uploading || analysisInProgress || !file}
            >
              {uploading ? 'Uploading...' : analysisInProgress ? 'Analyzing...' : 'Start Detection'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}; 