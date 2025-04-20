import {
    CpuIcon,
    PlusIcon,
    SunIcon,
    MoonIcon,
    TrashIcon,
    LogOutIcon,
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
  
    // Fetch user's analyses
    useEffect(() => {
      const fetchAnalyses = async () => {
        try {
          const token = localStorage.getItem('access');
          if (!token) {
            navigate('/login');
            return;
          }
          
          setIsLoading(true);
          
          // Log API endpoints we're using
          console.log('Fetching data from API endpoints:');
          console.log('- Videos endpoint: /api/videos/');
          console.log('- Analysis endpoint: /api/analysis/');
          
          // First get all video details
          const videosResponse = await api.get('/api/videos/');
          console.log('Raw videos response:', videosResponse);
          const videos = videosResponse.data;
          console.log('Videos data:', videos);
          
          if (videos && videos.length > 0) {
            console.log('First video thumbnail URL:', videos[0].thumbnail_url);
            console.log('First video URL:', videos[0].video_url);
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
            });
            console.log('Video map:', videoMap);
            
            // Map analyses to their corresponding videos
            const formattedAnalyses = analysisData.map((item: any) => {
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
                
                return {
                  id: item.id.toString(),
                  confidence: `${(resultData?.confidence || 0).toFixed(1)}%`,
                  duration: matchedVideo ? `${Math.floor(matchedVideo.Length / 60)}:${(matchedVideo.Length % 60).toString().padStart(2, '0')}` : "00:00",
                  resolution: matchedVideo ? matchedVideo.Resolution : "Unknown",
                  fps: matchedVideo ? `${matchedVideo.Frame_per_Second} fps` : "Unknown",
                  created_at: item.created_at,
                  result: resultData || { is_fake: false, confidence: 0 },
                  thumbnail_url: matchedVideo ? matchedVideo.thumbnail_url : null,
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
            });
            
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
                setSelectedImage('https://placehold.co/600x400?text=No+Thumbnail');
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
    }, [navigate, location.state]);
  
    const handleResultClick = (id: string) => {
      console.log('Clicked result:', id);
      const analysis = analyses.find(a => a.id === id);
      console.log('Found analysis:', analysis);
      setSelectedResult(id);
      setSelectedImage(analysis?.thumbnail_url || null);
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
  
    return (
      <div className={`flex h-screen w-full ${isDarkMode ? 'bg-neutral-950' : 'bg-gray-100'}`}>
        <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2" style={{ zIndex: 0 }}>
        <GreenCircle />
      </div>
        {/* Sidebar */}
        <aside className={`w-[300px] ${isDarkMode ? 'bg-[#222222] text-neutral-200' : 'bg-white text-gray-800'} p-4 flex flex-col border-r border-solid ${isDarkMode ? 'border-[#ffffff26]' : 'border-gray-200'}`}>
          <div className="flex flex-col flex-grow">
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
            <div className="flex-grow">
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
                      className={`flex-grow ${isDarkMode ? 'bg-[#ffffff0d]' : 'bg-gray-50'} border-none cursor-pointer ${
                        selectedResult === item.id ? 'ring-2 ring-[#097F4D]' : ''
                      }`}
                      onClick={() => handleResultClick(item.id)}
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
              onClick={() => setShowDetection(true)}
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
          <main className={`flex-grow ${isDarkMode ? 'bg-[#222222]' : 'bg-gray-50'} p-6`}>
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
                        onError={(e) => {
                          console.error('Error loading image:', selectedImage);
                          e.currentTarget.src = 'https://placehold.co/600x400?text=No+Thumbnail';
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
                            <div>Duration: {analyses.find(item => item.id === selectedResult)?.duration}</div>
                            <div>Resolution: {analyses.find(item => item.id === selectedResult)?.resolution}</div>
                            <div>Frame Rate: {analyses.find(item => item.id === selectedResult)?.fps}</div>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className={`text-center py-12 ${isDarkMode ? 'text-neutral-400' : 'text-gray-500'}`}>
                  <CpuIcon className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <h2 className="text-xl font-medium mb-2">No result selected</h2>
                  <p>Select a result from the sidebar or start a new detection.</p>
                </div>
              )}
            </div>
          </main>
        )}
  
        {/* Delete Confirmation Dialog */}
        <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <DialogContent className={`${isDarkMode ? 'bg-neutral-900 text-white' : 'bg-white text-gray-800'}`}>
            <DialogHeader>
              <DialogTitle>Delete Analysis</DialogTitle>
              <DialogDescription className={isDarkMode ? 'text-neutral-400' : 'text-gray-500'}>
                Are you sure you want to delete this analysis? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => setIsDeleteDialogOpen(false)}
                className={isDarkMode ? 'border-gray-700 text-white' : ''}
              >
                Cancel
              </Button>
              <Button 
                variant="destructive" 
                onClick={confirmDelete}
              >
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    );
  };

  export default Dashboard;

/*import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from "../api";

interface Analysis {
  id: number;
  result: {
    is_fake: boolean;
    confidence: number;
  };
  created_at: string;
}

const Dashboard: React.FC = () => {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('access');
    if (!token) {
      navigate('/login');
      return;
    }

    fetchAnalyses();
  }, [navigate]);

  const fetchAnalyses = async (): Promise<void> => {
    try {
      const response = await api.get<Analysis[]>('/api/analysis/');
      if (response.status === 200) {
        setAnalyses(response.data);
      }
    } catch (error) {
      console.error('Error fetching analyses:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold mb-6 text-white">Your Analyses</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {analyses.map((analysis) => (
          <div key={analysis.id} className="bg-gray-800 rounded-lg p-4">
            <div className="text-white">
              <p className="font-bold">Result: {analysis.result.is_fake ? 'Fake' : 'Real'}</p>
              <p>Confidence: {analysis.result.confidence}%</p>
              <p>Created: {new Date(analysis.created_at).toLocaleDateString()}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard; */
