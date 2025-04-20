import axios from "axios";
import { ACCESS_TOKEN } from "./constants";

// Define the base URL
const apiUrl = "/choreo-apis/awbo/backend/rest-api-be2/v1.0";
export const API_BASE_URL = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL : apiUrl;

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(ACCESS_TOKEN);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
