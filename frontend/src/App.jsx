import React, { useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Operator from './pages/Operator';
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminDashboard from "./pages/AdminDashboard";
import ForgotPassword from "./pages/ForgotPassword";
import Body1 from "./pages/Body1";
import Organizations from "./pages/Organizations";
import { AuthContext, AuthProvider } from "./components/AuthContext"; // Import AuthContext and AuthProvider

function Logout() {
  const { setIsLoggedIn } = useContext(AuthContext); // Use AuthContext
  localStorage.clear();
  setIsLoggedIn(false); // Update AuthContext
  return <Navigate to="/" />;
}

function RegisterAndLogout() {
  localStorage.clear();
  return <Register />;
}

function Navbar() {
  const { isLoggedIn, userRole } = useContext(AuthContext);

  console.log("Is Logged In:", isLoggedIn); // Debugging log

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <span className="logo">
          <a href="/">
            <img src="./public/logo.png" alt="Mawaqef Logo" className="logo-image" />
          </a>
        </span>
      </div>
      <div className="navbar-right">
        {userRole === 'admin' ? (
          <a href="/AdminDashboard">Admin Dashboard</a>
        ) : userRole === 'operator' ? (
          <a href="/operator">Operator Dashboard</a>
        ) : (
          <a href="/Organizations">Organizations</a>
        )}
        {isLoggedIn ? (
          <a href="/logout">Sign Out</a>
        ) : (
          <>
            <a href="/login">Sign In</a>
            <a href="/register">Sign Up</a>
          </>
        )}
      </div>
    </nav>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<Body1 />} />
          <Route
            path="/operator"
            element={
              <ProtectedRoute>
                <Operator />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<Login />} />
          <Route path="/forgotpass" element={<ForgotPassword />} />
          <Route path="/AdminDashboard" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
          <Route path="/logout" element={<Logout />} />
          <Route path="/register" element={<RegisterAndLogout />} />
          <Route path="/Organizations" element={<Organizations />} />
          <Route path="*" element={<NotFound />}></Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
