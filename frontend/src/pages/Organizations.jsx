import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import "../styles/Organizations.css";
import "../styles/Home.css";
import api from "../api";
import LoadingIndicator from "../components/LoadingIndicator";

const Organizations = () => {
    const location = useLocation();
    const [organizations, setOrganizations] = useState([]);
    const [filteredOrganizations, setFilteredOrganizations] = useState([]);
    const [searchTerm, setSearchTerm] = useState(location.state?.searchTerm || "");
    const [showMap, setShowMap] = useState(false);
    const [selectedOrg, setSelectedOrg] = useState(null);
    const [parkingSpots, setParkingSpots] = useState([]);
    const [loadingM, setLoadingM] = useState(false);
    const [loading, setLoading] = useState(true);
    const [showReportForm, setShowReportForm] = useState(false);
    const [reportText, setReportText] = useState('');
    const [reportSuccess, setReportSuccess] = useState(false);
    const [error, setError] = useState(null);
    const [textStyle, setTextStyle] = useState({
        fontSize: '16px',
        fontFamily: 'Arial',
        textAlign: 'left',
        fontWeight: 'normal',
        fontStyle: 'normal'
    });
    const [usedSpots, setUsedSpots] = useState(0);
    const [unusedSpots, setUnusedSpots] = useState(0);

    useEffect(() => {
        const fetchOrganizations = async () => {
            try {
                const response = await api.get("/api/organizations/");
                console.log("Organizations fetched: ", response.data);
                setLoading(false);
                setOrganizations(response.data);
                setFilteredOrganizations(response.data);
            } catch (error) {
                console.error("Error fetching organizations:", error);
            }
        };
        fetchOrganizations();
    }, []);

    useEffect(() => {
        const results = organizations.filter(
            (org) =>
                org.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                org.org.toLowerCase().includes(searchTerm.toLowerCase())
        );
        setFilteredOrganizations(results);
    }, [searchTerm, organizations]);

    const countParkingSpots = (spots) => {
        let used = 0;
        let unused = 0;
        
        spots.forEach(spot => {
            if (spot.status === 'sensor') {
                if (spot.sensor_status === 'used') {
                    used++;
                } else {
                    unused++;
                }
            }
        });
        
        setUsedSpots(used);
        setUnusedSpots(unused);
    };

    const fetchParkingSpots = async (orgId) => {
        try {
            const response = await api.get(`/api/parking-map/${orgId}/spots/`);
            console.log("Parking spots response:", response.data);
            if (Array.isArray(response.data)) {
                setParkingSpots(response.data);
                countParkingSpots(response.data);
            } else {
                setParkingSpots([]);
                setUsedSpots(0);
                setUnusedSpots(0);
            }
        } catch (error) {
            console.error("Error fetching parking spots:", error);
            setParkingSpots([]);
            setUsedSpots(0);
            setUnusedSpots(0);
        }
    };

    const handleCardClick = (org) => {
        setSelectedOrg(org);
        setShowMap(true);
        setLoadingM(true);
        fetchParkingSpots(org.id).finally(() => setLoadingM(false));
    };

    useEffect(() => {
        if (showMap && selectedOrg) {
            const interval = setInterval(() => {
                fetchParkingSpots(selectedOrg.id);
            }, 5000);

            return () => clearInterval(interval);
        }
    }, [showMap, selectedOrg]);

    const handleBack = () => {
        setShowMap(false);
        setSelectedOrg(null);
        setParkingSpots([]);
        setReportText('');
        setShowReportForm(false);
    };

    const getColorByStatus = (status, sensor_status) => {
        switch (status) {
            case "sensor":
                return sensor_status === "used" ? "red" : "green";
            case "maintenance":
                return "yellow";
            case "unavailable":
                return "transparent";
            case "road":
                return "rgba(0, 0, 0, 0.8)";
            default:
                return "white";
        }
    };

    const getSpotClasses = (spot) => {
        if (!spot) return 'tdspots2';
        let classes = 'tdspots2';
        
        if (spot.status === 'unavailable') {
            classes += ' spot-unavailable';
        } else if (spot.status === 'road') {
            classes += ' spot-road';
        }

        return classes;
    };

    const getBorderStyle = (spot, parkingSpots) => {
        if (!spot) return "1px solid #000";
        
        const borders = {
            top: "1px solid #000",
            right: "1px solid #000",
            bottom: "1px solid #000",
            left: "1px solid #000"
        };

        // Check adjacent cells
        const topSpot = parkingSpots.find(s => s.x_axis === spot.x_axis && s.y_axis === spot.y_axis - 1);
        const rightSpot = parkingSpots.find(s => s.x_axis === spot.x_axis + 1 && s.y_axis === spot.y_axis);
        const bottomSpot = parkingSpots.find(s => s.x_axis === spot.x_axis && s.y_axis === spot.y_axis + 1);
        const leftSpot = parkingSpots.find(s => s.x_axis === spot.x_axis - 1 && s.y_axis === spot.y_axis);

        // Remove borders between matching unavailable or road spots
        if (spot.status === "unavailable" || spot.status === "road") {
            if (topSpot?.status === spot.status) borders.top = "none";
            if (rightSpot?.status === spot.status) borders.right = "none";
            if (bottomSpot?.status === spot.status) borders.bottom = "none";
            if (leftSpot?.status === spot.status) borders.left = "none";
        }

        return {
            borderTop: borders.top,
            borderRight: borders.right,
            borderBottom: borders.bottom,
            borderLeft: borders.left
        };
    };

    const handleSubmitReport = async () => {
        if (!reportText.trim()) {
            setError("Please enter an issue");
            return;
        }
        
        try {
            await api.post('/api/map-report/', {
                parking_map: selectedOrg.id,
                text: reportText,
                font_size: textStyle.fontSize,
                font_family: textStyle.fontFamily,
                text_align: textStyle.textAlign,
                font_weight: textStyle.fontWeight,
                font_style: textStyle.fontStyle
            });
            setReportSuccess(true);
            setReportText('');
            setTimeout(() => {
                setShowReportForm(false);
                setReportSuccess(false);
            }, 2000);
        } catch (error) {
            console.error('Error submitting report:', error);
            setError("Failed to submit report. Please try again.");
        }
    };

    const handleStyleChange = (property, value) => {
        setTextStyle(prev => ({
            ...prev,
            [property]: value
        }));
    };

    return (
        <div className="organizations-background1">
            {showMap ? (
                <div className="map-view-container2">
                    <h2 className="map-heading">{selectedOrg?.name} Parking Map</h2>
                    
                    <button className="back-button" onClick={handleBack}>
                        Back
                    </button>
                    <br />
                    <div className="table-cont1">
                        {loadingM ? (
                            <LoadingIndicator />
                        ) : (
                            <>
                                {!showReportForm ? (
                                    <>
                                        <div className="parking-stats">
                                            <div className="stat-item">
                                                <span className="stat-label">Available:</span>
                                                <span className="stat-value available">{unusedSpots}</span>
                                            </div>
                                            <div className="stat-item">
                                                <span className="stat-label">Occupied:</span>
                                                <span className="stat-value occupied">{usedSpots}</span>
                                            </div>
                                        </div>
                                        <div className="centerre2">
                                            {parkingSpots.length > 0 ? (
                                                <table>
                                                    <tbody>
                                                        {[...Array(Math.max(...parkingSpots.map((spot) => spot.y_axis)) + 1)].map(
                                                            (_, row) => (
                                                                <tr key={row}>
                                                                    {[...Array(Math.max(...parkingSpots.map((spot) => spot.x_axis)) + 1)].map(
                                                                        (_, col) => {
                                                                            const spot = parkingSpots.find(
                                                                                (s) => s.x_axis === col && s.y_axis === row
                                                                            );
                                                                            return (
                                                                                <td
                                                                                    className={getSpotClasses(spot)}
                                                                                    key={col}
                                                                                    style={{
                                                                                        ...getBorderStyle(spot, parkingSpots),
                                                                                        backgroundColor: spot && spot.status !== 'unavailable' && spot.status !== 'road'
                                                                                            ? getColorByStatus(spot.status, spot.sensor_status)
                                                                                            : undefined
                                                                                    }}
                                                                                >
                                                                                    { }
                                                                                </td>
                                                                            );
                                                                        }
                                                                    )}
                                                                </tr>
                                                            )
                                                        )}
                                                    </tbody>
                                                </table>
                                            ) : (
                                                <p className="Gmessage">No parking spots available.</p>
                                            )}
                                        </div>
                                        <button 
                                            className="report-button"
                                            onClick={() => { setShowReportForm(true); setError(null); }}
                                        >
                                            Is there any issue?
                                        </button>
                                    </>
                                ) : (
                                    <div className="report-form">
                                        {reportSuccess ? (
                                            <p className="success-message">Report submitted successfully!</p>
                                        ) : (
                                            <>
                                                <div className="text-controls">
                                                    <select 
                                                        onChange={(e) => handleStyleChange('fontSize', e.target.value)}
                                                        value={textStyle.fontSize}
                                                    >
                                                        <option value="12px">Small Text</option>
                                                        <option value="16px">Medium Text</option>
                                                        <option value="20px">Large Text</option>
                                                    </select>

                                                    <select 
                                                        onChange={(e) => handleStyleChange('fontFamily', e.target.value)}
                                                        value={textStyle.fontFamily}
                                                    >
                                                        <option value="Arial">Arial Font</option>
                                                        <option value="Times New Roman">Times New Roman</option>
                                                        <option value="Courier New">Courier New</option>
                                                    </select>

                                                    <select 
                                                        onChange={(e) => handleStyleChange('textAlign', e.target.value)}
                                                        value={textStyle.textAlign}
                                                    >
                                                        <option value="left">Align Left</option>
                                                        <option value="center">Align Center</option>
                                                        <option value="right">Align Right</option>
                                                    </select>

                                                    <button 
                                                        type="button" 
                                                        onClick={() => handleStyleChange('fontWeight', textStyle.fontWeight === 'bold' ? 'normal' : 'bold')}
                                                        className={textStyle.fontWeight === 'bold' ? 'active' : ''}
                                                        title="Bold"
                                                    >
                                                        Bold
                                                    </button>

                                                    <button 
                                                        type="button" 
                                                        onClick={() => handleStyleChange('fontStyle', textStyle.fontStyle === 'italic' ? 'normal' : 'italic')}
                                                        className={textStyle.fontStyle === 'italic' ? 'active' : ''}
                                                        title="Italic"
                                                    >
                                                        Italic
                                                    </button>
                                                </div>

                                                <textarea
                                                    value={reportText}
                                                    onChange={(e) => setReportText(e.target.value)}
                                                    maxLength={255}
                                                    placeholder="Describe the issue..."
                                                    rows={5}
                                                    cols={10}
                                                    style={textStyle}
                                                />
                                                {error && <p className="error-message">{error}</p>}
                                                <div className="report-buttons">
                                                    <button onClick={handleSubmitReport}>Submit</button>
                                                    <button onClick={() => setShowReportForm(false)}>Cancel</button>
                                                </div>
                                                <p className="char-count">{reportText.length}/255</p>
                                            </>
                                        )}
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            ) : (
                <div className="organizations-container1">
                    <h1 className="heading1">Organizations Maps</h1>
                    <input
                        type="text"
                        placeholder="Search for an Organization's Parking Map..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="search-input1"
                    />
                    <div className="card-container1">
                        {loading && <LoadingIndicator />}
                        {!loading && filteredOrganizations.length > 0 && (
                            filteredOrganizations.map((org) => (
                                <div
                                    className="card1"
                                    key={org.id}
                                    onClick={() => handleCardClick(org)}
                                >
                                    <h4 className="card-title1">{org.name}</h4>
                                    <p className="card-text1">Organization: {org.org}</p>
                                    <p className="card-link1">
                                        <a href={org.loc} target="_blank" rel="noopener noreferrer">
                                            Location
                                        </a>
                                    </p>
                                </div>
                            ))
                        )}
                    </div>
                    {!loading && filteredOrganizations.length === 0 ? (
                        <p className="Gmessage2">No organizations found.</p>
                    ) : (
                        <br />
                    )}
                </div>
            )}
        </div>
    );
};

export default Organizations;
