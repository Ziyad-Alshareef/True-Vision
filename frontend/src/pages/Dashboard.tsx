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
import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Separator } from "../components/ui/separator";
import { Detection } from "./Detection";
import api from "../api";
import logo from "./assets/logo-transpa.png";
import { GreenCircle } from '../components/GreenCircle';
import { useTheme } from '../context/ThemeContext';
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

export const Dashboard = (): JSX.Element => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isDarkMode, toggleTheme } = useTheme();
  const [selectedResult, setSelectedResult] = useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [showDetection, setShowDetection] = useState(false);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Update getS3KeyFromUrl to be more forgiving
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

  // Fix the getSignedUrl function to work with the Heroku deployment
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

  // Fetch user's analyses
  useEffect(() => {
    // Create an async function inside the effect
    const fetchAnalyses = async () => {
      try {
        const token = localStorage.getItem('access');
        if (!token) {
          navigate('/login');
          return;
        }

        setIsLoading(true);

        // Check if we have a signed thumbnail URL from the upload
        const signedThumbnailUrl = location.state?.signedThumbnailUrl ||
          localStorage.getItem('last_signed_thumbnail_url') ||
          localStorage.getItem('last_api_signed_url');

        const lastUploadedId = location.state?.lastUploadedVideoId ||
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
              console.log('Setting thumbnail URL:', firstAnalysis.thumbnail_url);
              setSelectedImage(firstAnalysis.thumbnail_url);
            } else {
              console.log('No thumbnail URL available for first analysis');
              // Try using a direct placeholder based on video ID
              const videoId = firstAnalysis.result?.video_id;
              if (videoId) {
                const placeholderKey = `media/thumbnails/placeholder_${videoId}.jpg`;
                const signedUrl = await getSignedUrl(placeholderKey);
                if (signedUrl) {
                  console.log('Using signed URL for placeholder:', signedUrl);
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

    // Call the async function
    fetchAnalyses();
  }, [navigate, location.state]);

  // Update handleResultClick to use checkS3ObjectExists
  const handleResultClick = async (id: string) => {
    console.log('Clicked result:', id);
    const analysis = analyses.find(a => a.id === id);
    console.log('Found analysis:', analysis);
    setSelectedResult(id);

    if (analysis?.thumbnail_url) {
      const s3Key = getS3KeyFromUrl(analysis.thumbnail_url);

      if (s3Key) {
        // Check if the object exists first
        const objectCheck = await checkS3ObjectExists(s3Key);

        if (objectCheck.exists || objectCheck.alternateKey) {
          // Use the provided signed URL directly through our proxy
          if (objectCheck.signedUrl) {
            const proxyUrl = formatUrl(API_BASE_URL, `proxy-image/?url=${encodeURIComponent(objectCheck.signedUrl)}`);
            console.log('Using pre-verified proxy URL:', proxyUrl);
            setSelectedImage(proxyUrl);
            setShowDetection(false);
            return;
          }
        }
      }

      // Fallback to original behavior if object check fails
      setSelectedImage(analysis.thumbnail_url);
    } else {
      // Try using a direct placeholder based on video ID
      const videoId = analysis?.result?.video_id;
      if (videoId) {
        // Check if placeholder exists first
        const placeholderKey = `media/thumbnails/placeholder_${videoId}.jpg`;
        const objectCheck = await checkS3ObjectExists(placeholderKey);

        if (objectCheck.exists || objectCheck.alternateKey) {
          const finalKey = objectCheck.alternateKey || placeholderKey;
          const signedUrl = objectCheck.signedUrl || await getSignedUrl(finalKey);

          if (signedUrl) {
            const proxyUrl = formatUrl(API_BASE_URL, `proxy-image/?url=${encodeURIComponent(signedUrl)}`);
            console.log('Using verified placeholder URL through proxy:', proxyUrl);
            setSelectedImage(proxyUrl);
            setShowDetection(false);
            return;
          }
        }

        // If not found, fall back to placeholder
        setSelectedImage('https://placehold.co/600x400?text=No+Thumbnail');
      } else {
        setSelectedImage('https://placehold.co/600x400?text=No+Thumbnail');
      }
    }

    setShowDetection(false);
  };

  const handleDelete = async (id: string) => {
    setSelectedResult(id);
    setIsDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!selectedResult) return;

    try {
      await api.delete(`/api/analysis/${selectedResult}/`);

      // Remove the deleted analysis from state
      setAnalyses(analyses.filter(analysis => analysis.id !== selectedResult));

      // Select the first remaining analysis or clear selection
      if (analyses.length > 1) {
        const newSelectedId = analyses.find(a => a.id !== selectedResult)?.id || null;
        setSelectedResult(newSelectedId);
        const newAnalysis = analyses.find(a => a.id === newSelectedId);
        setSelectedImage(newAnalysis?.thumbnail_url || null);
      } else {
        setSelectedResult(null);
        setSelectedImage(null);
      }

      setIsDeleteDialogOpen(false);
    } catch (error) {
      console.error("Error deleting analysis:", error);
      // Show error message to user
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    navigate('/login');
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

  // Load an image with a signed URL
  const loadImageWithSignedUrl = async (imageUrl: string): Promise<string> => {
    // If it's not an S3 URL, return as is
    if (!imageUrl.includes('amazonaws') && !imageUrl.includes('/media/')) {
      return imageUrl;
    }

    const s3Key = getS3KeyFromUrl(imageUrl);
    if (!s3Key) {
      console.warn('Could not extract S3 key from URL:', imageUrl);
      return imageUrl;
    }

    console.log('Extracting S3 key:', s3Key);
    const signedUrl = await getSignedUrl(s3Key);
    if (!signedUrl) {
      console.warn('Could not get signed URL for:', s3Key);
      return imageUrl;
    }

    return signedUrl;
  };

  // Add a new function to verify image URLs
  const verifyImageUrl = async (url: string): Promise<boolean> => {
    try {
      // Use fetch with HEAD method to check if image exists
      const response = await fetch(url, {
        method: 'HEAD',
        mode: 'no-cors' // Important for cross-origin requests
      });
      return true; // If we get here, the image probably exists
    } catch (error) {
      console.error('Error verifying image URL:', error);
      return false;
    }
  };

  return (
    <div className={`flex min-h-screen w-full ${isDarkMode ? 'bg-[#222222]' : 'bg-gray-50'}`}>
      <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2" style={{ zIndex: 0 }}>
        <GreenCircle />
      </div>

      {/* Mobile Menu Toggle Button */}
      <Button
        className={`fixed top-4 left-4 z-[100] block lg:hidden ${isDarkMode ? 'bg-[#333333] text-white' : 'bg-white text-gray-800'}`}
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
      >
        {isSidebarOpen ? <XIcon className="h-5 w-5" /> : <MenuIcon className="h-5 w-5" />}
      </Button>

      {/* Sidebar */}
      <aside
        className={`fixed lg:static w-[300px] min-h-screen ${isDarkMode ? 'bg-[#222222] text-neutral-200' : 'bg-white text-gray-800'} p-4 flex flex-col border-r border-solid ${isDarkMode ? 'border-[#ffffff26]' : 'border-gray-200'} transition-transform duration-300 ease-in-out z-50 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
      >
        <div className="flex flex-col h-full">
          {/* User Profile */}
          <div className="mb-6">
            <Card className={`${isDarkMode ? 'bg-[#ffffff0d]' : 'bg-gray-50'} border-none`}>
              <CardContent className="flex items-center gap-3 p-3">
                <img
                  src={logo}
                  alt="True Vision Logo"
                  className="h-[40px] w-auto"
                />
                <span className={`${isDarkMode ? 'text-neutral-200' : 'text-gray-800'} font-medium`}>My Dashboard</span>
              </CardContent>
            </Card>
          </div>

          {/* Results List */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <p className={`${isDarkMode ? 'text-neutral-400' : 'text-gray-500'} text-center py-4`}>Loading your analyses...</p>
            ) : error ? (
              <p className="text-red-400 text-center py-4">{error}</p>
            ) : analyses.length === 0 ? (
              <p className={`${isDarkMode ? 'text-neutral-400' : 'text-gray-500'} text-center py-4`}>No analyses found. Start a new detection.</p>
            ) : (
              analyses.map((item) => (
                <div key={item.id} className="mb-2 flex">
                  <Card
                    className={`flex-grow ${isDarkMode ? 'bg-[#ffffff0d]' : 'bg-gray-50'} border-none cursor-pointer ${selectedResult === item.id ? 'ring-2 ring-[#097F4D]' : ''
                      }`}
                    onClick={() => {
                      handleResultClick(item.id);
                      setIsSidebarOpen(false);
                    }}
                  >
                    <CardContent className="flex items-center p-3">
                      <span className={`${isDarkMode ? 'text-neutral-200' : 'text-gray-800'}`}>Result#{item.id}</span>
                    </CardContent>
                  </Card>
                  <Button
                    variant="ghost"
                    className={`ml-2 ${isDarkMode ? 'text-neutral-200' : 'text-gray-800'} hover:text-red-500`}
                    onClick={() => handleDelete(item.id)}
                  >
                    <TrashIcon className="h-5 w-5" />
                  </Button>
                </div>
              ))
            )}
          </div>

          {/* New Detection Button */}
          <Button
            className="w-full bg-[#097F4D] hover:bg-[#076b41] text-white mb-6"
            onClick={() => {
              setShowDetection(true);
              setIsSidebarOpen(false);
            }}
          >
            <PlusIcon className="mr-2 h-5 w-5" />
            Start a new detection
          </Button>

          {/* Bottom Actions */}
          <div className="mt-auto">
            <Separator className={`my-4 ${isDarkMode ? 'bg-[#ffffff26]' : 'bg-gray-200'}`} />
            <Button
              variant="ghost"
              className={`w-full justify-start ${isDarkMode ? 'text-neutral-200' : 'text-gray-800'} mb-2`}
              onClick={async () => {
                try {
                  await api.delete('/api/analysis/clear/');
                  setAnalyses([]);
                  setSelectedResult(null);
                  setSelectedImage(null);
                } catch (error) {
                  console.error("Error clearing analyses:", error);
                }
              }}
            >
              <TrashIcon className="mr-2 h-5 w-5" />
              Clear all results
            </Button>
            <Button
              variant="ghost"
              className={`w-full justify-start ${isDarkMode ? 'text-neutral-200' : 'text-gray-800'} mb-2`}
              onClick={toggleTheme}
            >
              {isDarkMode ? (
                <>
                  <SunIcon className="mr-2 h-5 w-5" />
                  Switch to Light Mode
                </>
              ) : (
                <>
                  <MoonIcon className="mr-2 h-5 w-5" />
                  Switch to Dark Mode
                </>
              )}
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start text-red-500"
              onClick={handleLogout}
            >
              <LogOutIcon className="mr-2 h-5 w-5" />
              Log out
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      {showDetection ? (
        <Detection />
      ) : (
        <div className="flex-1 min-h-screen">
          <main className={`w-full ${isDarkMode ? 'bg-[#222222]' : 'bg-gray-50'} p-6`}>
            <div className="max-w-6xl mx-auto">
              <h1 className={`text-2xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-800'} mb-6`}>Result details</h1>

              {selectedResult ? (
                <div className="space-y-6">
                  <div className="aspect-video bg-black rounded-lg overflow-hidden">
                    {selectedImage ? (
                      <img
                        src={selectedImage}
                        alt="Result preview"
                        className="w-full h-full object-contain"
                        onError={async (e) => {
                          try {
                            console.error('Error loading image:', selectedImage);
                            const imgElement = e.currentTarget as HTMLImageElement;
                            if (!imgElement) {
                              console.error('Image element is null, cannot update src');
                              return;
                            }

                            // Check if this is a CORS error or 404
                            const isCorsOrMissingFile = selectedImage?.includes('amazonaws.com') || false;

                            if (isCorsOrMissingFile) {
                              console.log('Likely S3 issue with image, trying alternative approaches');

                              // Extract video ID from the URL if possible
                              let videoId = null;
                              const currentAnalysis = analyses.find(a => a.id === selectedResult);
                              if (currentAnalysis?.result?.video_id) {
                                videoId = currentAnalysis.result.video_id;
                              } else if (selectedImage) {
                                // Try to extract from thumbnail URL
                                const match = selectedImage.match(/(?:thumbnail|placeholder)_(\d+)\.jpg/);
                                if (match && match[1]) {
                                  videoId = match[1];
                                }
                              }

                              // If we have a video ID, try different fallback approaches
                              if (videoId) {
                                console.log('Found video ID:', videoId);

                                // Array of possible paths to try
                                const pathsToTry = [
                                  `media/thumbnails/placeholder_${videoId}.jpg`,
                                  `media/thumbnails/thumbnail_${videoId}.jpg`,
                                  `media/videos/thumbnail_${videoId}.jpg`
                                ];

                                // Check if proxy endpoint is available
                                const isProxyAvailable = await checkEndpointAvailability('/proxy-image/');

                                // Try each path in sequence
                                for (const path of pathsToTry) {
                                  // Get signed URL for the path
                                  const signedUrl = await getSignedUrl(path);

                                  if (signedUrl) {
                                    if (isProxyAvailable) {
                                      // Use proxy if available
                                      const proxyUrl = formatUrl(API_BASE_URL, `proxy-image/?url=${encodeURIComponent(signedUrl)}`);
                                      console.log(`Trying proxy URL for ${path}:`, proxyUrl);

                                      // Try proxy URL first
                                      const proxySuccess = await loadImageDirectly(proxyUrl, imgElement);
                                      if (proxySuccess) {
                                        console.log('Proxy loading succeeded');
                                        return;
                                      }
                                    }

                                    // If proxy failed or isn't available, try direct URL
                                    console.log(`Trying direct signed URL for ${path}:`, signedUrl);
                                    const directSuccess = await loadImageDirectly(signedUrl, imgElement);
                                    if (directSuccess) {
                                      console.log('Direct loading succeeded');
                                      return;
                                    }
                                  }
                                }
                              }

                              // If all attempts with paths failed, try a public placeholder service
                              const placeholderUrl = 'https://placehold.co/600x400?text=No+Thumbnail+Found';
                              console.log('Using public placeholder service:', placeholderUrl);
                              imgElement.src = placeholderUrl;
                              return;
                            }

                            // If all else fails, use placeholder
                            console.log('All attempts failed, using placeholder');
                            imgElement.src = 'https://placehold.co/600x400?text=No+Thumbnail+Available';
                          } catch (error) {
                            console.error('Error in image error handler:', error);
                            // Try one last time with a safe fallback
                            try {
                              const imgElement = e.currentTarget as HTMLImageElement;
                              if (imgElement) {
                                imgElement.src = 'https://placehold.co/600x400?text=Error+Loading+Image';
                              }
                            } catch (finalError) {
                              console.error('Even fallback image failed:', finalError);
                            }
                          }
                        }}
                        onLoad={(e) => {
                          // Check if the image might be completely black
                          try {
                            console.log('Thumbnail loaded successfully:', selectedImage);
                            const img = e.currentTarget as HTMLImageElement;

                            // Create a canvas to analyze the image
                            const canvas = document.createElement('canvas');
                            canvas.width = Math.min(img.naturalWidth, 50); // Analyze a small version
                            canvas.height = Math.min(img.naturalHeight, 50);

                            const ctx = canvas.getContext('2d');
                            if (ctx) {
                              ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                              // Get image data
                              const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                              const data = imageData.data;

                              // Check if the image is mostly black
                              let totalBrightness = 0;
                              for (let i = 0; i < data.length; i += 4) {
                                // Calculate brightness (simple average)
                                const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
                                totalBrightness += brightness;
                              }

                              const avgBrightness = totalBrightness / (data.length / 4);
                              console.log('Average brightness:', avgBrightness);

                              // If avg brightness is too low, replace with placeholder
                              if (avgBrightness < 20) {
                                console.log('Thumbnail appears to be too dark, replacing with placeholder');

                                // Check if green placeholder (then don't replace it)
                                let greenPixels = 0;
                                for (let i = 0; i < data.length; i += 4) {
                                  // Check for green color dominance
                                  if (data[i] < 100 && data[i + 1] > 100 && data[i + 2] < 100) {
                                    greenPixels++;
                                  }
                                }

                                const greenPercentage = greenPixels / (data.length / 4) * 100;
                                console.log('Green percentage:', greenPercentage);

                                // If not a green placeholder, replace with one
                                if (greenPercentage < 30) {
                                  img.src = 'https://placehold.co/600x400?text=No+Visible+Thumbnail';
                                } else {
                                  console.log('Detected green placeholder, keeping it');
                                }
                              }
                            }
                          } catch (err) {
                            console.error('Error analyzing image:', err);
                          }
                        }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <p className="text-gray-500">No thumbnail available</p>
                      </div>
                    )}
                  </div>

                  <div className={`${isDarkMode ? 'bg-[#333333]' : 'bg-white'} rounded-lg p-4 shadow-sm`}>
                    <table className="w-full">
                      <thead>
                        <tr>
                          <th className={`text-left p-2 ${isDarkMode ? 'text-neutral-200' : 'text-gray-800'}`}>Model Result</th>
                          <th className={`text-left p-2 ${isDarkMode ? 'text-neutral-200' : 'text-gray-800'}`}>Confidence Score</th>
                          <th className={`text-left p-2 ${isDarkMode ? 'text-neutral-200' : 'text-gray-800'}`}>Video Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className={`p-2 ${isDarkMode ? 'text-neutral-200' : 'text-gray-800'}`}>
                            {analyses.find(item => item.id === selectedResult)?.result?.is_fake ? 'FAKE' : 'REAL'}
                          </td>
                          <td className="p-2 text-red-500">
                            {analyses.find(item => item.id === selectedResult)?.confidence}
                          </td>
                          <td className={`p-2 ${isDarkMode ? 'text-neutral-200' : 'text-gray-800'}`}>
                            {analyses.find(item => item.id === selectedResult)?.duration}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)]">
                  <p className={`${isDarkMode ? 'text-neutral-400' : 'text-gray-500'} mb-4`}>Select a result to view details</p>
                </div>
              )}
            </div>
          </main>
        </div>
      )}

      {isDeleteDialogOpen && selectedResult && (
        <Dialog open={isDeleteDialogOpen} onOpenChange={() => setIsDeleteDialogOpen(false)}>
          <DialogContent className={`${isDarkMode ? 'bg-[#333333] text-white' : 'bg-white text-black'}`}>
            <DialogHeader>
              <DialogTitle>Confirm Deletion</DialogTitle>
              <DialogDescription className={`${isDarkMode ? 'text-neutral-300' : 'text-gray-500'}`}>
                Are you sure you want to delete Result#{selectedResult}? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={confirmDelete}>
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default Dashboard;