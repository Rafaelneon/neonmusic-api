import axios from 'axios';

const API_BASE = '/api/v1';

export const musicApi = {
    getTracks: (offset = 0, limit = 50) => 
        axios.get(`${API_BASE}/music/tracks`, { params: { offset, limit } }).then(r => r.data),
    
    downloadMusic: (url) => 
        axios.post(`${API_BASE}/music/download`, { url, use_search: true }).then(r => r.data),
    
    getStatus: (taskId) => 
        axios.get(`${API_BASE}/music/status/${taskId}`).then(r => r.data),
};
