import React from "react";
import "../styles/Home.css";

const Confmodal3 = ({ isOpen, onClose, onConfirm, message }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Confirm Action</h2>
        <p>{message}</p>
        
          <button className="Opbutton" onClick={onConfirm}>
            Confirm
          </button>
          <button className="Opbutton" onClick={onClose}>
            Cancel
          </button>
        
      </div>
    </div>
  );
};

export default Confmodal3;