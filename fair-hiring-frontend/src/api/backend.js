// Dynamically use the current hostname for local dev, allowing access from network devices (e.g. phones on 172.x.x.x)
let envBase = import.meta.env.VITE_BACKEND_URL;
if (envBase && envBase.includes('localhost') && window.location.hostname !== 'localhost') {
  envBase = `http://${window.location.hostname}:8012`;
}
const BASE = envBase || `http://${window.location.hostname}:8012`;
console.log("Using Backend URL:", BASE);

// Auth token management
// Call setAuthToken(token) after Auth0 login so all subsequent API calls include
// the Bearer token. The token is never persisted to localStorage.
let _authToken = null;
export function setAuthToken(token) { _authToken = token; }
export function getAuthToken() { return _authToken; }

async function request(path, options) {
  const isFormData = options?.body instanceof FormData;

  const headers = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    // Attach Auth0 Bearer token if available
    ...(_authToken ? { Authorization: `Bearer ${_authToken}` } : {}),
    ...(options?.headers || {}),
  };

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  });

  let data = null;
  try {
    data = await res.json();
  } catch { }

  if (!res.ok) {
    const msg = data?.detail || data?.error || data?.message || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

export const api = {
  candidateSignup: (payload) =>
    request("/auth/candidate/signup", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  candidateLogin: (payload) =>
    request("/auth/candidate/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  // Auth0 integration: called after Auth0 redirect, syncs the DB row
  auth0SyncCandidate: () =>
    request("/auth/candidate/auth0-sync", {
      method: "POST",
    }),
  companySignup: (payload) =>
    request("/auth/company/signup", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  companyLogin: (payload) =>
    request("/auth/company/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listPublishedJobs: () => request("/candidate/jobs", { method: "GET" }),
  listCompanyJobs: (companyId) =>
    request(`/company/${companyId}/jobs`, { method: "GET" }),

  createJob: (payload) =>
    request("/company/job", { method: "POST", body: JSON.stringify(payload) }),
  deleteJob: (companyId, jobId) =>
    request(`/company/${companyId}/jobs/${jobId}`, { method: "DELETE" }),

  // Candidate
  applyToJob: (formData) =>
    request("/candidate/apply", {
      method: "POST",
      body: formData // Expects FormData now
    }),

  getApplicationStatus: (applicationId) =>
    request(`/candidate/application/${applicationId}/status`, { method: "GET" }),

  submitTestResults: (applicationId, formData) =>
    request(`/candidate/application/${applicationId}/submit-test`, {
      method: "POST",
      body: formData
    }),

  getCandidateStats: (anonId) =>
    request(`/candidate/${encodeURIComponent(anonId)}/stats`, { method: "GET" }),
  listCandidateApplications: (anonId) =>
    request(`/candidate/${encodeURIComponent(anonId)}/applications`, { method: "GET" }),

  // Company
  getCompanyStats: (companyId) =>
    request(`/company/${companyId}/stats`, { method: "GET" }),
  runMatching: (companyId, jobId) =>
    request(`/company/${companyId}/jobs/${jobId}/run-matching`, { method: "POST" }),
  listJobApplications: (companyId, jobId) =>
    request(`/company/${companyId}/jobs/${jobId}/applications`, { method: "GET" }),
  decideApplications: (companyId, jobId, applicationIds, action, note) =>
    request(`/company/${companyId}/jobs/${jobId}/applications/decision`, {
      method: "POST",
      body: JSON.stringify({ application_ids: applicationIds, action, note }),
    }),
  autoFinalizeJob: (companyId, jobId) =>
    request(`/company/${companyId}/jobs/${jobId}/auto-finalize`, {
      method: "POST",
    }),
  listSelected: (companyId, jobId) =>
    request(`/company/${companyId}/jobs/${jobId}/selected`, { method: "GET" }),
  reviewQueue: (companyId) =>
    companyId
      ? request(`/company/${companyId}/review-queue`, { method: "GET" })
      : request(`/company/reviewer/queue`, { method: "GET" }),
  reviewAction: (companyId, caseId, payload) =>
    companyId
      ? request(`/company/${companyId}/review-queue/${caseId}/action`, {
          method: "POST",
          body: JSON.stringify(payload),
        })
      : request(`/company/reviewer/queue/${caseId}/action`, {
          method: "POST",
          body: JSON.stringify(payload),
        }),

  // Passport
  getPassport: (anonId) =>
    request(`/passport/${encodeURIComponent(anonId)}`, { method: "GET" }),
  verifyPassport: (payload) =>
    request("/passport/verify", { method: "POST", body: JSON.stringify(payload) }),

  // Agents
  analyzeJobDescription: (description) =>
    request("/company/analyze_bias", {
      method: "POST",
      body: JSON.stringify({ description }),
    }),
};
