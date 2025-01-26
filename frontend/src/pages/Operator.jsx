import { useState, useEffect } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import { ACCESS_TOKEN } from "../constants";
import "../styles/Home.css";
import LoadingIndicator from "../components/LoadingIndicator";
import ConfirmationModal from "../components/ConfirmationModal";
import Confmodal2 from "../components/Confmodal2";
import Confmodal3 from "../components/Confmodal3";

function Operator() {

    const [isAuthorized, setIsAuthorized] = useState(false);
    const [parkingMaps, setParkingMaps] = useState([]);
    const [dimensions, setDimensions] = useState({ width: 0, length: 0 });
    const [orientation, setOrientation] = useState("horizontal");
    const [name, setName] = useState("");
    const [loc, setLoc] = useState("");
    const [showAllMaps, setShowAllMaps] = useState(true);
    const [showAddMap, setshowAddMap] = useState(false);
    const [showMap, setShowMap] = useState(false);
    const [Mapid, setMapid] = useState("");
    const [OPName, setOPName] = useState("");
    const [OPEmail, setOPEmail] = useState("");
    const [OPPN, setOPPN] = useState("");
    const [parkingSpots, setParkingSpots] = useState([]);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [mapId, setMapId] = useState("");
    const [showParkingMaps, setShowParkingMaps] = useState(false);
    const [showCreateMap, setShowCreateMap] = useState(false);
    const [isEditingMap, setIsEditingMap] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [cardsPerPage, setCardsPerPage] = useState(10);
    const [loading, setLoading] = useState(true);
    const [loadingM, setLoadingM] = useState(false);
    const [showProfile, setShowProfile] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [message, setMessage] = useState("");
    const [phoneNumber, setPhoneNumber] = useState(OPPN);
    const [loadingP, setLoadingP] = useState(false);
    const [isModalOpenM, setIsModalOpenM] = useState(false);
    const [actionTypeM, setActionTypeM] = useState(null);
    const [currentMap, setCurrentMap] = useState(null);
    const [loadingt, setLoadingt] = useState(false);
    const [showReports, setShowReports] = useState(false);
    const [mapReports, setMapReports] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedReport, setSelectedReport] = useState(null);
    const [isModalOpenM3, setIsModalOpenM3] = useState(false);
    const [showTooltip, setShowTooltip] = useState(false);


    const handleEditClick = () => {
        setIsEditing(true);
        setPhoneNumber(OPPN);
        setMessage("");
    };

    const handleSaveClick = async () => {
        setMessage("");
        if (phoneNumber.length != 10) {
            setMessage("Phone number must be 10 digits long.");
            return;
        }
        if (phoneNumber == OPPN) {
            setIsEditing(false);
            setLoadingP(false);
            return;
        }
        try {
            setLoadingP(true);
            await api.put("/api/update-phone/", { phone_number: phoneNumber });
            setMessage("Phone number updated successfully!");
            setOPPN(phoneNumber);
            setIsEditing(false);
            setLoadingP(false);
        } catch (error) {
            try {
                setLoadingP(true);
                await api.put("/api/update-phone/", { phone_number: phoneNumber });
                setMessage("Phone number updated successfully!");
                setOPPN(phoneNumber);
                setIsEditing(false);
                setLoadingP(false);
            } catch (error) {
                try {
                    setLoadingP(true);
                    await api.put("/api/update-phone/", { phone_number: phoneNumber });
                    setMessage("Phone number updated successfully!");
                    setOPPN(phoneNumber);
                    setIsEditing(false);
                    setLoadingP(false);
                } catch (error) {
                    try {
                        setLoadingP(true);
                        await api.put("/api/update-phone/", { phone_number: phoneNumber });
                        setMessage("Phone number updated successfully!");
                        setOPPN(phoneNumber);
                        setIsEditing(false);
                        setLoadingP(false);
                    } catch (error) {
                        try {
                            setLoadingP(true);
                            await api.put("/api/update-phone/", { phone_number: phoneNumber });
                            setMessage("Phone number updated successfully!");
                            setOPPN(phoneNumber);
                            setIsEditing(false);
                            setLoadingP(false);
                        } catch (error) {
                            try {
                                setLoadingP(true);
                                await api.put("/api/update-phone/", { phone_number: phoneNumber });
                                setMessage("Phone number updated successfully!");
                                setOPPN(phoneNumber);
                                setIsEditing(false);
                                setLoadingP(false);
                            } catch (error) {
                                try {
                                    setLoadingP(true);
                                    await api.put("/api/update-phone/", { phone_number: phoneNumber });
                                    setMessage("Phone number updated successfully!");
                                    setOPPN(phoneNumber);
                                    setIsEditing(false);
                                    setLoadingP(false);
                                } catch (error) {
                                    console.error("Failed to update phone number:", error);
                                    setMessage("Failed to update phone number. Please try again.");
                                    setLoadingP(false);
                                }
                            }
                        }
                    }
                }
            }
        }
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
                return "rgba(0, 0, 0, 0.5)";
            default:
                return "white";
        }
    };

    const navigate = useNavigate();

    const fetchParkingMaps = async (operatorId) => {
        try {
            const res = await api.get(`/api/parking-map/${operatorId}/`);
            setParkingMaps(res.data);
            setLoading(false);
        } catch (error) {
            try {
                const res = await api.get(`/api/parking-map/${operatorId}/`);
                setParkingMaps(res.data);
                setLoading(false);
            } catch (error) {
                try {
                    const res = await api.get(`/api/parking-map/${operatorId}/`);
                    setParkingMaps(res.data);
                    setLoading(false);
                } catch (error) {
                    try {
                        const res = await api.get(`/api/parking-map/${operatorId}/`);
                        setParkingMaps(res.data);
                        setLoading(false);
                    } catch (error) {
                        setLoading(false);
                        console.error("Failed to load parking maps", error);

                    }
                }
            }
        }
    };

    const fetchParkingSpots = async () => {
        try {
            const response = await api.get(`/api/parking-map/${Mapid}/spots/`);
            setParkingSpots(response.data);
            setLoadingM(false);
        } catch (error) {
            try {
                const response = await api.get(`/api/parking-map/${Mapid}/spots/`);
                setParkingSpots(response.data);
                setLoadingM(false);
            } catch (error) {
                try {
                    const response = await api.get(`/api/parking-map/${Mapid}/spots/`);
                    setParkingSpots(response.data);
                    setLoadingM(false);
                } catch (error) {
                    try {
                        const response = await api.get(`/api/parking-map/${Mapid}/spots/`);
                        setParkingSpots(response.data);
                        setLoadingM(false);
                    } catch (error) {
                        console.error("Error fetching parking spots:", error);
                    }
                }
            }
        }
    };

    const openModalM = (map, action) => {
        setCurrentMap(map);
        setActionTypeM(action);
        setShowParkingMaps(false); // Hide the table when the modal opens
        setIsModalOpenM(true);
    };
    const handleConfirmM = async () => {
        setIsModalOpenM(false);
        setLoadingt(true);

        if (actionTypeM === 'delete') {
            await handleDeleteMap(currentMap.id);
        }
        setLoadingt(false);
        setShowParkingMaps(true); // Show the table again after confirmation
    };
    const flipParkingSpotStatus = async (spotId) => {
        try {
            //setLoadingM(true);
            const response = await api.patch(`/api/parking-spot/${spotId}/flip-status/`);
            const updatedSpot = response.data;
            fetchParkingSpots();
            setParkingSpots((prevSpots) =>
                prevSpots.map((spot) => (spot.id === spotId ? updatedSpot : spot))
            );
            setLoadingM(false);
        } catch (error) {
            try {
                setLoadingM(true);
                const response = await api.patch(`/api/parking-spot/${spotId}/flip-status/`);
                const updatedSpot = response.data;
                fetchParkingSpots();
                setParkingSpots((prevSpots) =>
                    prevSpots.map((spot) => (spot.id === spotId ? updatedSpot : spot))
                );
                setLoadingM(false);
            } catch (error) {
                try {
                    setLoadingM(true);
                    const response = await api.patch(`/api/parking-spot/${spotId}/flip-status/`);
                    const updatedSpot = response.data;
                    fetchParkingSpots();
                    setParkingSpots((prevSpots) =>
                        prevSpots.map((spot) => (spot.id === spotId ? updatedSpot : spot))
                    );
                    setLoadingM(false);
                } catch (error) {
                    console.error("Error flipping parking spot status:", error);
                    setLoadingM(false);
                }
            }
        }
    };

    useEffect(() => {
        const checkOperatorRole = async () => {
            const accessToken = localStorage.getItem(ACCESS_TOKEN);
            if (!accessToken) {
                navigate("/login");
                return;
            }

            try {
                const userRes = await api.get("/api/user/");
                if (userRes.data.role !== "operator") {
                    navigate("/");
                } else {
                    setOPName(userRes.data.organization);
                    setOPEmail(userRes.data.email);
                    setOPPN(userRes.data.phone_number);
                    setIsAuthorized(userRes.data.authorized);
                    if (userRes.data.authorized) {
                        fetchParkingMaps(userRes.data.id);
                    } else setLoading(false);
                }
            } catch (error) {
                try {
                    const userRes = await api.get("/api/user/");
                    if (userRes.data.role !== "operator") {
                        navigate("/");
                    } else {
                        setOPName(userRes.data.organization);
                        setOPEmail(userRes.data.email);
                        setOPPN(userRes.data.phone_number);
                        setIsAuthorized(userRes.data.authorized);
                        if (userRes.data.authorized) {
                            fetchParkingMaps(userRes.data.id);
                        } else setLoading(false);
                    }
                } catch (error) {
                    try {
                        const userRes = await api.get("/api/user/");
                        if (userRes.data.role !== "operator") {
                            navigate("/");
                        } else {
                            setOPName(userRes.data.organization);
                            setOPEmail(userRes.data.email);
                            setOPPN(userRes.data.phone_number);
                            setIsAuthorized(userRes.data.authorized);
                            if (userRes.data.authorized) {
                                fetchParkingMaps(userRes.data.id);
                            } else setLoading(false);
                        }
                    } catch (error) {
                        console.error("Unauthorized", error);
                        navigate("/login");
                    }
                }
            }
        };

        checkOperatorRole();
    }, [navigate]);

    useEffect(() => {
        if (Mapid) {
            console.log("Fetching parking spots for mapId:", Mapid);

            fetchParkingSpots();

            const interval = setInterval(fetchParkingSpots, 5000);
            return () => clearInterval(interval);
        }
    }, [Mapid]);

    useEffect(() => {
        console.log("Parking spots:", parkingSpots);
    }, [parkingSpots]);


    const indexOfLastCard = currentPage * cardsPerPage;
    const indexOfFirstCard = indexOfLastCard - cardsPerPage;
    const currentCards = parkingMaps.slice(indexOfFirstCard, indexOfLastCard);


    const totalPages = Math.ceil(parkingMaps.length / cardsPerPage);
    const loadParkingMaps = async (operatorId) => {
        try {
            const res = await api.get(`/api/parking-map/${operatorId}/`); // Correct URL
            setParkingMaps(res.data);
        } catch (error) {
            try {
                const res = await api.get(`/api/parking-map/${operatorId}/`); // Correct URL
                setParkingMaps(res.data);
            } catch (error) {
                try {
                    const res = await api.get(`/api/parking-map/${operatorId}/`); // Correct URL
                    setParkingMaps(res.data);
                } catch (error) {
                    console.error("Failed to load parking maps", error);
                }
            }
        }
    };

    const handleCreateParkingMap = async () => {
        setError(null);
        setSuccess(null);


        if (dimensions.width < 1 || dimensions.length < 1) {
            setError("Width and length must be positive numbers.");
            return;
        }

        if (name.length < 1) {
            setError("Name cannot be empty.");
            return;
        }
        try {
            setLoadingM(true);
            const res = await api.post("/api/create-parking-map/", {
                name: name,
                width: parseInt(dimensions.width),
                length: parseInt(dimensions.length),
                orientation: orientation,
                loc: loc
            });


            const newMap = {
                id: res.data.id,
                name: res.data.name,
                width: res.data.width,
                length: res.data.length,
                orientation: res.data.orientation,
                loc: res.data.loc,
            };

            try {
                const userRes2 = await api.get("/api/user/");
                loadParkingMaps(userRes2.data.id);

            } catch (error) {
                try {
                    const userRes2 = await api.get("/api/user/");
                    loadParkingMaps(userRes2.data.id);

                } catch (error) {
                    try {
                        const userRes2 = await api.get("/api/user/");
                        loadParkingMaps(userRes2.data.id);

                    } catch (error) {
                        console.error("Unauthorized", error);

                    }

                }

            }
            //setParkingMaps((prev) => [...prev, newMap]);


            //setShowCreateMap(false);
            setLoadingM(false);
            setName("");
            setLoc("");
            setSuccess("Parking Spots Map added successfully!")
            setDimensions({ width: 0, length: 0 });
        } catch (error) {
            try {
                setLoadingM(true);
                const res = await api.post("/api/create-parking-map/", {
                    name: name,
                    width: parseInt(dimensions.width),
                    length: parseInt(dimensions.length),
                    orientation: orientation,
                    loc: loc
                });


                const newMap = {
                    id: res.data.id,
                    name: res.data.name,
                    width: res.data.width,
                    length: res.data.length,
                    orientation: res.data.orientation,
                    loc: res.data.loc,
                };

                try {
                    const userRes2 = await api.get("/api/user/");
                    loadParkingMaps(userRes2.data.id);

                } catch (error) {
                    try {
                        const userRes2 = await api.get("/api/user/");
                        loadParkingMaps(userRes2.data.id);

                    } catch (error) {
                        try {
                            const userRes2 = await api.get("/api/user/");
                            loadParkingMaps(userRes2.data.id);

                        } catch (error) {
                            console.error("Unauthorized", error);

                        }

                    }

                }
                //setParkingMaps((prev) => [...prev, newMap]);


                //setShowCreateMap(false);
                setLoadingM(false);
                setName("");
                setLoc("");
                setSuccess("Parking Spots Map added successfully!")
                setDimensions({ width: 0, length: 0 });
            } catch (error) {
                try {
                    setLoadingM(true);
                    const res = await api.post("/api/create-parking-map/", {
                        name: name,
                        width: parseInt(dimensions.width),
                        length: parseInt(dimensions.length),
                        orientation: orientation,
                        loc: loc
                    });


                    const newMap = {
                        id: res.data.id,
                        name: res.data.name,
                        width: res.data.width,
                        length: res.data.length,
                        orientation: res.data.orientation,
                        loc: res.data.loc,
                    };

                    try {
                        const userRes2 = await api.get("/api/user/");
                        loadParkingMaps(userRes2.data.id);

                    } catch (error) {
                        try {
                            const userRes2 = await api.get("/api/user/");
                            loadParkingMaps(userRes2.data.id);

                        } catch (error) {
                            try {
                                const userRes2 = await api.get("/api/user/");
                                loadParkingMaps(userRes2.data.id);

                            } catch (error) {
                                console.error("Unauthorized", error);

                            }

                        }

                    }
                    //setParkingMaps((prev) => [...prev, newMap]);


                    //setShowCreateMap(false);
                    setLoadingM(false);
                    setName("");
                    setLoc("");
                    setSuccess("Parking Spots Map added successfully!")
                    setDimensions({ width: 0, length: 0 });
                } catch (error) {
                    console.error("Error creating parking map", error);
                    setError("Error creating parking map, Please try again.")
                    fetchParkingMaps();
                    setLoadingM(false);
                }
            }
        }
    };

    const handleEditMap = (mapId) => {
        setMapid(mapId);
        setIsEditingMap(true);
        setLoadingM(true);
        setShowParkingMaps(false);
        setShowMap(true);
    };

    const handleBack = () => {
        setShowParkingMaps(true);
        setShowMap(false);
        setMapid("");
        setIsEditingMap(false);
        setParkingSpots([]);
        setLoadingM(false);
    };

    useEffect(() => {
        const updateCardsPerPage = () => {
            const width = window.innerWidth;
            const height = window.innerHeight;

            if (width >= 1200 && height >= 1000) {
                setCardsPerPage(12);

            }
            else if (height == 1025 && width == 768) {
                setCardsPerPage(2);
            }
            else if (height == 912 && width == 1368) {
                setCardsPerPage(10);
            }
            else if (width >= 992 && height >= 800) {
                setCardsPerPage(12);
            } else if (width >= 768 && height >= 700) {
                setCardsPerPage(6);
            } else if (width >= 768 && height < 700) {
                setCardsPerPage(4);
            } else if (width >= 576 && height >= 500) {
                setCardsPerPage(3);
            } else if (width >= 390 && height >= 400) {
                setCardsPerPage(2);
            } else {
                setCardsPerPage(1); // very small screens
            }
        };

        window.addEventListener('resize', updateCardsPerPage);
        updateCardsPerPage();

        return () => {
            window.removeEventListener('resize', updateCardsPerPage);
        };
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }



    const handleDeleteMap = async (mapId) => {
        try {
            setLoadingM(true);
            await api.delete(`/api/map/${mapId}/Reject/`);
            setParkingMaps((prevMaps) => prevMaps.filter((map) => map.id !== mapId));
            setLoadingM(false);
        } catch (error) {
            try {
                setLoadingM(true);
                await api.delete(`/api/map/${mapId}/Reject/`);
                setParkingMaps((prevMaps) => prevMaps.filter((map) => map.id !== mapId));
                setLoadingM(false);
            } catch (error) {
                try {
                    setLoadingM(true);
                    await api.delete(`/api/map/${mapId}/Reject/`);
                    setParkingMaps((prevMaps) => prevMaps.filter((map) => map.id !== mapId));
                    setLoadingM(false);
                } catch (error) {
                    try {
                        setLoadingM(true);
                        await api.delete(`/api/map/${mapId}/Reject/`);
                        setParkingMaps((prevMaps) => prevMaps.filter((map) => map.id !== mapId));
                        setLoadingM(false);
                    } catch (error) {
                        try {
                            setLoadingM(true);
                            await api.delete(`/api/map/${mapId}/Reject/`);
                            setParkingMaps((prevMaps) => prevMaps.filter((map) => map.id !== mapId));
                            setLoadingM(false);
                        } catch (error) {
                            console.error("Error deleting parking map:", error);
                            setLoadingM(false);
                        }
                    }
                }
            }
        }
    };

    const handleViewReports = async (mapId) => {
        try {
            const response = await api.get(`/api/map-reports/${mapId}/`);
            setMapReports(response.data);
            setShowParkingMaps(false);
            setShowReports(true);
        } catch (error) {
            console.error('Error fetching reports:', error);
        }
    };

    const handleDeleteReport = async () => {
        try {
            await api.delete(`/api/map-report/${selectedReport.id}/`);
            setMapReports(prevReports =>
                prevReports.filter(report => report.id !== selectedReport.id)
            );
            setIsModalOpenM3(false);
            setSelectedReport(null);
            setShowReports(true);
        } catch (error) {
            console.error('Error deleting report:', error);
        }
    };

    return (
        <div className="operator-container">
            <h2 className="welcome-operator">Operator Dashboard</h2>
            {isAuthorized && !isEditingMap && (
                <div className="button-container">
                    <button className="Opbutton" onClick={() => { setShowParkingMaps(true); setShowCreateMap(false); setShowProfile(false); setShowReports(false); }}>Show Parking Spot Maps</button>
                    <button className="Opbutton" onClick={() => { setShowParkingMaps(false); setShowCreateMap(true); setShowProfile(false); setError(null); setSuccess(null); setShowReports(false); }}>Create Parking Spot Map</button>
                    <button className="Opbutton" onClick={() => { setShowParkingMaps(false); setShowCreateMap(false); setShowProfile(true); setMessage(""); setIsEditing(false); setShowReports(false); }}>Show Profile Details</button>
                </div>
            )}
            {loadingt && <LoadingIndicator />}
            {isAuthorized && showParkingMaps && (
                <>
                    <h3 className="fontcolorsss">Parking Spot Maps</h3>
                    <div className="card-container">
                        {currentCards.length > 0 ? (
                            currentCards.map((map) => (
                                <div className="card" key={map.id}>
                                    {/* <h4 className="fontcolorsss">Map ID: {map.id}</h4> */}
                                    <h4 className="fontcolorsss">Name: {map.name}</h4>
                                    <a href={map.loc}> Location</a>
                                    <p className="fontcolorsss">Dimensions: {map.width} x {map.length}</p>
                                    <p className="fontcolorsss">Status: {map.accepted ? 'Accepted✅' : 'Pending⏳'}</p>
                                    <button className="Opbutton" onClick={() => handleEditMap(map.id)}>Edit Parking Spot Map</button><br />
                                    {/*<button className="Opbutton" onClick={() => handleDeleteMap(map.id)}>Delete Map</button>*/}
                                    <button className="Opbuttonr" onClick={() => openModalM(map, 'delete')}>Delete</button>
                                    <button className="Opbutton" onClick={() => handleViewReports(map.id)}>View Issues</button>
                                </div>
                            ))
                        ) : (
                            <p className="fontcolorsss">No parking spot maps available.</p>
                        )}
                    </div>

                    {/* Pagination Controls */}
                    <div className="pagination">
                        {currentPage > 1 && (
                            <button onClick={() => setCurrentPage(currentPage - 1)}>
                                Previous
                            </button>
                        )}

                        {currentPage < totalPages && (
                            <button onClick={() => setCurrentPage(currentPage + 1)}>
                                Next
                            </button>
                        )}
                    </div>
                </>
            )}

            {isAuthorized && showCreateMap && (
                <div className="create-map-container">
                    <h3 className="create-map-heading">Create Parking Spot Map</h3>
                    <label className="create-map-label">
                        Name:
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                        />
                    </label>
                    <br />
                    <label className="create-map-label">
                        Width:
                        <input
                            type="number"
                            value={dimensions.width}
                            onChange={(e) => setDimensions({ ...dimensions, width: e.target.value })}
                        />
                    </label>
                    <br />
                    <label className="create-map-label">
                        Length:
                        <input
                            type="number"
                            value={dimensions.length}
                            onChange={(e) => setDimensions({ ...dimensions, length: e.target.value })}
                        />
                    </label>
                    <br />
                    <label className="create-map-label">
                        Location:
                        <input
                            type="text"
                            value={loc}
                            onChange={(e) => setLoc(e.target.value)}
                        />
                    </label>
                    <br />
                    {error && <p className="error-message">{error}</p>}
                    {success && <p className="success-message">{success}</p>}
                    <br />
                    {loadingM && <LoadingIndicator />}
                    <br />
                    <button className="create-map-button" onClick={handleCreateParkingMap}>Create Parking Spot Map</button>
                </div>
            )}

            {isAuthorized && showProfile && (
                <div className="card">
                    <br />
                    <h2 className="proffontb">Profile</h2>

                    <h4 className="proffont">Oragnization: {OPName}</h4>



                    <h4 className="proffont">Email: {OPEmail}</h4>



                    <h4 className="proffont">
                        Phone Number:{" "}
                        {isEditing ? (
                            <input
                                type="text"
                                value={phoneNumber}
                                onChange={(e) => setPhoneNumber(e.target.value)}
                            />
                        ) : (
                            OPPN
                        )}
                        <br /><br /><button className="Opbutton" onClick={isEditing ? handleSaveClick : handleEditClick}>
                            {isEditing ? "Save" : "Edit"}
                        </button>
                    </h4>
                    {message && <p>{message}</p>}
                    {loadingP && <LoadingIndicator />}

                    {/* Display success or failure message */}


                </div>
            )}

            {isAuthorized && showMap && (
                <>
                    <button className="Opbutton" onClick={handleBack}>
                        Back
                    </button>
                    {loadingM && <LoadingIndicator />}
                    <div className="table-cont">
                        <div className="centerre"> </div>
                        <table>
                            <tbody>
                                {parkingSpots.length > 0 && (
                                    [...Array(Math.max(...parkingSpots.map(spot => spot.y_axis)) + 1)].map((_, row) => (
                                        <tr key={row}>
                                            {[...Array(Math.max(...parkingSpots.map(spot => spot.x_axis)) + 1)].map((_, col) => {
                                                const spot = parkingSpots.find(s => s.x_axis === col && s.y_axis === row);
                                                return (
                                                    <td className="tdspots"
                                                        key={col}
                                                        style={{ backgroundColor: spot ? getColorByStatus(spot.status, spot.sensor_status) : 'white' }}
                                                        onClick={() => spot && flipParkingSpotStatus(spot.id)}
                                                    >{/* onClick={() => spot && flipParkingSpotStatus(spot.id)} */}
                                                        {spot ? `${spot.id}` : 'N/A'}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                        <div
                            className={`tooltip-container ${showTooltip ? 'expanded' : ''}`}
                            onClick={() => setShowTooltip(!showTooltip)}
                        >
                            <div className="tooltip-icon"></div>
                            <div className="tooltip-text">
                                Change a parking spot status by clicking on it
                            </div>
                        </div>
                    </div>
                </>
            )}

            {showReports && !isModalOpenM3 && (
                <>
                    <button className="back-button" onClick={() => {
                        setShowReports(false);
                        setShowParkingMaps(true);
                    }}>
                        Back to Maps
                    </button>
                    <div className="reports-container">
                        <h2>Map Issues</h2>
                        {mapReports.length > 0 ? (
                            <div className="reports-list">
                                {mapReports.map(report => (
                                    <div key={report.id} className="report-item">
                                        <div className="report-header">
                                            <p
                                                className="report-text"
                                                style={{
                                                    fontSize: report.font_size,
                                                    fontFamily: report.font_family,
                                                    textAlign: report.text_align,
                                                    fontWeight: report.font_weight,
                                                    fontStyle: report.font_style
                                                }}
                                            >
                                                {report.text}
                                            </p>
                                            <button
                                                className="delete-report-btn"
                                                onClick={() => {
                                                    setSelectedReport(report);
                                                    setIsModalOpenM3(true);
                                                }}
                                            >
                                                ×
                                            </button>
                                        </div>
                                        <small className="report-date">
                                            {new Date(report.created_at).toLocaleString()}
                                        </small>
                                    </div>
                                ))}
                            </div>
                        ) : (<div><br />
                            <h2>No reports found for this map.</h2>
                        </div>)}
                    </div> </>
            )}

            <Confmodal3
                isOpen={isModalOpenM3}
                onClose={() => {
                    setIsModalOpenM3(false);
                    setSelectedReport(null);
                }}
                onConfirm={handleDeleteReport}
                message="Are you sure you want to delete this report?"
            />

            {!isAuthorized && (
                <div>
                    <p className="welcome-operator">
                        You are not authorized. An admin will contact you soon 😊.
                    </p>
                </div>
            )}
            <Confmodal2
                isOpen={isModalOpenM}
                onClose={() => {
                    setIsModalOpenM(false);
                    setShowParkingMaps(true); // Show the table again if modal is closed
                }}
                onConfirm={handleConfirmM}
                mapDetails={currentMap}
                actionType={actionTypeM} // Pass the action type to the modal
            />
        </div>
    );
}

export default Operator;
