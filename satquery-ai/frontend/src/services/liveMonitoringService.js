import api from './api';

export const liveMonitoringService = {
    async getActiveJobs() {
        const response = await api.get('/api/monitoring/active');
        return response.data;
    },

    async getJobStatus(jobId) {
        const response = await api.get(`/api/monitoring/status/${jobId}`);
        return response.data;
    },

    async getHistory(jobId) {
        const response = await api.get(`/api/monitoring/history/${jobId}`);
        return response.data.history;
    },

    async getAllEvents() {
        const response = await api.get('/api/monitoring/events');
        return response.data;
    },

    async startMonitoring(lat, lon, radius, type) {
        const response = await api.post('/api/monitoring/start', {
            latitude: lat,
            longitude: lon,
            radius_km: radius,
            monitoring_type: type,
            frequency: 'fast_demo'
        });
        return response.data;
    },

    async triggerCheck(jobId) {
        const response = await api.post(`/api/monitoring/${jobId}/check`);
        return response.data;
    }
};
