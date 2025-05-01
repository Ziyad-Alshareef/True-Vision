import {
  CpuIcon,
  PlusIcon,
  SunIcon,
  MoonIcon,
  TrashIcon,
  LogOutIcon,
  MenuIcon,
  XIcon,
} from "lucide-react";
import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Separator } from "../components/ui/separator";
import { Detection } from "./Detection";
import api from "../api";
import logo from "./assets/logo-transpa.png";
import { GreenCircle } from '../components/GreenCircle';
import { useTheme } from '../context/ThemeContext';
import './Dashboard.css';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";

// Add this constant for API base URL (since importing it directly has issues)
const API_BASE_URL = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL : "/choreo-apis/awbo/backend/rest-api-be2/v1.0";

// Define location state interface
interface LocationState {
  signedThumbnailUrl?: string;
  lastUploadedVideoId?: string;
}

// Define the analysis interface
interface Analysis {
  id: string;
  confidence: string;
  duration: string;
  resolution?: string;
  fps?: string;
  created_at: string;
  result: {
    is_fake: boolean;
    confidence: number;
    video_id?: number;
  };
  thumbnail_url?: string;
  video_url?: string;
}

// Add a function to format URLs correctly
const formatUrl = (baseUrl: string, path: string): string => {
  // Remove trailing slash from base URL if present
  const cleanBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  // Remove leading slash from path if present
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${cleanBase}/${cleanPath}`;
};

// Add helper functions for thumbnail handling
const getS3KeyFromUrl = (url: string): string | null => {
  if (!url) return null;

  // Remove any query parameters first (everything after '?')
  const baseUrl = url.split('?')[0];

  // For URLs like https://true-vision.s3.amazonaws.com/media/thumbnails/placeholder_1.jpg
  if (baseUrl.includes('amazonaws.com')) {
    const parts = baseUrl.split('amazonaws.com/');
    if (parts.length > 1) {
      return parts[1];
    }
  }

  // For URLs that are just keys like media/thumbnails/placeholder_1.jpg
  if (baseUrl.startsWith('media/')) {
    return baseUrl;
  }

  // For Django media URLs like /media/thumbnails/placeholder_1.jpg
  if (baseUrl.startsWith('/media/')) {
    return baseUrl.substring(1); // Remove leading slash
  }

  // If it contains thumbnail or placeholder in the path
  if (baseUrl.includes('thumbnail_') || baseUrl.includes('placeholder_')) {
    // Extract just the filename
    const filename = baseUrl.split('/').pop();
    if (filename) {
      // Try to extract video ID from filename
      const match = filename.match(/(?:thumbnail|placeholder)_(\d+)\.jpg$/);
      if (match && match[1]) {
        const videoId = match[1];
        return `media/thumbnails/${filename}`;
      }
      return `media/thumbnails/${filename}`;
    }
  }

  return null;
};

const getSignedUrl = async (s3Key: string): Promise<string | null> => {
  try {
    // Remove any query parameters first (everything after '?')
    const cleanKey = s3Key.split('?')[0];

    console.log(`Getting signed URL for clean key: ${cleanKey}`);

    // First try the /s3/signed-url/ endpoint (which should be in the updated API)
    try {
      const response = await api.get(`/s3/signed-url/?key=${encodeURIComponent(cleanKey)}`);
      if (response.status === 200 && response.data && response.data.signed_url) {
        console.log(`Got signed URL for ${cleanKey}:`, response.data.signed_url);
        return response.data.signed_url;
      }
    } catch (newEndpointError) {
      console.log('New endpoint not available, trying legacy endpoint');
      // Fall back to legacy endpoint
      const legacyResponse = await api.get(`/api/s3/signed-url/?key=${encodeURIComponent(cleanKey)}`);
      if (legacyResponse.status === 200 && legacyResponse.data && legacyResponse.data.signed_url) {
        console.log(`Got signed URL from legacy endpoint for ${cleanKey}:`, legacyResponse.data.signed_url);
        return legacyResponse.data.signed_url;
      }
    }

    return null;
  } catch (error) {
    console.error('Error getting signed URL:', error);
    return null;
  }
};

// Add a function to check if endpoints are available on the backend
const checkEndpointAvailability = (() => {
  // Cache the availability status
  const availabilityCache: Record<string, boolean> = {};

  // Return a function that checks availability
  return async (endpoint: string): Promise<boolean> => {
    // Return from cache if already checked
    if (availabilityCache.hasOwnProperty(endpoint)) {
      return availabilityCache[endpoint];
    }

    try {
      // Try a HEAD request to check if endpoint exists
      const response = await api.head(endpoint);
      availabilityCache[endpoint] = response.status < 400;
      return availabilityCache[endpoint];
    } catch (error) {
      console.log(`Endpoint ${endpoint} not available:`, error);
      availabilityCache[endpoint] = false;
      return false;
    }
  };
})();

// Fix the checkS3ObjectExists function to handle nullable signedUrl correctly
const checkS3ObjectExists = async (key: string): Promise<{ exists: boolean, alternateKey?: string, signedUrl?: string }> => {
  try {
    // First check if the endpoint is available
    const isEndpointAvailable = await checkEndpointAvailability('/s3/object-exists/');

    if (!isEndpointAvailable) {
      console.log('S3 object-exists endpoint not available, using direct signed URL');
      try {
        // Fall back to getting a signed URL directly
        const directSignedUrl = await getSignedUrl(key);
        return {
          exists: !!directSignedUrl,
          signedUrl: directSignedUrl || undefined  // Convert null to undefined
        };
      } catch (signedUrlError) {
        console.error('Error getting signed URL:', signedUrlError);
        return { exists: false };
      }
    }

    // If endpoint is available, use it
    const response = await api.get(`/s3/object-exists/?key=${encodeURIComponent(key)}`);
    if (response.status === 200) {
      console.log(`Object exists check for ${key}:`, response.data);
      return {
        exists: response.data.exists,
        alternateKey: response.data.alternate_key,
        signedUrl: response.data.signed_url
      };
    }
    return { exists: false };
  } catch (error) {
    console.error('Error checking if S3 object exists:', error);
    try {
      // Fall back to getting a signed URL directly
      const directSignedUrl = await getSignedUrl(key);
      return {
        exists: !!directSignedUrl,
        signedUrl: directSignedUrl || undefined  // Convert null to undefined
      };
    } catch (signedUrlError) {
      console.error('Error getting fallback signed URL:', signedUrlError);
      return { exists: false };
    }
  }
};

export const Dashboard = (): JSX.Element => {
  const navigate = useNavigate();
  const location = useLocation();
  const locationState = location.state as LocationState;
  const { isDarkMode, toggleTheme } = useTheme();
  const [selectedResult, setSelectedResult] = useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [showDetection, setShowDetection] = useState(false);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isClearAllDialogOpen, setIsClearAllDialogOpen] = useState(false);
  const [isNoResultsDialogOpen, setIsNoResultsDialogOpen] = useState(false);
  const [isImageLoading, setIsImageLoading] = useState(false);

  // Add viewport height calculation effect
  useEffect(() => {
    const updateHeight = () => {
      // First we get the viewport height and we multiple it by 1% to get a value for a vh unit
      const vh = window.innerHeight * 0.01;
      // Then we set the value in the --vh custom property to the root of the document
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    // Initial calculation
    updateHeight();

    // Add event listeners for resize and orientation change
    window.addEventListener('resize', updateHeight);
    window.addEventListener('orientationchange', updateHeight);

    // Cleanup
    return () => {
      window.removeEventListener('resize', updateHeight);
      window.removeEventListener('orientationchange', updateHeight);
    };
  }, []);

  // Fetch analyses effect
  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        const token = localStorage.getItem('access');
        if (!token) {
          navigate('/login');
          return;
        }

        setIsLoading(true);

        // Check if we have a signed thumbnail URL from the upload
        const signedThumbnailUrl = locationState?.signedThumbnailUrl ||
          localStorage.getItem('last_signed_thumbnail_url') ||
          localStorage.getItem('last_api_signed_url');

        const lastUploadedId = locationState?.lastUploadedVideoId ||
          localStorage.getItem('last_uploaded_video_id');

        if (signedThumbnailUrl && lastUploadedId) {
          console.log(`Found signed thumbnail URL for video ${lastUploadedId}:`, signedThumbnailUrl);
        }

        // Log API endpoints we're using
        console.log('Fetching data from API endpoints:');
        console.log('- Videos endpoint: /api/videos/');
        console.log('- Analysis endpoint: /api/analysis/');

        // First get all video details
        const videosResponse = await api.get('/api/videos/');
        console.log('Raw videos response:', videosResponse);
        const videos = videosResponse.data;
        console.log('Videos data:', videos);

        // Process videos to get signed URLs for all thumbnails
        if (videos && videos.length > 0) {
          for (const video of videos) {
            // If this is the video that was just uploaded, use the signed URL we got from the upload process
            if (lastUploadedId && video.Video_id.toString() === lastUploadedId.toString() && signedThumbnailUrl) {
              console.log(`Using provided signed URL for video ${video.Video_id}`);
              video.thumbnail_url = signedThumbnailUrl;
              continue;
            }

            // Otherwise, get a signed URL from the backend
            if (video.thumbnail_url) {
              const s3Key = getS3KeyFromUrl(video.thumbnail_url);
              if (s3Key) {
                const signedUrl = await getSignedUrl(s3Key);
                if (signedUrl) {
                  console.log(`Replacing thumbnail URL for video ${video.Video_id} with signed URL`);
                  video.thumbnail_url = signedUrl;
                }
              }
            }
          }

          console.log('First video thumbnail URL (after signing):', videos[0].thumbnail_url);
        }

        // Then get all analyses
        const analysisResponse = await api.get('/api/analysis/');
        console.log('Raw analysis response:', analysisResponse);
        const analysisData = analysisResponse.data;
        console.log('Analysis data sample:', analysisData.length > 0 ? analysisData[0] : 'No analyses found');

        if (videosResponse.status === 200 && analysisResponse.status === 200) {
          // Map videos by ID for easier lookup
          const videoMap: Record<number, any> = {};
          videos.forEach((video: any) => {
            videoMap[video.Video_id] = video;

            // If we have a direct URL for this video, replace the thumbnail URL
            if (lastUploadedId && video.Video_id.toString() === lastUploadedId.toString() && signedThumbnailUrl) {
              console.log(`Overriding thumbnail URL for video ${video.Video_id} with direct S3 URL`);
              video.thumbnail_url = signedThumbnailUrl;
            }
          });
          console.log('Video map with potential overrides:', videoMap);

          // Map analyses to their corresponding videos
          const formattedAnalyses = await Promise.all(analysisData.map(async (item: any) => {
            try {
              console.log('Processing analysis item:', item);

              // Parse result_data if it's a string
              let resultData;
              try {
                resultData = typeof item.result_data === 'string'
                  ? JSON.parse(item.result_data)
                  : item.result_data;
              } catch (e) {
                console.error('Error parsing result_data:', e);
                resultData = { is_fake: false, confidence: 0 };
              }
              console.log('Parsed result data:', resultData);

              // Find video ID either from the result_data or from the video URL if available
              let videoId = null;
              if (resultData && resultData.video_id) {
                videoId = resultData.video_id;
                console.log(`Found video_id ${videoId} in result_data`);
              } else if (item.video) {
                // Try to extract video ID from the video URL if present
                const videoUrlMatch = item.video.match(/\/(\d+)\/$/);
                if (videoUrlMatch && videoUrlMatch[1]) {
                  videoId = parseInt(videoUrlMatch[1]);
                  console.log(`Extracted video_id ${videoId} from video URL`);
                }
              }

              // Get the video by ID
              const video = videoId ? videoMap[videoId] : null;
              console.log(`Video lookup for ID ${videoId}:`, video ? 'Found' : 'Not found');

              // If video not found through ID mapping, try to find by comparing URLs
              let fallbackVideo = null;
              if (!video && item.video) {
                fallbackVideo = videos.find((v: any) => v.video_url === item.video);
                console.log('Fallback video search by URL:', fallbackVideo ? 'Found' : 'Not found');
              }

              const matchedVideo = video || fallbackVideo;
              console.log('Final matched video:', matchedVideo);

              // Direct S3 URL construction if we know the video ID but don't have a thumbnail
              let thumbnailUrl = matchedVideo?.thumbnail_url || null;
              if (videoId && !thumbnailUrl) {
                // Try both regular thumbnail and placeholder URLs
                const directThumbKey = `media/thumbnails/thumbnail_${videoId}.jpg`;
                const placeholderKey = `media/thumbnails/placeholder_${videoId}.jpg`;

                // First try the regular thumbnail
                let signedUrl = await getSignedUrl(directThumbKey);
                if (!signedUrl) {
                  // If that fails, try the placeholder
                  signedUrl = await getSignedUrl(placeholderKey);
                }

                if (signedUrl) {
                  thumbnailUrl = signedUrl;
                  console.log('Using signed URL for constructed path:', thumbnailUrl);
                }

                // If this is the last uploaded video and we have a stored URL, use that
                if (!signedUrl && lastUploadedId && videoId.toString() === lastUploadedId.toString() && signedThumbnailUrl) {
                  thumbnailUrl = signedThumbnailUrl;
                  console.log('Using stored direct S3 URL:', thumbnailUrl);
                }
              }

              return {
                id: item.id.toString(),
                confidence: `${(resultData?.confidence || 0).toFixed(1)}%`,
                duration: matchedVideo ? `${Math.floor(matchedVideo.Length / 60)}:${(matchedVideo.Length % 60).toString().padStart(2, '0')}` : "00:00",
                resolution: matchedVideo ? matchedVideo.Resolution : "Unknown",
                fps: matchedVideo ? `${matchedVideo.Frame_per_Second} fps` : "Unknown",
                created_at: item.created_at,
                result: resultData || { is_fake: false, confidence: 0 },
                thumbnail_url: thumbnailUrl,
                video_url: matchedVideo ? matchedVideo.video_url : null
              };
            } catch (e) {
              console.error('Error processing analysis item:', e);
              return {
                id: item.id?.toString() || 'unknown',
                confidence: '0%',
                duration: '00:00',
                resolution: 'Unknown',
                fps: 'Unknown',
                created_at: item.created_at || new Date().toISOString(),
                result: { is_fake: false, confidence: 0 },
                thumbnail_url: null,
                video_url: null
              };
            }
          }));

          console.log('Final formatted analyses:', formattedAnalyses);
          setAnalyses(formattedAnalyses);

          // Select the first result if available
          if (formattedAnalyses.length > 0) {
            const firstAnalysis = formattedAnalyses[0];
            setSelectedResult(firstAnalysis.id);

            if (firstAnalysis.thumbnail_url) {
              setSelectedImage(firstAnalysis.thumbnail_url);
            } else {
              const videoId = firstAnalysis.result?.video_id;
              if (videoId) {
                const placeholderKey = `media/thumbnails/placeholder_${videoId}.jpg`;
                const signedUrl = await getSignedUrl(placeholderKey);
                if (signedUrl) {
                  setSelectedImage(signedUrl);
                } else {
                  setSelectedImage('https://placehold.co/600x400?text=No+Thumbnail');
                }
              } else {
                setSelectedImage('https://placehold.co/600x400?text=No+Thumbnail');
              }
            }
          }
        }
      } catch (error) {
        console.error("Error fetching analyses:", error);
        setError("Failed to load your analyses. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalyses();
  }, [navigate, locationState]);

  // Memoize the selected analysis
  const selectedAnalysis = useMemo(() => {
    return analyses.find(a => a.id === selectedResult);
  }, [analyses, selectedResult]);

  // Update handleResultClick to set loading state immediately
  const handleResultClick = async (id: string) => {
    setSelectedResult(id);
    setIsImageLoading(true); // Show spinner immediately
    const analysis = analyses.find(a => a.id === id);
    setShowDetection(false);

    if (analysis?.thumbnail_url) {
      const s3Key = getS3KeyFromUrl(analysis.thumbnail_url);
      if (s3Key) {
        const objectCheck = await checkS3ObjectExists(s3Key);
        if (objectCheck.exists || objectCheck.alternateKey) {
          if (objectCheck.signedUrl) {
            const proxyUrl = formatUrl(API_BASE_URL, `proxy-image/?url=${encodeURIComponent(objectCheck.signedUrl)}`);
            setSelectedImage(proxyUrl);
            return;
          }
        }
      }
      setSelectedImage(analysis.thumbnail_url);
    } else {
      const videoId = analysis?.result?.video_id;
      if (videoId) {
        const placeholderKey = `media/thumbnails/placeholder_${videoId}.jpg`;
        const objectCheck = await checkS3ObjectExists(placeholderKey);
        if (objectCheck.exists || objectCheck.alternateKey) {
          const finalKey = objectCheck.alternateKey || placeholderKey;
          const signedUrl = objectCheck.signedUrl || await getSignedUrl(finalKey);
          if (signedUrl) {
            const proxyUrl = formatUrl(API_BASE_URL, `proxy-image/?url=${encodeURIComponent(signedUrl)}`);
            setSelectedImage(proxyUrl);
            return;
          }
        }
        setSelectedImage('https://placehold.co/600x400?text=No+Thumbnail');
      } else {
        setSelectedImage('https://placehold.co/600x400?text=No+Thumbnail');
      }
    }
  };

  // Add direct image loading function that bypasses the proxy
  const loadImageDirectly = async (url: string, imgElement: HTMLImageElement): Promise<boolean> => {
    return new Promise((resolve) => {
      // Create a temporary image to test loading
      const tempImg = new Image();

      // Set up event handlers
      tempImg.onload = () => {
        // Image loaded successfully, set it on the actual element
        imgElement.src = url;
        resolve(true);
      };

      tempImg.onerror = () => {
        // Failed to load
        resolve(false);
      };

      // Set a timeout to avoid hanging
      setTimeout(() => resolve(false), 5000);

      // Try to load the image
      tempImg.src = url;
    });
  };

  // Handle delete
  const handleDelete = async (id: string) => {
    setSelectedResult(id);
    setIsDeleteDialogOpen(true);
  };

  // Confirm delete
  const confirmDelete = async () => {
    if (!selectedResult) return;

    try {
      await api.delete(`/api/analysis/${selectedResult}/`);
      setAnalyses(analyses.filter((analysis: Analysis) => analysis.id !== selectedResult));

      if (analyses.length > 1) {
        const newSelectedId = analyses.find((a: Analysis) => a.id !== selectedResult)?.id || null;
        setSelectedResult(newSelectedId);
        const newAnalysis = analyses.find((a: Analysis) => a.id === newSelectedId);
        setSelectedImage(newAnalysis?.thumbnail_url || null);
      } else {
        setSelectedResult(null);
        setSelectedImage(null);
      }

      setIsDeleteDialogOpen(false);
    } catch (error) {
      console.error("Error deleting analysis:", error);
    }
  };

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    navigate('/login');
  };

  // Add effect to handle new analysis selection
  useEffect(() => {
    const handleNewAnalysis = async () => {
      // Check if we're returning from Detection (showDetection is false) and have analyses
      if (!showDetection && analyses.length > 0) {
        // Get the most recent analysis (first in the list since they're ordered by date)
        const latestAnalysis = analyses[0];

        // Set the selected result
        setSelectedResult(latestAnalysis.id);
        setIsImageLoading(true);

        // Try to set the thumbnail
        if (latestAnalysis.thumbnail_url) {
          const s3Key = getS3KeyFromUrl(latestAnalysis.thumbnail_url);
          if (s3Key) {
            const objectCheck = await checkS3ObjectExists(s3Key);
            if (objectCheck.exists || objectCheck.alternateKey) {
              if (objectCheck.signedUrl) {
                const proxyUrl = formatUrl(API_BASE_URL, `proxy-image/?url=${encodeURIComponent(objectCheck.signedUrl)}`);
                setSelectedImage(proxyUrl);
                return;
              }
            }
          }
          setSelectedImage(latestAnalysis.thumbnail_url);
        } else if (latestAnalysis.result?.video_id) {
          const placeholderKey = `media/thumbnails/placeholder_${latestAnalysis.result.video_id}.jpg`;
          const objectCheck = await checkS3ObjectExists(placeholderKey);
          if (objectCheck.exists || objectCheck.alternateKey) {
            const finalKey = objectCheck.alternateKey || placeholderKey;
            const signedUrl = objectCheck.signedUrl || await getSignedUrl(finalKey);
            if (signedUrl) {
              const proxyUrl = formatUrl(API_BASE_URL, `proxy-image/?url=${encodeURIComponent(signedUrl)}`);
              setSelectedImage(proxyUrl);
              return;
            }
          }
          setSelectedImage('https://placehold.co/600x400?text=No+Thumbnail');
        }
      }
    };

    handleNewAnalysis();
  }, [analyses, showDetection]); // Depend on analyses and showDetection

  return (
    <div className={`dashboard-container ${!isDarkMode ? 'light' : ''}`}>
      <div className="green-circle-container">
        <GreenCircle />
      </div>

      <button
        className={`menu-toggle ${!isDarkMode ? 'light' : ''}`}
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
      >
        {isSidebarOpen ? <XIcon className="h-5 w-5" /> : <MenuIcon className="h-5 w-5" />}
      </button>

      <aside className={`sidebar ${!isDarkMode ? 'light' : ''} ${isSidebarOpen ? 'open' : ''}`}>
        <div className="header-card">
          <div className="header-content">
            <img src={logo} alt="True Vision Logo" className="logo" />
            <span className={`dashboard-title ${!isDarkMode ? 'light' : ''}`}>
              My Dashboard
            </span>
          </div>
        </div>

        <div className="results-container">
          <div className="results-list">
            {isLoading ? (
              <p className={`loading-text ${!isDarkMode ? 'light' : ''}`}>Loading your analyses...</p>
            ) : error ? (
              <p className="error-text">{error}</p>
            ) : analyses.length === 0 ? (
              <p className={`empty-text ${!isDarkMode ? 'light' : ''}`}>No analyses found. Start a new detection.</p>
            ) : (
              <div className="results-list">
                {analyses.map((item) => (
                  <div key={item.id} className="result-item">
                    <div
                      className={`result-card ${!isDarkMode ? 'light' : ''} ${selectedResult === item.id ? 'selected' : ''}`}
                      onClick={() => handleResultClick(item.id)}
                    >
                      <div className="result-content">
                        <div className="result-info">
                          <div className={`status-dot ${item.result?.is_fake ? 'fake' : 'real'}`} />
                          <span className={`result-id ${!isDarkMode ? 'light' : ''}`}>Result #{item.id}</span>
                        </div>
                        <span className="result-date">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <button
                      className={`delete-button ${!isDarkMode ? 'light' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(item.id);
                      }}
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="bottom-actions">
          <button
            className="new-detection-button"
            onClick={() => {
              setShowDetection(true);
              setSelectedResult(null);
              setSelectedImage(null);
              setIsSidebarOpen(false);
            }}
          >
            <PlusIcon className="h-5 w-5" />
            Start a new detection
          </button>

          <div className={`separator ${!isDarkMode ? 'light' : ''}`} />

          <button
            className={`action-button ${!isDarkMode ? 'light' : ''}`}
            onClick={() => {
              if (analyses.length === 0) {
                setIsNoResultsDialogOpen(true);
              } else {
                setIsClearAllDialogOpen(true);
              }
            }}
          >
            <TrashIcon className="h-5 w-5" />
            Clear all results
          </button>

          <button
            className={`action-button ${!isDarkMode ? 'light' : ''}`}
            onClick={toggleTheme}
          >
            {isDarkMode ? (
              <>
                <SunIcon className="h-5 w-5" />
                Switch to Light Mode
              </>
            ) : (
              <>
                <MoonIcon className="h-5 w-5" />
                Switch to Dark Mode
              </>
            )}
          </button>

          <button
            className="logout-button"
            onClick={handleLogout}
          >
            <LogOutIcon className="h-5 w-5" />
            Log out
          </button>
        </div>
      </aside>

      {showDetection ? (
        <Detection onAnalysisComplete={() => {
          setShowDetection(false);
          // Fetch latest analyses to ensure we have the new one
          const fetchLatestAnalyses = async () => {
            try {
              const analysisResponse = await api.get('/api/analysis/');
              if (analysisResponse.status === 200) {
                const newAnalyses = analysisResponse.data.map((item: any) => ({
                  id: item.id.toString(),
                  confidence: `${(item.result_data?.confidence || 0).toFixed(1)}%`,
                  duration: "00:00", // This will be updated when video data is fetched
                  created_at: item.created_at,
                  result: item.result_data || { is_fake: false, confidence: 0 },
                  thumbnail_url: null,
                  video_url: null
                }));
                setAnalyses(newAnalyses);
              }
            } catch (error) {
              console.error("Error fetching latest analyses:", error);
            }
          };
          fetchLatestAnalyses();
        }} />
      ) : (
        <div className="main-content">
          <div className="content-wrapper">
            <h1 className={`content-title ${!isDarkMode ? 'light' : ''}`}>Result details</h1>

            {selectedResult ? (
              <div className="space-y-6">
                <div className="preview-container">
                  <div className="aspect-video bg-black rounded-lg overflow-hidden relative w-full h-full">
                    <div className="relative w-full h-full">
                      {selectedImage && (
                        <img
                          key={selectedImage}
                          src={selectedImage}
                          alt=""
                          className="w-full h-full object-contain"
                          style={{
                            opacity: isImageLoading ? 0 : 1,
                            transition: 'opacity 0.2s ease-in-out'
                          }}
                          onLoad={(e) => {
                            try {
                              const img = e.currentTarget as HTMLImageElement;
                              const canvas = document.createElement('canvas');
                              canvas.width = Math.min(img.naturalWidth, 50);
                              canvas.height = Math.min(img.naturalHeight, 50);
                              const ctx = canvas.getContext('2d');
                              if (ctx) {
                                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                                const data = imageData.data;
                                let totalBrightness = 0;
                                for (let i = 0; i < data.length; i += 4) {
                                  const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
                                  totalBrightness += brightness;
                                }
                                const avgBrightness = totalBrightness / (data.length / 4);
                                if (avgBrightness < 20) {
                                  let greenPixels = 0;
                                  for (let i = 0; i < data.length; i += 4) {
                                    if (data[i] < 100 && data[i + 1] > 100 && data[i + 2] < 100) {
                                      greenPixels++;
                                    }
                                  }
                                  const greenPercentage = greenPixels / (data.length / 4) * 100;
                                  if (greenPercentage < 30) {
                                    img.src = 'https://placehold.co/600x400?text=No+Visible+Thumbnail';
                                    return;
                                  }
                                }
                                setIsImageLoading(false);
                              }
                            } catch (err) {
                              setIsImageLoading(false);
                            }
                          }}
                          onError={async (e) => {
                            try {
                              const imgElement = e.currentTarget as HTMLImageElement;
                              if (!imgElement) return;

                              // Try to get a working URL
                              const currentAnalysis = analyses.find((a: Analysis) => a.id === selectedResult);
                              let videoId = currentAnalysis?.result?.video_id;

                              if (!videoId && selectedImage) {
                                const match = selectedImage.match(/(?:thumbnail|placeholder)_(\d+)\.jpg/);
                                if (match && match[1]) {
                                  videoId = parseInt(match[1], 10);
                                }
                              }

                              if (videoId) {
                                const pathsToTry = [
                                  `media/thumbnails/thumbnail_${videoId}.jpg`,
                                  `media/thumbnails/placeholder_${videoId}.jpg`,
                                  `media/videos/thumbnail_${videoId}.jpg`
                                ];

                                for (const path of pathsToTry) {
                                  const signedUrl = await getSignedUrl(path);
                                  if (signedUrl) {
                                    const isProxyAvailable = await checkEndpointAvailability('/proxy-image/');
                                    if (isProxyAvailable) {
                                      const proxyUrl = formatUrl(API_BASE_URL, `proxy-image/?url=${encodeURIComponent(signedUrl)}`);
                                      imgElement.src = proxyUrl;
                                      return;
                                    }
                                    imgElement.src = signedUrl;
                                    return;
                                  }
                                }
                              }
                              imgElement.src = 'https://placehold.co/600x400?text=No+Thumbnail';
                            } catch (error) {
                              console.error('Error in image error handler:', error);
                            } finally {
                              setIsImageLoading(false);
                            }
                          }}
                        />
                      )}
                      {isImageLoading && (
                        <div className="loading-overlay">
                          <div className="loading-spinner" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="content-details">
                  <div className={`details-table ${!isDarkMode ? 'light' : ''}`}>
                    <table className="w-full">
                      <thead>
                        <tr>
                          <th>Model Result</th>
                          <th>Confidence Score</th>
                          <th>Duration</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedAnalysis && (
                          <tr>
                            <td style={{ color: selectedAnalysis.result?.is_fake ? '#ef4444' : '#22c55e', textAlign: 'center' }}>
                              {selectedAnalysis.result?.is_fake ? 'Fake' : 'Real'}
                            </td>
                            <td className="confidence text-center">
                              {selectedAnalysis.confidence}
                            </td>
                            <td className="text-center">
                              {selectedAnalysis.duration}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)]">
                <p className={`${isDarkMode ? 'text-neutral-400' : 'text-gray-500'} mb-4`}>
                  Select a result to view details
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {isDeleteDialogOpen && selectedResult && (
        <Dialog open={isDeleteDialogOpen} onOpenChange={() => setIsDeleteDialogOpen(false)}>
          <DialogContent className={`${isDarkMode ? 'dark bg-neutral-900 text-white' : 'light bg-white text-gray-900'}`}>
            <DialogHeader>
              <DialogTitle className={isDarkMode ? 'text-white' : 'text-gray-900'}>Confirm Deletion</DialogTitle>
              <DialogDescription className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>
                Are you sure you want to delete Result#{selectedResult}? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant={isDarkMode ? "outline" : "secondary"} onClick={() => setIsDeleteDialogOpen(false)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={confirmDelete}>
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      <Dialog open={isClearAllDialogOpen} onOpenChange={() => setIsClearAllDialogOpen(false)}>
        <DialogContent className={`${isDarkMode ? 'dark bg-neutral-900 text-white' : 'light bg-white text-gray-900'}`}>
          <DialogHeader>
            <DialogTitle className={isDarkMode ? 'text-white' : 'text-gray-900'}>Clear All Results</DialogTitle>
            <DialogDescription className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>
              Are you sure you want to clear all results? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant={isDarkMode ? "outline" : "secondary"} onClick={() => setIsClearAllDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={async () => {
                try {
                  // Delete each analysis one by one
                  for (const analysis of analyses) {
                    await api.delete(`/api/analysis/${analysis.id}/`);
                  }

                  // Clear the state
                  setAnalyses([]);
                  setSelectedResult(null);
                  setSelectedImage(null);
                  setShowDetection(false);
                  setIsClearAllDialogOpen(false);
                } catch (error) {
                  console.error("Error clearing analyses:", error);
                  setError("Failed to clear analyses. Please try again.");
                }
              }}
            >
              Clear All
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isNoResultsDialogOpen} onOpenChange={() => setIsNoResultsDialogOpen(false)}>
        <DialogContent className={`${isDarkMode ? 'dark bg-neutral-900 text-white' : 'light bg-white text-gray-900'}`}>
          <DialogHeader>
            <DialogTitle className={isDarkMode ? 'text-white' : 'text-gray-900'}>No Results</DialogTitle>
            <DialogDescription className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>
              You don't have any results to clear. Start a new detection to analyze your first video.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant={isDarkMode ? "outline" : "secondary"} onClick={() => setIsNoResultsDialogOpen(false)}>
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Dashboard;