import React, { createContext, useState, useEffect } from 'react';
import { ACCESS_TOKEN } from '../constants';
import api from '../api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem(ACCESS_TOKEN));
    const [userRole, setUserRole] = useState(null);

    useEffect(() => {
        const fetchUserRole = async () => {
            const accessToken = localStorage.getItem(ACCESS_TOKEN);
            if (accessToken) {
                try {
                    const res = await api.get("/api/user/", {
                        headers: {
                            Authorization: `Bearer ${accessToken}`,
                        },
                    });
                    setUserRole(res.data.role);
                } catch (error) {
                    console.error("Error fetching user role:", error);
                }
            }
        };

        fetchUserRole();

        const handleStorageChange = () => {
            setIsLoggedIn(!!localStorage.getItem(ACCESS_TOKEN));
            fetchUserRole();
        };

        window.addEventListener('storage', handleStorageChange);

        return () => {
            window.removeEventListener('storage', handleStorageChange);
        };
    }, []);

    return (
        <AuthContext.Provider value={{ isLoggedIn, setIsLoggedIn, userRole, setUserRole }}>
            {children}
        </AuthContext.Provider>
    );
};