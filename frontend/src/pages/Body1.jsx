import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './index.css';
import './Body1.css';
import './App.css';

function Body1() {
    const [searchTerm, setSearchTerm] = useState('');
    const navigate = useNavigate();

    const handleSearch = () => {
        navigate('/Organizations', { state: { searchTerm } });
    };

    return (
        <div className="body1-container">
            <div className="image-container">
                <img
                    src={new URL('./assets/ParkingSpots-1.png', import.meta.url).href}
                    alt="Parking Spots Pic"
                    className="background-image"
                    onError={(e) => {
                        console.error("Image failed to load:", e);
                        e.target.style.display = 'none';
                    }}
                />

                <div className="search-container">
                    <h1 className="search-container123">Find Your Parking Spot Easily🚗</h1>
                    <input 
                        type="text" 
                        placeholder="Search for an Organization's Parking Map..." 
                        className="search-input" 
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                                handleSearch();
                            }
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

export default Body1;