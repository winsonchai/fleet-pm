/**
 * FleetPM API Client Module
 */
const API = (() => {
  const BASE_URL = '';

  let token = localStorage.getItem('fleetpm_token') || null;
  let user = JSON.parse(localStorage.getItem('fleetpm_user') || 'null');

  function setAuth(newToken, newUser) {
    token = newToken;
    user = newUser;
    if (token) {
      localStorage.setItem('fleetpm_token', token);
      localStorage.setItem('fleetpm_user', JSON.stringify(newUser));
    } else {
      localStorage.removeItem('fleetpm_token');
      localStorage.removeItem('fleetpm_user');
    }
  }

  function getAuth() {
    return { token, user };
  }

  async function request(path, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const res = await fetch(`${BASE_URL}${path}`, config);

      if (res.status === 401) {
        setAuth(null, null);
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        throw new Error('Session expired or unauthorized. Please log in again.');
      }

      if (res.status === 204) {
        return null;
      }

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || `Request failed with status ${res.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Error on ${path}:`, err);
      throw err;
    }
  }

  return {
    getAuth,
    setAuth,

    // Auth
    async login(email, password) {
      const data = await request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setAuth(data.access_token, data.user);
      return data;
    },

    logout() {
      setAuth(null, null);
    },

    async getMe() {
      const data = await request('/api/auth/me');
      setAuth(token, data);
      return data;
    },

    async getCompanyUsers() {
      return request('/api/auth/users');
    },

    // Dashboard
    async getDashboardStats() {
      return request('/api/dashboard/stats');
    },

    // Vehicles
    async getVehicles(filters = {}) {
      const query = new URLSearchParams();
      if (filters.category_id) query.append('category_id', filters.category_id);
      if (filters.status) query.append('status', filters.status);
      if (filters.q) query.append('q', filters.q);
      const queryString = query.toString() ? `?${query.toString()}` : '';
      return request(`/api/vehicles${queryString}`);
    },

    async getVehicle(id) {
      return request(`/api/vehicles/${id}`);
    },

    async createVehicle(payload) {
      return request('/api/vehicles', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async updateVehicle(id, payload) {
      return request(`/api/vehicles/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    },

    async deleteVehicle(id) {
      return request(`/api/vehicles/${id}`, {
        method: 'DELETE',
      });
    },

    // Projects
    async getProjects(filters = {}) {
      const query = new URLSearchParams();
      if (filters.status) query.append('status', filters.status);
      if (filters.q) query.append('q', filters.q);
      const queryString = query.toString() ? `?${query.toString()}` : '';
      return request(`/api/projects${queryString}`);
    },

    async createProject(payload) {
      return request('/api/projects', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async updateProject(id, payload) {
      return request(`/api/projects/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    },

    async deleteProject(id) {
      return request(`/api/projects/${id}`, {
        method: 'DELETE',
      });
    },

    // Categories
    async getCategories() {
      return request('/api/categories');
    },

    async createCategory(payload) {
      return request('/api/categories', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async updateCategory(id, payload) {
      return request(`/api/categories/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    },

    async deleteCategory(id) {
      return request(`/api/categories/${id}`, {
        method: 'DELETE',
      });
    },

    // Logs & Trips
    async getLogs(filters = {}) {
      const query = new URLSearchParams();
      if (filters.status) query.append('status', filters.status);
      if (filters.vehicle_id) query.append('vehicle_id', filters.vehicle_id);
      if (filters.project_id) query.append('project_id', filters.project_id);
      if (filters.q) query.append('q', filters.q);
      if (filters.days) query.append('days', filters.days);
      if (filters.start_date) query.append('start_date', filters.start_date);
      if (filters.end_date) query.append('end_date', filters.end_date);
      if (filters.limit) query.append('limit', filters.limit);
      const queryString = query.toString() ? `?${query.toString()}` : '';
      return request(`/api/logs${queryString}`);
    },

    async checkoutVehicle(payload) {
      return request('/api/logs/checkout', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async checkinVehicle(logId, payload) {
      return request(`/api/logs/${logId}/checkin`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
  };
})();
