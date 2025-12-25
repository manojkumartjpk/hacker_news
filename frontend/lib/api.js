import axios from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

// Request interceptor to add CSRF token for unsafe methods.
api.interceptors.request.use((config) => {
  const method = config.method?.toUpperCase();
  if (method && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrfToken = Cookies.get('csrf_token');
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }
  }
  return config;
});

// Response interceptor to handle token refresh or logout
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('auth_status');
      Cookies.remove('csrf_token');
      // Redirect to login if on client side
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (userData) => api.post('/auth/register', userData),
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  usernameAvailable: (username) => api.get('/auth/username-available', { params: { username } }),
  me: () => api.get('/auth/me'),
};

export const postsAPI = {
  getPosts: (params) => api.get('/posts/', { params }),
  searchPosts: (params) => api.get('/posts/search', { params }),
  getPost: (id) => api.get(`/posts/${id}`),
  createPost: (postData) => api.post('/posts/', postData),
  updatePost: (id, postData) => api.put(`/posts/${id}`, postData),
  deletePost: (id) => api.delete(`/posts/${id}`),
  vote: (postId, voteData) => api.post(`/posts/${postId}/vote`, voteData),
  getVote: (postId) => api.get(`/posts/${postId}/vote`),
  unvote: (postId) => api.delete(`/posts/${postId}/vote`),
};

export const commentsAPI = {
  getComments: (postId) => api.get(`/posts/${postId}/comments`),
  getComment: (commentId) => api.get(`/comments/${commentId}`),
  createComment: (postId, commentData) => api.post(`/posts/${postId}/comments`, commentData),
  updateComment: (commentId, commentData) => api.put(`/comments/${commentId}`, commentData),
  deleteComment: (commentId) => api.delete(`/comments/${commentId}`),
  getRecentComments: (params) => api.get('/comments/recent', { params }),
  vote: (commentId, voteData) => api.post(`/comments/${commentId}/vote`, voteData),
  getVote: (commentId) => api.get(`/comments/${commentId}/vote`),
  unvote: (commentId) => api.delete(`/comments/${commentId}/vote`),
};

export const notificationsAPI = {
  getNotifications: (params) => api.get('/notifications/', { params }),
  markAsRead: (id) => api.put(`/notifications/${id}/read`),
  getUnreadCount: () => api.get('/notifications/unread/count'),
};

export default api;
