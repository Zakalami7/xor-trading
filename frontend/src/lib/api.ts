import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// Create axios instance
const api = axios.create({
    baseURL: `${API_BASE_URL}/api/v1`,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                try {
                    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
                        refresh_token: refreshToken,
                    });

                    const { access_token, refresh_token } = response.data;
                    localStorage.setItem('access_token', access_token);
                    localStorage.setItem('refresh_token', refresh_token);

                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    return api(originalRequest);
                } catch (refreshError) {
                    // Refresh failed - logout
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login';
                }
            }
        }

        return Promise.reject(error);
    }
);

// Auth
export const authApi = {
    login: (email: string, password: string, mfaCode?: string) =>
        api.post('/auth/login', { email, password, mfa_code: mfaCode }),
    register: (data: { email: string; username: string; password: string; full_name?: string }) =>
        api.post('/auth/register', data),
    logout: () => api.post('/auth/logout'),
    changePassword: (currentPassword: string, newPassword: string) =>
        api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),
    setupMfa: () => api.post('/auth/mfa/setup'),
    verifyMfa: (code: string) => api.post('/auth/mfa/verify', { code }),
    disableMfa: (code: string) => api.post('/auth/mfa/disable', { code }),
};

// User
export const userApi = {
    getMe: () => api.get('/users/me'),
    updateMe: (data: any) => api.patch('/users/me', data),
    updateRiskSettings: (settings: any) => api.patch('/users/me/risk-settings', settings),
};

// Bots
export const botsApi = {
    list: (params?: { status?: string; page?: number }) => api.get('/bots', { params }),
    get: (id: string) => api.get(`/bots/${id}`),
    create: (data: any) => api.post('/bots', data),
    update: (id: string, data: any) => api.patch(`/bots/${id}`, data),
    delete: (id: string) => api.delete(`/bots/${id}`),
    action: (id: string, action: string, reason?: string) =>
        api.post(`/bots/${id}/action`, { action, reason }),
    getLogs: (id: string, limit?: number) => api.get(`/bots/${id}/logs`, { params: { limit } }),
};

// Strategies
export const strategiesApi = {
    list: (type?: string) => api.get('/strategies', { params: { strategy_type: type } }),
    get: (id: string) => api.get(`/strategies/${id}`),
    getSchema: (type: string) => api.get(`/strategies/type/${type}/schema`),
    validate: (type: string, params: any) => api.post('/strategies/validate', { strategy_type: type, params }),
};

// Orders
export const ordersApi = {
    list: (params?: { bot_id?: string; status?: string; symbol?: string }) =>
        api.get('/orders', { params }),
    getActive: () => api.get('/orders/active'),
    get: (id: string) => api.get(`/orders/${id}`),
    cancel: (id: string) => api.post(`/orders/${id}/cancel`),
    cancelAll: (params?: { bot_id?: string; symbol?: string }) =>
        api.post('/orders/cancel-all', params),
    getStats: (params?: { bot_id?: string; period?: string }) =>
        api.get('/orders/stats/summary', { params }),
};

// Positions
export const positionsApi = {
    list: (params?: { bot_id?: string; status?: string }) =>
        api.get('/positions', { params }),
    getOpen: () => api.get('/positions/open'),
    get: (id: string) => api.get(`/positions/${id}`),
    close: (id: string) => api.post(`/positions/${id}/close`),
};

// Exchanges
export const exchangesApi = {
    getSupported: () => api.get('/exchanges/supported'),
    listCredentials: () => api.get('/exchanges/credentials'),
    createCredential: (data: any) => api.post('/exchanges/credentials', data),
    deleteCredential: (id: string) => api.delete(`/exchanges/credentials/${id}`),
};

// Analytics
export const analyticsApi = {
    getDashboard: () => api.get('/analytics/dashboard'),
    getPnl: (params?: { period?: string; bot_id?: string }) =>
        api.get('/analytics/pnl', { params }),
    getBotPerformance: (botId: string) => api.get(`/analytics/performance/${botId}`),
};

export default api;
