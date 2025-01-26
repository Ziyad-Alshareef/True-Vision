import React, { useState } from 'react';
import api from "../api";
import "../styles/ForgotPass.css";
import LoadingIndicator from "../components/LoadingIndicator";

function ForgotPassword() {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [pinSent, setPinSent] = useState(false);
    const [pin, setPin] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [passwordChanged, setPasswordChanged] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSendPin = async () => {
        try {
            setLoading(true);
            const response = await api.post("/api/forgot-password/", { email });
            setMessage(response.data.message);
            setPinSent(true);
            setLoading(false);
        } catch (error) {
            setMessage(error.response.data.error);
            setLoading(false);
        }
    };

    const handleResetPassword = async () => {
        if (newPassword.length < 8) {
            setMessage("Password must be at least 8 characters long.");
            return;
        }
        if (!/[a-zA-Z]/.test(newPassword)) {
            setMessage("Password must contain at least one letter.");
            return;
        }
        try {
            setLoading(true);
            const response = await api.post('/api/reset-password/', { email, pin, new_password: newPassword });
            setMessage("");
            setPasswordChanged(true);
            setLoading(false);
        } catch (error) {
            setMessage(error.response.data.error);
            setLoading(false);
        }
    };

    return (
        <div className="forgot-password-container">
            <div className="forgot-password-box">
                <h2>Forgot Password</h2>
                {!pinSent ? (
                    <div className="input-group">
                        <label>Email:</label>
                        <input
                            type="email"
                            className="forgot-password-input"
                            value={email.toLowerCase()}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                        {loading && <LoadingIndicator />}
                        <button className="forgot-password-button" onClick={handleSendPin}>Send PIN</button>
                    </div>
                ) : !passwordChanged ? (
                    <div className="input-group">
                        <label>PIN:</label>
                        <input
                            type="text"
                            className="forgot-password-input"
                            value={pin}
                            onChange={(e) => setPin(e.target.value)}
                        />
                        <label>New Password:</label>
                        <input
                            type="password"
                            className="forgot-password-input"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                        />
                        {loading && <LoadingIndicator />}
                        <button className="forgot-password-button" onClick={handleResetPassword}>Reset Password</button>
                    </div>
                ) : (
                    <h4>Password reset successfully!😊</h4>
                )}
                {/*passwordChanged && <p>{message}</p>*/}
                {message && <p>{message}</p>}
            </div>
            <div className="forgot-password-image"></div>
        </div>
    );
}

export default ForgotPassword;
