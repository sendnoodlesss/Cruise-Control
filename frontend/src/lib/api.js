import axios from "axios";

export const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";
export const API_BASE = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API_BASE,
});

export const listPathways = () =>
  api.get("/pathways").then((r) => r.data);

export const createPathway = (payload) =>
  api.post("/pathways", payload).then((r) => r.data);

export const getPathway = (id) =>
  api.get(`/pathways/${id}`).then((r) => r.data);

export const updatePathway = (id, payload) =>
  api.put(`/pathways/${id}`, payload).then((r) => r.data);

export const deletePathway = (id) =>
  api.delete(`/pathways/${id}`).then((r) => r.data);

export const uploadResume = (id, file) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post(`/pathways/${id}/resume`, fd).then((r) => r.data);
};

export const addEmailProvider = (id, payload) =>
  api.post(`/pathways/${id}/email-providers`, payload).then((r) => r.data);

export const listEmailProviders = (id) =>
  api.get(`/pathways/${id}/email-providers`).then((r) => r.data);

export const deleteEmailProvider = (id) =>
  api.delete(`/email-providers/${id}`).then((r) => r.data);

export const runPathway = (id) =>
  api.post(`/pathways/${id}/run`).then((r) => r.data);

export const getStatus = (id) =>
  api.get(`/pathways/${id}/status`).then((r) => r.data);

export const getInternships = (id) =>
  api.get(`/pathways/${id}/internships`).then((r) => r.data);

export const getUnlisted = (id) =>
  api.get(`/pathways/${id}/unlisted-companies`).then((r) => r.data);

export const getEmailDrafts = (id) =>
  api.get(`/pathways/${id}/email-drafts`).then((r) => r.data);

export const updateEmail = (id, payload) =>
  api.put(`/email-drafts/${id}`, payload).then((r) => r.data);

export const removeEmail = (id) =>
  api.delete(`/email-drafts/${id}`).then((r) => r.data);

export const sendEmails = (id, emailIds) =>
  api.post(`/pathways/${id}/send-emails`, { email_ids: emailIds }).then((r) => r.data);

export const getStats = () =>
  api.get("/stats").then((r) => r.data);

export const getAnalytics = () =>
  api.get("/analytics").then((r) => r.data);

export const getIntegrationsStatus = () =>
  api.get("/integrations/status").then((r) => r.data);

export const getModelCatalogue = () =>
  api.get("/models/catalogue").then((r) => r.data);

export const exportInternshipsUrl = (id) =>
  `${API_BASE}/pathways/${id}/export-internships`;

export const exportUnlistedUrl = (id) =>
  `${API_BASE}/pathways/${id}/export-unlisted`;