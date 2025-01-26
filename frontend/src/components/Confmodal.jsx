import React from 'react';
import "../styles/AdminDashboard.css";

const Confmodal = ({ isOpen, onClose, onConfirm, mapDetails, actionType }) => {
    if (!isOpen) return null;


    const actionMessage = actionType === 'delete'
        ? 'Do you want to delete this map?'
        : actionType === 'reject'
            ? 'Do you want to reject this map?'
            : actionType === 'accept'
                ? 'Do you want to accept this map?'
                : '';

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2>Confirm Action</h2>
                <p>{actionMessage}</p>
                <p>Organization: {mapDetails?.org}</p>
                <p>Operator Email: {mapDetails?.email}</p>
                <p>Map Name: {mapDetails?.name}</p>
                <button onClick={onConfirm}>Yes</button>
                <button onClick={onClose}>No</button>
            </div>
        </div>
    );
};

export default Confmodal;
