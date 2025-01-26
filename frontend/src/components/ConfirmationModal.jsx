import React from 'react';
import "../styles/AdminDashboard.css";

const ConfirmationModal = ({ isOpen, onClose, onConfirm, operatorDetails, actionType }) => {
    if (!isOpen) return null;


    const actionMessage = actionType === 'delete'
        ? 'Do you want to delete this operator?'
        : actionType === 'reject'
            ? 'Do you want to reject this operator?'
            : actionType === 'accept'
                ? 'Do you want to accept this operator?'
                : '';

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2>Confirm Action</h2>
                <p>{actionMessage}</p>
                <p>Name: {operatorDetails?.organization}</p>
                <p>Email: {operatorDetails?.email}</p>
                <p>Phone Number: {operatorDetails?.phone_number}</p>
                <button onClick={onConfirm}>Yes</button>
                <button onClick={onClose}>No</button>
            </div>
        </div>
    );
};

export default ConfirmationModal;
