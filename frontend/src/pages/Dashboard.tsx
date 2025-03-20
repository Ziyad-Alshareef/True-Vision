import {
    CpuIcon,
    PlusIcon,
    SunIcon,
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
    };
  }
  
  export const Dashboard = (): JSX.Element => {
    const navigate = useNavigate();
    const location = useLocation();
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
          const response = await api.get('/api/analysis/');
          
          if (response.status === 200) {
            // Format the data to match our expected structure
            const formattedAnalyses = response.data.map((item: any) => ({
              id: item.id.toString(),
              confidence: `${(item.result.confidence * 100).toFixed(3)}%`,
              duration: item.duration || "00:00",
              resolution: item.resolution || "Unknown",
              fps: item.fps || "Unknown",
              created_at: item.created_at,
              result: item.result
            }));
            
            setAnalyses(formattedAnalyses);
            
            // Select the first result if available
            if (formattedAnalyses.length > 0) {
              setSelectedResult(formattedAnalyses[0].id);
              setSelectedImage("/sample-image.jpg"); // Replace with actual thumbnail
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
      setSelectedResult(id);
      setSelectedImage("/sample-image.jpg"); // Replace with actual image handling
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
      <div className="flex h-screen bg-neutral-950">
        <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2" style={{ zIndex: 0 }}>
        <GreenCircle />
      </div>
        {/* Sidebar */}
        <aside className="w-[300px] bg-[#222222] p-4 flex flex-col border-r border-solid border-[#ffffff26]">
          <div className="flex flex-col flex-grow">
            {/* User Profile */}
            <div className="mb-6">
              <Card className="bg-[#ffffff0d] border-none">
                <CardContent className="flex items-center gap-3 p-3">
                  <img
                    src={logo}
                    alt="True Vision Logo"
                    className="h-[40px] w-auto"
                  />
                  <span className="text-neutral-200 font-medium">My Dashboard</span>
                </CardContent>
              </Card>
            </div>
  
            {/* Results List */}
            <div className="flex-grow">
              {isLoading ? (
                <p className="text-neutral-400 text-center py-4">Loading your analyses...</p>
              ) : error ? (
                <p className="text-red-400 text-center py-4">{error}</p>
              ) : analyses.length === 0 ? (
                <p className="text-neutral-400 text-center py-4">No analyses found. Start a new detection.</p>
              ) : (
                analyses.map((item) => (
                  <div key={item.id} className="mb-2 flex">
                    <Card 
                      className={`flex-grow bg-[#ffffff0d] border-none cursor-pointer ${
                        selectedResult === item.id ? 'ring-2 ring-[#097F4D]' : ''
                      }`}
                      onClick={() => handleResultClick(item.id)}
                    >
                      <CardContent className="flex items-center p-3">
                        <span className="text-neutral-200">Result#{item.id}</span>
                      </CardContent>
                    </Card>
                    <Button
                      variant="ghost"
                      className="ml-2 text-neutral-200 hover:text-red-500"
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
              <Separator className="my-4 bg-[#ffffff26]" />
              <Button 
                variant="ghost" 
                className="w-full justify-start text-neutral-200 mb-2"
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
              <Button variant="ghost" className="w-full justify-start text-neutral-200 mb-2">
                <SunIcon className="mr-2 h-5 w-5" />
                Switch Light Mode
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
          <main className="flex-grow bg-[#222222] p-6">
            <div className="max-w-6xl mx-auto">
              <h1 className="text-2xl font-semibold text-white mb-6">Result details</h1>
              
              {selectedResult && selectedImage ? (
                <div className="space-y-6">
                  <div className="aspect-video bg-black rounded-lg overflow-hidden">
                    <img
                      src={selectedImage}
                      alt="Result preview"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  
                  <div className="bg-[#333333] rounded-lg p-4">
                    <table className="w-full text-neutral-200">
                      <thead>
                        <tr>
                          <th className="text-left p-2">Model Result</th>
                          <th className="text-left p-2">Confidence Score</th>
                          <th className="text-left p-2">Video Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedResult && (
                          <tr>
                            <td className="p-2">
                              {analyses.find(item => item.id === selectedResult)?.result.is_fake ? 'FAKE' : 'REAL'}
                            </td>
                            <td className="p-2 text-red-500">
                              {analyses.find(item => item.id === selectedResult)?.confidence}
                            </td>
                            <td className="p-2">
                              Duration: {analyses.find(item => item.id === selectedResult)?.duration}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : !isLoading && !error && analyses.length > 0 ? (
                <p className="text-neutral-400 text-center py-4">Select a result to view details</p>
              ) : null}
            </div>
          </main>
        )}
  
        {/* Delete Confirmation Dialog */}
        <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <DialogContent className="bg-[#333333] text-white border-none">
            <DialogHeader>
              <DialogTitle>Are you sure?</DialogTitle>
              <DialogDescription className="text-neutral-400">
                This action will Delete Result#{selectedResult}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="mt-4">
              <Button
                variant="ghost"
                onClick={() => setIsDeleteDialogOpen(false)}
                className="text-neutral-200"
              >
                Cancel
              </Button>
              <Button
                onClick={confirmDelete}
                className="bg-red-500 hover:bg-red-600 text-white"
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
