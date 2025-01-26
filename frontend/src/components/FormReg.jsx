import React, { useState } from 'react';
import api from "../api";
import "../styles/Form.css";

const FormReg = ({ route, method }) => {
    const [formData, setFormData] = useState({
        organization: '',
        email: '',
        phone_number: '',
        password: '',
        confirmPassword: '' // Added confirmPassword field
    });

    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setSuccess(null);

        // Password policy checks
        if (formData.phone_number.length != 10) {
            setError("Phone number must be 10 digits long.");
            return;
        }
        if (formData.email.length < 1) {
            setError("Email cannot be empty.");
            return;
        }
        if (formData.password.length < 8) {
            setError("Password must be at least 8 characters long.");
            return;
        }
        if (!/[a-zA-Z]/.test(formData.password)) {
            setError("Password must contain at least one letter.");
            return;
        }
        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        const { confirmPassword, ...dataToSend } = formData; // Exclude confirmPassword

        try {
            const response = await api.post(route, dataToSend);
            if (response.status === 201 || response.status === 200) {
                setSuccess("Operator registered successfully!");
                setFormData({
                    organization: '',
                    email: '',
                    phone_number: '',
                    password: '',
                    confirmPassword: '' // Reset confirmPassword field
                });
            }
        } catch (error) {
            // Handle specific validation errors from the backend
            if (error.response?.data) {
                const errorData = error.response.data;
                if (errorData.organization) {
                    setError(`${errorData.organization[0]}`);
                } else if (errorData.email) {
                    setError(`${errorData.email[0]}`);
                } else {
                    setError("Registration failed. Please try again.");
                }
            } else {
                setError("Registration failed. Please try again.");
            }
    };
    }
    return (
        <div className="reg-form-container">
            <div className="reg-form-box">
                <h2>Register Operator</h2>
                <form onSubmit={handleSubmit}>
                    <div className="reg-input-group">
                        <label htmlFor="organization">Organization:</label>
                        <input
                            className="reg-form-input"
                            type="text"
                            name="organization"
                            value={formData.organization}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div className="reg-input-group">
                        <label htmlFor="email">Email:</label>
                        <input
                            className="reg-form-input"
                            type="email"
                            name="email"
                            value={formData.email.toLowerCase()}
                            onChange={handleChange}
                            
                        />
                    </div>
                    <div className="reg-input-group">
                        <label htmlFor="phone_number">Phone Number:</label>
                        <input
                            className="reg-form-input"
                            type="tel"
                            name="phone_number"
                            value={formData.phone_number}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div className="reg-input-group">
                        <label htmlFor="password">Password:</label>
                        <input
                            className="reg-form-input"
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div className="reg-input-group">
                        <label htmlFor="confirmPassword">Confirm Password:</label>
                        <input
                            className="reg-form-input"
                            type="password"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    {error && <p style={{ color: 'red' }}>{error}</p>}
                    {success && <p style={{ color: 'green' }}>{success}</p>}
                    <button className="reg-form-button" type="submit">Register</button>
                </form>
            </div>
            <div className="reg-form-image" style={{ backgroundImage: "url('../../public/parkingspots-1.png')" }}></div>
        </div>
    );
};

export default FormReg;