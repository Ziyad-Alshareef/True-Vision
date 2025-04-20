import React, { useState, useRef } from 'react';
import { Button } from '../components/ui/button';
import api from '../api';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';

export const Detection = () => {
  const { isDarkMode, isTransitioning } = useTheme();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (file) {
      // Check if file is a video
      if (!file.type.startsWith('video/')) {
        setError('Please select a valid video file');
        return;
      }
      
      // Check file size (limit to 100MB for example)
      if (file.size > 100 * 1024 * 1024) {
        setError('File is too large. Maximum size is 100MB');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
    }
  };

  // Handle drag and drop
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    const file = e.dataTransfer.files?.[0] || null;
    if (file) {
      if (!file.type.startsWith('video/')) {
        setError('Please select a valid video file');
        return;
      }
      
      if (file.size > 100 * 1024 * 1024) {
        setError('File is too large. Maximum size is 100MB');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  // Handle upload
  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a video file');
      return;
    }

    try {
      setIsUploading(true);
      setUploadProgress(0);
      setError(null);

      const formData = new FormData();
      formData.append('video', selectedFile);

      // Make API request with upload progress
      const response = await api.post('/api/test/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 100)
          );
          setUploadProgress(percentCompleted);
        },
      });

      // Check response and handle success
      if (response.status === 201) {
        console.log('Upload successful:', response.data);
        
        // Store the video ID in localStorage so we can highlight it in the dashboard
        if (response.data && response.data.video_id) {
          localStorage.setItem('last_uploaded_video_id', response.data.video_id.toString());
          console.log('Stored video ID for highlighting:', response.data.video_id);
          
          // Store the direct S3 placeholder URL based on video ID
          const placeholderUrl = `https://s3.us-west-2.amazonaws.com/true-vision/media/thumbnails/placeholder_${response.data.video_id}.jpg`;
          localStorage.setItem('last_thumbnail_url', placeholderUrl);
          console.log('Stored direct S3 placeholder URL:', placeholderUrl);
        }
        
        // Log the thumbnail URL if available
        if (response.data && response.data.thumbnail_path) {
          console.log('Thumbnail path in response:', response.data.thumbnail_path);
          localStorage.setItem('last_api_thumbnail_url', response.data.thumbnail_path);
          
          // Also try to extract and store the S3 URL directly if it's not a direct URL
          if (response.data.thumbnail_path && !response.data.thumbnail_path.startsWith('http')) {
            // It's likely a relative path, convert to S3 URL
            const filename = response.data.thumbnail_path.split('/').pop();
            const s3Url = `https://s3.us-west-2.amazonaws.com/true-vision/media/thumbnails/${filename}`;
            localStorage.setItem('last_s3_thumbnail_url', s3Url);
            console.log('Converted to S3 URL:', s3Url);
          } else if (response.data.thumbnail_path) {
            localStorage.setItem('last_s3_thumbnail_url', response.data.thumbnail_path);
          }
        }
        
        // Pass a refresh flag and the video ID in the state
        navigate('/dashboard', { 
          state: { 
            refresh: true,
            lastUploadedVideoId: response.data?.video_id,
            directThumbnailUrl: localStorage.getItem('last_s3_thumbnail_url')
          }
        });
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError('Failed to upload and analyze video. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  // Handle click on upload area to trigger file input
  const handleUploadAreaClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={`flex-grow w-full ${isDarkMode ? 'bg-[#222222]' : 'bg-gray-50'} p-6 ${
      isTransitioning ? 'theme-transitioning' : ''
    }`}>
      {/* Theme Toggle Button - Fixed Position 
      <div className="fixed top-6 right-6 z-50">
        <ThemeToggle />
      </div>*/}
      
      <div className="max-w-6xl mx-auto text-center">
        <h1 className="text-3xl font-semibold mb-2">
          <span className={isDarkMode ? 'text-white' : 'text-gray-800'}>New </span>
          <span className="text-[#097F4D]">Detection</span>
        </h1>
        <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600'} mb-12`}>Upload a video for deepfake detection</p>

        {/* Upload Area */}
        <div 
          className={`border-2 border-dashed ${selectedFile ? 'border-[#097F4D]' : isDarkMode ? 'border-gray-600' : 'border-gray-300'} rounded-lg p-12 mb-8 cursor-pointer hover:border-[#097F4D] transition-colors ${isDarkMode ? 'bg-neutral-900/30' : 'bg-gray-50'}`}
          onClick={handleUploadAreaClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          {selectedFile ? (
            <div className="text-center">
              <p className="text-[#097F4D] font-medium">{selectedFile.name}</p>
              <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500' } text-sm mt-2`}>
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          ) : (
            <div>
              <p className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>Drag and drop your video here, or click to upload</p>
              <p className={`${isDarkMode ? 'text-gray-500' : 'text-gray-500' }  text-sm mt-2`}>Supported formats: MP4, MOV, AVI (Max: 100MB)</p>
            </div>
          )}
          
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept="video/*"
            onChange={handleFileChange}
          />
        </div>

        {/* Error message */}
        {error && (
          <div className={`${isDarkMode ? 'bg-red-500/20' : 'bg-red-100'} ${isDarkMode ? 'text-red-400' : 'text-red-600'} p-3 rounded-md mb-6`}>
            {error}
          </div>
        )}

        {/* Upload progress */}
        {isUploading && (
          <div className="mb-6">
            <div className={`h-2 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded-full mb-2`}>
              <div 
                className="h-2 bg-[#097F4D] rounded-full" 
                style={{ width: `${uploadProgress}%` }} 
              />
            </div>
            <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600' } text-sm`}>Uploading... {uploadProgress}%</p>
          </div>
        )}

        {/* Upload button */}
        <Button
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          className="bg-[#097F4D] hover:bg-[#076b41] text-white px-8 py-2 mb-12 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? 'Uploading...' : 'Analyze Video'}
        </Button>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-12 h-12 mx-auto mb-4 flex items-center justify-center">
              <svg className="w-8 h-8 text-[#097F4D]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className={`${isDarkMode ? 'text-white' : 'text-gray-800' }  font-medium mb-2`}>Accurate Detection</h3>
            <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600' }  text-sm`}>Ensuring precise identification of manipulated content.</p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 mx-auto mb-4 flex items-center justify-center">
              <svg className="w-8 h-8 text-[#097F4D]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            </div>
            <h3 className={`${isDarkMode ? 'text-white' : 'text-gray-800' }  font-medium mb-2`}>Upload Your Video</h3>
            <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600' }  text-sm`}>Easily provide a video for deepfake detection.</p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 mx-auto mb-4 flex items-center justify-center">
              <svg className="w-8 h-8 text-[#097F4D]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className={`${isDarkMode ? 'text-white' : 'text-gray-800' } font-medium mb-2`}>Instant Results</h3>
            <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600' } text-sm`}>Get detection outcomes in seconds.</p>
          </div>
        </div>
      </div>
    </div>
  );
};