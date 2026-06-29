import axios from "axios";

const apiBase = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "/api/v1";

const client = axios.create({
  baseURL: apiBase,
  headers: { "Content-Type": "application/json" },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
