import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Divisions ──────────────────────────────────────────────────────────────
export const getDivisions = ()          => api.get('/divisions/');
export const createDivision = (data)    => api.post('/divisions/', data);
export const deleteDivision = (id)      => api.delete(`/divisions/${id}`);

// ── Subjects ───────────────────────────────────────────────────────────────
export const getSubjects = ()           => api.get('/subjects/');
export const createSubject = (data)     => api.post('/subjects/', data);
export const deleteSubject = (id)       => api.delete(`/subjects/${id}`);

// ── Faculty ────────────────────────────────────────────────────────────────
export const getFaculty = ()            => api.get('/faculty/');
export const createFaculty = (data)     => api.post('/faculty/', data);
export const deleteFaculty = (id)       => api.delete(`/faculty/${id}`);
export const assignFacultySubjects = (id, subjectIds) =>
  api.put(`/faculty/${id}/subjects`, { subject_ids: subjectIds });

// ── Rooms ──────────────────────────────────────────────────────────────────
export const getRooms = ()              => api.get('/rooms/');
export const createRoom = (data)        => api.post('/rooms/', data);
export const deleteRoom = (id)          => api.delete(`/rooms/${id}`);

// ── Timetable ──────────────────────────────────────────────────────────────
export const solveTimetable = ()        => api.post('/timetable/solve');
export const getLatestTimetable = ()    => api.get('/timetable/latest');
export const getDivisionTimetable = (id) => api.get(`/timetable/${id}`);
export const getSolveRuns = ()          => api.get('/timetable/runs');
export const getStats = ()              => api.get('/timetable/stats/overview');

export default api;
