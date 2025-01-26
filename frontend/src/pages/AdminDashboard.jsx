import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ACCESS_TOKEN } from "../constants";
import api from "../api";
import "../styles/AdminDashboard.css";
import "../styles/Organizations.css";
import ConfirmationModal from "../components/ConfirmationModal";
import Confmodal from "../components/Confmodal";
import LoadingIndicator from "../components/LoadingIndicator";

const AdminDashboard = () => {
  const [operators, setOperators] = useState([]);
  const [allOperators, setAllOperators] = useState([]); //ذا والي فوقه يختلفون الي تحت حق كل العملاء الي تم اعتمادهم
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [currentPageAll, setCurrentPageAll] = useState(1);
  const [currentPageMaps, setCurrentPageMaps] = useState(1);
  const [currentPageAllMaps, setCurrentPageAllMaps] = useState(1);
  const [showAuthorized, setShowAuthorized] = useState(false);
  const [showAllAuthorized, setShowAllAuthorized] = useState(false); //الداشبورد اول ماتدخلها فاضية وفيه ازرار تفتح لك الجداول، السطر هذا والي فوقه حق انها تكون مخفية بالبداية لين تضغطها
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isModalOpenM, setIsModalOpenM] = useState(false);
  const [currentOperator, setCurrentOperator] = useState(null);
  const [currentMap, setCurrentMap] = useState(null);
  const [actionType, setActionType] = useState(null);
  const [actionTypeM, setActionTypeM] = useState(null);
  const [isTableVisible, setIsTableVisible] = useState(true);
  const [showNonAuthMaps, setShowNonAuthMaps] = useState(false);
  const [showAllAutMaps, setShowAllAutMaps] = useState(false);
  const [nonMaps, setNonMaps] = useState([]);
  const [allMaps, setAllMaps] = useState([]);
  const [showMap, setShowMap] = useState(false);
  const [Mapid, setMapid] = useState("");
  const [parkingSpots, setParkingSpots] = useState([]);
  const [loadingM, setLoadingM] = useState(false);
  const [loadingt, setLoadingt] = useState(false);
  const navigate = useNavigate();
  const rowsPerPage = 5;


  const getColorByStatus = (status, sensor_status) => {
    switch (status) {
      case "sensor":
        return sensor_status === "used" ? "red" : "green";
      case "maintenance":
        return "yellow";
      case "unavailable":
        return "transparent";
      case "road":
        return "rgba(0, 0, 0, 0.5)"; // 50% transparent black
      default:
        return "white";
    }
  };

  /*const getSpotClasses = (spot) => {
    if (!spot) return 'tdspots3';
    let classes = 'tdspots3';
    
    if (spot.status === 'unavailable') {
        classes += ' spot-unavailable';
    } else if (spot.status === 'road') {
        classes += ' spot-road';
    }

    return classes;
  };*/

  const getBorderStyle = (spot, parkingSpots) => {
    if (!spot) return "1px solid #000";
    
    const borders = {
        borderTop: "1px solid #000",
        borderRight: "1px solid #000",
        borderBottom: "1px solid #000",
        borderLeft: "1px solid #000"
    };

    // Check adjacent cells
    const topSpot = parkingSpots.find(s => s.x_axis === spot.x_axis && s.y_axis === spot.y_axis - 1);
    const rightSpot = parkingSpots.find(s => s.x_axis === spot.x_axis + 1 && s.y_axis === spot.y_axis);
    const bottomSpot = parkingSpots.find(s => s.x_axis === spot.x_axis && s.y_axis === spot.y_axis + 1);
    const leftSpot = parkingSpots.find(s => s.x_axis === spot.x_axis - 1 && s.y_axis === spot.y_axis);

    // Remove borders between matching unavailable or road spots
    if (spot.status === "unavailable" || spot.status === "road") {
        if (topSpot?.status === spot.status) borders.borderTop = "none";
        if (rightSpot?.status === spot.status) borders.borderRight = "none";
        if (bottomSpot?.status === spot.status) borders.borderBottom = "none";
        if (leftSpot?.status === spot.status) borders.borderLeft = "none";
    }

    return borders;
  };

  useEffect(() => {
    const checkAdminRole = async () => {
      const accessToken = localStorage.getItem(ACCESS_TOKEN);
      if (!accessToken) {
        navigate("/login");
        return;
      }

      try {
        const userRes = await api.get("/api/user/");
        if (userRes.data.role !== "admin") {
          navigate("/");
        } else {
          fetchOperators(); //Fetch unAuth
          fetchAllAuthorizedOperators(); // Fetch all Auth operators on load
          fetchNonAutMaps();
          fetchAllAuthMaps();
        }
      } catch (error) {
        console.error("Unauthorized", error);
        navigate("/login");
      }
    };

    checkAdminRole();
  }, [navigate]);

  const fetchParkingSpots = async () => {
    try {

      const response = await api.get(`/api/parking-map/${Mapid}/spots/`);
      setParkingSpots(response.data);
      console.log(response.data[0].status);
      console.log(response.data[0].sensor_status);
      console.log(response.data.length);
      // SPRINT 4 USER STORY: make a for loop that goes to each spot and detirmine if its a sensor dependent&&its status is used or unused and there should be counters
      setLoadingM(false);
    } catch (error) {
      console.error("Error fetching parking spots:", error);
    }
  };
  useEffect(() => {
    if (Mapid) {
      console.log("Fetching parking spots for mapId:", Mapid); setParkingSpots([])
      fetchParkingSpots();
      const interval = setInterval(fetchParkingSpots, 5000);
      return () => clearInterval(interval);
    }
  }, [Mapid]);
  const handleEditMap = (mapId) => {
    setMapid(mapId);
    //setIsEditingMap(true);
    setIsTableVisible(false);
    setShowMap(true);
    setLoadingM(true);
  };

  const handleBack = () => {
    setIsTableVisible(true);
    setShowMap(false);
    setMapid("");
    //setIsEditingMap(false);
    setParkingSpots([]);
    setLoadingM(false);
  };
  const fetchOperators = async () => {
    try {
      const res = await api.get("/api/operators/unapproved/");
      setOperators(res.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching operators", error);
    }
  };

  const fetchAllAuthorizedOperators = async () => {
    try {
      const res = await api.get("/api/operators/authorized/");
      setAllOperators(res.data);
    } catch (error) {
      console.error("Error fetching all authorized operators", error);
    }
  };
  const fetchNonAutMaps = async () => {
    try {
      const res = await api.get("/api/maps/unapproved/");
      setNonMaps(res.data);
    } catch (error) {
      console.error("Error fetching maps", error);
    }
  };
  const fetchAllAuthMaps = async () => {
    try {
      const res = await api.get("/api/maps/authorized/");
      setAllMaps(res.data);
    } catch (error) {
      console.error("Error fetching all accepted maps", error);
    }
  };


  const openModal = (operator, action) => {
    setCurrentOperator(operator);
    setActionType(action);
    setIsTableVisible(false); // Hide the table when the modal opens
    setIsModalOpen(true);
  };
  const openModalM = (map, action) => {
    setCurrentMap(map);
    setActionTypeM(action);
    setIsTableVisible(false); // Hide the table when the modal opens
    setIsModalOpenM(true);
  };

  const handleConfirm = async () => {
    if (actionType === 'accept') {
      await handleAuthorize(currentOperator.id);
    } else if (actionType === 'reject') {
      await RejectOP(currentOperator.id);
    } else if (actionType === 'delete') {
      await handleDelete(currentOperator.id);
    }
    setIsModalOpen(false);
    setIsTableVisible(true); // Show the table again after confirmation
  };
  const handleConfirmM = async () => {
    setIsModalOpenM(false);
    setLoadingt(true);
    if (actionTypeM === 'accept') {
      await handleAcceptM(currentMap.id);
    } else if (actionTypeM === 'reject') {
      await RejectM(currentMap.id);
    } else if (actionTypeM === 'delete') {
      await handleDeleteM(currentMap.id);
    }
    setLoadingt(false);
    setIsTableVisible(true); // Show the table again after confirmation
  };

  const handleAuthorize = async (operatorId) => {
    try {
      const res = await api.patch(`/api/operators/${operatorId}/authorize/`);
      setOperators((prev) => prev.filter((operator) => operator.id !== operatorId));
      setAllOperators((prev) => [...prev, res.data]);
      await fetchAllAuthorizedOperators(); // Uncomment if the API changes need verification
    } catch (error) {
      console.error("Error Accepting operator", error);
    }
  };


  const RejectOP = async (operatorId) => {
    try {
      await api.delete(`/api/operators/${operatorId}/Reject/`);
      setOperators((prev) => prev.filter((operator) => operator.id !== operatorId));
    } catch (error) {
      console.error("Error rejecting operator", error);
    }
  };

  const handleDelete = async (operatorId) => {
    try {
      await api.delete(`/api/operators/${operatorId}/Reject/`); // Use the correct endpoint
      setAllOperators((prev) => prev.filter((operator) => operator.id !== operatorId));
      await fetchAllAuthMaps();
      await fetchNonAutMaps();
    } catch (error) {
      console.error("Error deleting operator", error);
    }
  };


  const handleAcceptM = async (mapId) => {
    try {
      const res = await api.patch(`/api/map/${mapId}/authorize/`);
      setNonMaps((prev) => prev.filter((map) => map.id !== mapId));
      setAllMaps((prev) => [...prev, res.data]);
      await fetchAllAuthMaps(); // Uncomment if the API changes need verification
    } catch (error) {
      console.error("Error Accepting Map", error);
    }
  };


  const RejectM = async (mapId) => {
    try {
      await api.delete(`/api/map/${mapId}/Reject/`);
      setNonMaps((prev) => prev.filter((map) => map.id !== mapId));
    } catch (error) {
      console.error("Error rejecting map", error);
    }
  };

  const handleDeleteM = async (mapId) => {
    try {
      await api.delete(`/api/map/${mapId}/Reject/`); // Use the correct endpoint
      setAllMaps((prev) => prev.filter((map) => map.id !== mapId));
    } catch (error) {
      console.error("Error deleting map", error);
    }
  };
  const indexOfLastRow = currentPage * rowsPerPage;
  const indexOfFirstRow = indexOfLastRow - rowsPerPage;
  const currentRows = operators.slice(indexOfFirstRow, indexOfLastRow);
  const totalPages = Math.ceil(operators.length / rowsPerPage);

  // Pagination for all operators
  const indexOfLastRowAll = currentPageAll * rowsPerPage;
  const indexOfFirstRowAll = indexOfLastRowAll - rowsPerPage;
  const currentRowsAll = allOperators.slice(indexOfFirstRowAll, indexOfLastRowAll);
  const totalPagesAll = Math.ceil(allOperators.length / rowsPerPage);

  const indexOfLastRowMaps = currentPageMaps * rowsPerPage;
  const indexOfFirstRowMaps = indexOfLastRowMaps - rowsPerPage;
  const currentRowsMaps = nonMaps.slice(indexOfFirstRowMaps, indexOfLastRowMaps);
  const totalPagesMaps = Math.ceil(nonMaps.length / rowsPerPage);

  const indexOfLastRowAllMaps = currentPageAllMaps * rowsPerPage;
  const indexOfFirstRowAllMaps = indexOfLastRowAllMaps - rowsPerPage;
  const currentRowsAllMaps = allMaps.slice(indexOfFirstRowAllMaps, indexOfLastRowAllMaps);
  const totalPagesAllMaps = Math.ceil(allMaps.length / rowsPerPage);

  const getSpotClasses = (spot) => {
    if (!spot) return 'tdspots3';
    let classes = 'tdspots3';
    
    if (spot.status === 'unavailable') {
        classes += ' spot-unavailable';
    } else if (spot.status === 'road') {
        classes += ' spot-road';
    }

    return classes;
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="admin-dashboard">
      <h1>Admin Dashboard</h1>
      <div className="button-container1">
        <button onClick={() => { setShowAuthorized(true); setShowAllAuthorized(false); setShowNonAuthMaps(false); setShowAllAutMaps(false); }}>Pending Operators Requests</button>
        <button onClick={() => { setShowAuthorized(false); setShowAllAuthorized(true); setShowNonAuthMaps(false); setShowAllAutMaps(false); }}>All Accepted Operators</button>
        <button onClick={() => { setShowAuthorized(false); setShowAllAuthorized(false); setShowNonAuthMaps(true); setShowAllAutMaps(false); }}>Pending Maps Requests</button>
        <button onClick={() => { setShowAuthorized(false); setShowAllAuthorized(false); setShowNonAuthMaps(false); setShowAllAutMaps(true); }}>All Accepted Maps</button>
      </div>
      <br />
      {loadingt && <LoadingIndicator />}
      {showAuthorized && isTableVisible && ( // Check if the table should be visible
        <div className="table-container">
          <h2 className='Table-heading'>Accept Operators</h2>
          {operators.length === 0 ? (
            <p>No operators pending Acceptance.</p>
          ) : (
            <div>
              <table>
                <thead>
                  <tr>
                    <th>Organization</th>
                    <th>Email</th>
                    <th>Phone Number</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {currentRows.map((operator) => (
                    <tr key={operator.id}>
                      <td>{operator.organization}</td>
                      <td>{operator.email}</td>
                      <td>{operator.phone_number}</td>
                      <td>
                        <button onClick={() => openModal(operator, 'accept')}>Accept</button>
                        <button onClick={() => openModal(operator, 'reject')}>Reject</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="pagination">
                {Array.from({ length: totalPages }, (_, index) => (
                  <button
                    key={index + 1}
                    onClick={() => setCurrentPage(index + 1)}
                    className={currentPage === index + 1 ? "active" : ""}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {showAllAuthorized && isTableVisible && ( // Check if the table should be visible
        <div className="table-container">
          <h2 className='Table-heading'>All Authorized Operators</h2>
          {allOperators.length === 0 ? (
            <p>No authorized operators available for deletion.</p>
          ) : (
            <div>
              <table>
                <thead>
                  <tr>
                    <th>Organization</th>
                    <th>Email</th>
                    <th>Phone Number</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {currentRowsAll.map((operator) => (
                    <tr key={operator.id}>
                      <td>{operator.organization}</td>
                      <td>{operator.email}</td>
                      <td>{operator.phone_number}</td>
                      <td>
                        <button onClick={() => openModal(operator, 'delete')}>Delete</button> {/* Delete button */}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="pagination">
                {Array.from({ length: totalPagesAll }, (_, index) => (
                  <button
                    key={index + 1}
                    onClick={() => setCurrentPageAll(index + 1)}
                    className={currentPageAll === index + 1 ? "active" : ""}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {showNonAuthMaps && isTableVisible && ( // Check if the table should be visible
        <div className="table-container">
          <h2 className='Table-heading'>Accept Maps</h2>
          {nonMaps.length === 0 ? (
            <p>No maps pending Acceptance.</p>
          ) : (
            <div>
              <table>
                <thead>
                  <tr>
                    <th>Organization</th>
                    <th>Email</th>
                    <th>Map name</th>
                    <th>Location</th>
                    <th>Spots</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {currentRowsMaps.map((Map) => (
                    <tr key={Map.id}>
                      <td>{Map.org}</td>
                      <td>{Map.email}</td>
                      <td>{Map.name}</td>
                      <td><a href={Map.loc}> Location</a></td>
                      <td><button className="Opbutton" onClick={() => handleEditMap(Map.id)}>Show Parking Spots</button></td>
                      <td>
                        <button onClick={() => openModalM(Map, 'accept')}>Accept</button> {/* Delete button */}
                        <button onClick={() => openModalM(Map, 'reject')}>Reject</button> {/* Delete button */}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="pagination">
                {Array.from({ length: totalPagesMaps }, (_, index) => (
                  <button
                    key={index + 1}
                    onClick={() => setCurrentPageMaps(index + 1)}
                    className={currentPageMaps === index + 1 ? "active" : ""}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}


      {showAllAutMaps && isTableVisible && ( // Check if the table should be visible
        <div className="table-container">
          <h2 className='Table-heading'>All Accepted Maps</h2>
          {allMaps.length === 0 ? (
            <p>No accepted maps available for deletion.</p>
          ) : (
            <div>
              <table>
                <thead>
                  <tr>
                    <th>Organization</th>
                    <th>Email</th>
                    <th>Map name</th>
                    <th>Location</th>
                    <th>Spots</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {currentRowsAllMaps.map((Map) => (
                    <tr key={Map.id}>
                      <td>{Map.org}</td>
                      <td>{Map.email}</td>
                      <td>{Map.name}</td>
                      <td><a href={Map.loc}> Location</a></td>
                      <td><button className="Opbutton" onClick={() => handleEditMap(Map.id)}>Show</button></td>
                      <td>

                        <button onClick={() => openModalM(Map, 'delete')}>Delete</button> {/* Delete button */}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="pagination">
                {Array.from({ length: totalPagesAllMaps }, (_, index) => (
                  <button
                    key={index + 1}
                    onClick={() => setCurrentPageAllMaps(index + 1)}
                    className={currentPageAllMaps === index + 1 ? "active" : ""}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!isTableVisible && showMap && (
        <>
          <div className="map-view-container3">
            <button className="back-button" onClick={handleBack}>
              Back
            </button>

            <div className="table-cont3">
              {loadingM ? (
                <LoadingIndicator />
              ) : (
                <div className="centerre3">
                  {parkingSpots.length > 0 ? (
                    <table>
                      <tbody>
                        {[...Array(Math.max(...parkingSpots.map(spot => spot.y_axis)) + 1)].map((_, row) => (
                          <tr key={row}>
                            {[...Array(Math.max(...parkingSpots.map(spot => spot.x_axis)) + 1)].map((_, col) => {
                              const spot = parkingSpots.find(s => s.x_axis === col && s.y_axis === row);
                              return (
                                <td
                                  className={getSpotClasses(spot)}
                                  key={col}
                                  style={{
                                    width: '20px',
                                    height: '50px',
                                    ...(spot ? getBorderStyle(spot, parkingSpots) : { border: "1px solid #000" }),
                                    ...(spot && spot.status === 'sensor' ? { 
                                        backgroundColor: getColorByStatus(spot.status, spot.sensor_status)
                                    } : {})
                                  }}
                                >
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="Gmessage">No parking spots available.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      <ConfirmationModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setIsTableVisible(true); // Show the table again if modal is closed
        }}
        onConfirm={handleConfirm}
        operatorDetails={currentOperator}
        actionType={actionType} // Pass the action type to the modal
      />
      <Confmodal
        isOpen={isModalOpenM}
        onClose={() => {
          setIsModalOpenM(false);
          setIsTableVisible(true); // Show the table again if modal is closed
        }}
        onConfirm={handleConfirmM}
        mapDetails={currentMap}
        actionType={actionTypeM} // Pass the action type to the modal
      />
    </div>
  );
};

export default AdminDashboard;
