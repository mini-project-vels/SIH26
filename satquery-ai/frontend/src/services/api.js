import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const getImageUrl = (pathOrUrl) => {
    if (!pathOrUrl) return null;
    if (pathOrUrl.startsWith('http')) return pathOrUrl;

    // ensure singular slash mapping for relative paths
    const cleanPath = pathOrUrl.replace(/\\/g, '/').replace(/^\//, '');
    return `${API_BASE_URL}/${cleanPath}`;
}

export default api;
