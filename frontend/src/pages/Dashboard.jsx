import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from "../api";

const Dashboard = () => {
  const [analyses, setAnalyses] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('access');
    if (!token) {
      navigate('/login');
      return;
    }

    fetchAnalyses();
  }, [navigate]);

  const fetchAnalyses = async () => {
    try {
      const response = await api.get('/api/analysis/');
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

export default Dashboard;