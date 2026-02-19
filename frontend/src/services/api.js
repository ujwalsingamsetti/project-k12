import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const register = (data) => api.post('/auth/register', data);
export const login = (data) => api.post('/auth/login', data);
export const getMe = () => api.get('/auth/me');

// Teacher
export const createPaper = (data) => api.post('/teacher/papers', data);
export const createPaperFromImage = (files, title, subject, duration) => {
  const formData = new FormData();
  // Support multiple files
  if (Array.isArray(files)) {
    files.forEach((file) => {
      formData.append('files', file);
    });
  } else {
    formData.append('files', files);
  }
  if (title) formData.append('title', title);
  if (subject) formData.append('subject', subject);
  if (duration) formData.append('duration_minutes', duration);
  return api.post('/teacher/papers/from-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const getMyPapers = () => api.get('/teacher/papers');
export const getPaper = (id) => api.get(`/teacher/papers/${id}`);
export const getPaperSubmissions = (id) => api.get(`/teacher/papers/${id}/submissions`);
export const deletePaper = (id) => api.delete(`/teacher/papers/${id}`);
export const uploadTextbook = (file, title, subject) => {
  const formData = new FormData();
  formData.append('file', file);
  if (title) formData.append('title', title);
  if (subject) formData.append('subject', subject);
  return api.post('/teacher/textbooks', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const getMyTextbooks = () => api.get('/teacher/textbooks');
export const deleteTextbook = (id) => api.delete(`/teacher/textbooks/${id}`);

// Student
export const getTeachers = () => api.get('/student/teachers');
export const getAvailablePapers = (teacherId = null) => {
  const params = teacherId ? { teacher_id: teacherId } : {};
  return api.get('/student/papers', { params });
};
export const getPaperDetails = (id) => api.get(`/student/papers/${id}`);
export const submitAnswer = (paperId, files) => {
  const formData = new FormData();
  // Handle both single file and multiple files
  if (Array.isArray(files)) {
    files.forEach((file) => {
      formData.append('files', file);
    });
  } else {
    formData.append('files', files);
  }
  return api.post(`/student/submit/${paperId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const getMySubmissions = () => api.get('/student/submissions');
export const getSubmissionDetails = (id) => api.get(`/student/submissions/${id}`);
export const getSubmissionImage = (imagePath) => {
  return `http://localhost:8000/uploads/${imagePath}`;
};

export default api;
