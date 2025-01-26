import { useState, useContext } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";
import "../styles/Form.css";
import LoadingIndicator from "./LoadingIndicator";
import { AuthContext } from "./AuthContext"; // Import AuthContext

function Form({ route, method }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { setIsLoggedIn, setUserRole } = useContext(AuthContext); // Use AuthContext
    const [error, setError] = useState(null);
    

    const name = method === "login" ? "Login" : "Register";

    const handleSubmit = async (e) => {
        setLoading(true);
        e.preventDefault();
        setError(null);
        


        try {
            const res = await api.post(route, { email, password });
            if (method === "login") {
                console.log("API Response:", res.data); // Debugging log for API response
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
                console.log("Access Token Set:", localStorage.getItem(ACCESS_TOKEN)); // Debugging log for localStorage
                setIsLoggedIn(true); // Update AuthContext
                setUserRole(res.data.role); // Update user role in AuthContext

                if (res.data.role === 'admin') {
                    navigate("/AdminDashboard");
                } else {
                    navigate("/operator");
                }
            } else {
                navigate("/login");
            }
        } catch (error) {
            if (error.response && error.response.status === 401) {
                setError("Incorrect email or password. Please try again.");
            } else {
                setError("An error occurred. Please try again later.");
                
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="form-container">
            <div className="form-box">
                <h2>{name}</h2>
                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label>Email</label>
                        <input
                            className="form-input"
                            type="email"
                            name="email"
                            value={email.toLowerCase()}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Email"
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label>Password</label>
                        <input
                            className="form-input"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Password"
                            required
                        />
                    </div>
                    {error && <p style={{ color: 'red' }}>{error}</p>}
                    
                    {loading && <LoadingIndicator />}
                    <div><button className="form-button" type="submit">
                        {name}
                    </button></div><br/>
                    <a href="/forgotpass"> Forgot your password?</a>
                </form>
            </div>
            <div className="form-image" style={{ backgroundImage: "url('../../public/parkingspots-1.png')" }}></div>
        </div>
    );
}

export default Form;