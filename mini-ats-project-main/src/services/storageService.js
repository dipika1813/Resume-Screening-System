// Storage Service / Data Access Layer
// Phase 2: data now lives in MySQL (through the Express backend).
// Reads are instant (from a memory copy loaded at startup).
// Writes update the memory copy immediately AND are sent to MySQL in the background.
// All function names are the same as before, so the screens keep working.

import { calculateMatchScore } from './matchingService';

const API = 'http://localhost:5000/api';
const ACTIVE_USER_KEY = 'mini_ats_active_user';

// In-memory copy of the database tables
const cache = { users: [], jobs: [], skills: [], applications: [] };

// ---------- network helpers ----------
async function request(method, path, body) {
  const res = await fetch(API + path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

// Background writes run one after another, so order is always correct
let queue = Promise.resolve();
function enqueue(method, path, body) {
  queue = queue.then(() =>
    request(method, path, body).catch((err) =>
      console.error(`[MySQL sync failed] ${method} ${path} -> ${err.message}`)
    )
  );
  return queue;
}

// ---------- converters (MySQL column names <-> frontend names) ----------
const isoDate = (s) => (s ? String(s).replace(' ', 'T') : s);
const toMysqlDate = (d) => {
  if (!d) return null;
  const x = new Date(d);
  return isNaN(x) ? null : x.toISOString().slice(0, 19).replace('T', ' ');
};
const parseList = (v) => {
  if (Array.isArray(v)) return v;
  try { return JSON.parse(v) || []; } catch { return []; }
};
const initialsOf = (name) =>
  (name || 'CO').split(' ').filter(Boolean).map((w) => w[0]).join('').substring(0, 2).toUpperCase();

function userFromApi(u) {
  return {
    id: u.id,
    name: u.name,
    email: u.email,
    role: u.role,
    companyName: u.company_name || '',
    phone: u.phone || '',
    location: u.location || '',
    education: u.education || '',
    degree: u.degree || '',
    graduationYear: u.graduation_year || '',
    experienceYears: Number(u.experience_years) || 0,
    bio: u.bio || '',
    skills: u.skills || [],
    resumeFile: u.resume_file_name
      ? { name: u.resume_file_name, size: u.resume_file_size, uploadedAt: isoDate(u.resume_uploaded_at) }
      : null,
    createdAt: isoDate(u.created_at),
    updatedAt: isoDate(u.updated_at),
  };
}

function jobFromApi(j) {
  return {
    id: j.id,
    recruiterId: j.recruiter_id,
    companyName: j.company_name,
    companyInitials: initialsOf(j.company_name),
    title: j.title,
    location: j.location,
    type: j.job_type,
    minExperience: j.min_experience,
    description: j.description,
    requiredSkills: j.skills || [],
    threshold: j.threshold,
    deadline: j.deadline ? String(j.deadline).slice(0, 10) : '',
    salary: j.salary || 'Best in Industry',
    status: j.status,
    createdAt: isoDate(j.created_at),
    updatedAt: isoDate(j.updated_at),
  };
}

function appFromApi(a) {
  return {
    id: a.id,
    jobId: a.job_id,
    candidateId: a.candidate_id,
    candidateName: a.candidate_name,
    candidateEmail: a.candidate_email,
    appliedDate: isoDate(a.applied_date),
    status: a.status,
    matchScore: a.match_score,
    matchedSkills: parseList(a.matched_skills),
    missingSkills: parseList(a.missing_skills),
    notes: a.notes || '',
    updatedAt: isoDate(a.updated_at),
  };
}

function userUpdatesToApi(u) {
  const map = {
    name: 'name', companyName: 'company_name', phone: 'phone', location: 'location',
    education: 'education', degree: 'degree', graduationYear: 'graduation_year',
    bio: 'bio', skills: 'skills',
  };
  const out = {};
  for (const [k, v] of Object.entries(map)) if (u[k] !== undefined) out[v] = u[k];
  if (u.experienceYears !== undefined) out.experience_years = Number(u.experienceYears) || 0;
  if (u.resumeFile !== undefined) {
    const r = u.resumeFile;
    out.resume_file_name = r ? r.name || r.fileName || null : null;
    out.resume_file_size = r && r.size != null ? String(r.size) : null;
    out.resume_uploaded_at = r ? toMysqlDate(r.uploadedAt || r.uploadDate) : null;
  }
  return out;
}

// ---------- LOAD DATA FROM MYSQL (called once when the app starts) ----------
export async function initStorage() {
  const data = await request('GET', '/bootstrap');
  cache.users = data.users.map(userFromApi);
  cache.jobs = data.jobs.map(jobFromApi);
  cache.skills = data.skills.map((s) => ({ id: s.id, name: s.name, category: s.category }));
  cache.applications = data.applications.map(appFromApi);
}

// --- AUTH (these two are async: use await) ---

export async function loginUser(email, password) {
  const u = await request('POST', '/auth/login', { email, password });
  const user = userFromApi(u);
  const i = cache.users.findIndex((x) => x.id === user.id);
  if (i === -1) cache.users.push(user); else cache.users[i] = user;
  return user;
}

export async function createUser(userData) {
  const id = `usr-${Date.now()}`;
  const email = userData.email.toLowerCase().trim();
  await request('POST', '/auth/register', {
    id,
    name: userData.name,
    email,
    password: userData.password,
    role: userData.role || 'candidate',
    company_name: userData.companyName || '',
    phone: userData.phone || '',
    location: userData.location || '',
  });

  const newUser = {
    id,
    name: userData.name,
    email,
    role: userData.role || 'candidate',
    companyName: userData.companyName || '',
    phone: userData.phone || '',
    location: userData.location || '',
    education: userData.education || '',
    degree: userData.degree || '',
    graduationYear: userData.graduationYear || '',
    experienceYears: Number(userData.experienceYears) || 0,
    bio: userData.bio || '',
    skills: userData.skills || [],
    resumeFile: userData.resumeFile || null,
    createdAt: new Date().toISOString(),
  };

  // save the extra profile fields + skills
  await request('PUT', `/users/${id}`, userUpdatesToApi({
    education: newUser.education, degree: newUser.degree, graduationYear: newUser.graduationYear,
    experienceYears: newUser.experienceYears, bio: newUser.bio, skills: newUser.skills,
    resumeFile: newUser.resumeFile,
  }));

  cache.users.push(newUser);
  return newUser;
}

// --- USER OPERATIONS ---

export function getUsers() {
  return cache.users;
}

export function getUserById(id) {
  return cache.users.find((u) => u.id === id) || null;
}

export function getUserByEmail(email) {
  return cache.users.find((u) => u.email.toLowerCase() === (email || '').toLowerCase().trim()) || null;
}

export function updateUser(id, updates) {
  const index = cache.users.findIndex((u) => u.id === id);
  if (index === -1) throw new Error('User not found.');

  cache.users[index] = { ...cache.users[index], ...updates, updatedAt: new Date().toISOString() };
  const updated = cache.users[index];

  enqueue('PUT', `/users/${id}`, userUpdatesToApi(updates));

  const activeUser = getActiveUser();
  if (activeUser && activeUser.id === id) setActiveUser(updated);

  if (updates.skills || updates.name) syncCandidateApplications(id, updated);
  return updated;
}

// Keep application records in sync when a candidate updates skills
function syncCandidateApplications(candidateId, updatedUser) {
  cache.applications = cache.applications.map((app) => {
    if (app.candidateId !== candidateId) return app;
    const job = cache.jobs.find((j) => j.id === app.jobId);
    if (!job) return app;
    const m = calculateMatchScore(updatedUser.skills || [], job.requiredSkills || []);
    const next = {
      ...app,
      candidateName: updatedUser.name || app.candidateName,
      matchScore: m.score,
      matchedSkills: m.matchedSkills,
      missingSkills: m.missingSkills,
      status: m.score >= (job.threshold || 80) ? 'Shortlisted' : app.status,
    };
    enqueue('PUT', `/applications/${app.id}`, {
      status: next.status,
      match_score: next.matchScore,
      matched_skills: next.matchedSkills,
      missing_skills: next.missingSkills,
    });
    return next;
  });
}

// --- ACTIVE SESSION (stays in the browser: it is only "who is logged in") ---

export function getActiveUser() {
  try {
    const raw = localStorage.getItem(ACTIVE_USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (err) {
    return null;
  }
}

export function setActiveUser(user) {
  if (!user) localStorage.removeItem(ACTIVE_USER_KEY);
  else localStorage.setItem(ACTIVE_USER_KEY, JSON.stringify(user));
}

export function clearActiveUser() {
  localStorage.removeItem(ACTIVE_USER_KEY);
}

// --- SKILLS ---

export function getSkills() {
  return cache.skills;
}

export function addCustomSkill(skillName, category = 'Custom') {
  if (!skillName || !skillName.trim()) return null;
  const trimmed = skillName.trim();
  const exists = cache.skills.find((s) => s.name.toLowerCase() === trimmed.toLowerCase());
  if (exists) return exists;

  const newSkill = { id: `sk-${Date.now()}`, name: trimmed, category };
  cache.skills.push(newSkill);
  enqueue('POST', '/skills', newSkill);
  return newSkill;
}

// --- JOBS ---

export function getJobs(filters = {}) {
  let jobs = [...cache.jobs];

  if (filters.recruiterId) jobs = jobs.filter((j) => j.recruiterId === filters.recruiterId);
  if (filters.status) jobs = jobs.filter((j) => j.status === filters.status);
  if (filters.type && filters.type !== 'All') {
    jobs = jobs.filter((j) => j.type.toLowerCase() === filters.type.toLowerCase());
  }
  if (filters.search) {
    const q = filters.search.toLowerCase();
    jobs = jobs.filter((j) =>
      j.title.toLowerCase().includes(q) ||
      j.companyName.toLowerCase().includes(q) ||
      j.location.toLowerCase().includes(q) ||
      (j.requiredSkills || []).some((s) => s.toLowerCase().includes(q))
    );
  }
  return jobs;
}

export function getJobById(id) {
  return cache.jobs.find((j) => j.id === id) || null;
}

export function createJob(jobData) {
  const newJob = {
    id: `job-${Date.now()}`,
    recruiterId: jobData.recruiterId || 'usr-recruiter-1',
    companyName: jobData.companyName,
    companyInitials: initialsOf(jobData.companyName),
    title: jobData.title,
    location: jobData.location,
    type: jobData.type || 'Full-Time',
    minExperience: jobData.minExperience || '0-2 years',
    description: jobData.description,
    requiredSkills: jobData.requiredSkills || [],
    threshold: Number(jobData.threshold) || 80,
    deadline: jobData.deadline || '',
    salary: jobData.salary || 'Best in Industry',
    status: jobData.status || 'Active',
    createdAt: new Date().toISOString(),
  };

  cache.jobs.unshift(newJob);
  enqueue('POST', '/jobs', {
    id: newJob.id,
    recruiter_id: newJob.recruiterId,
    company_name: newJob.companyName,
    title: newJob.title,
    location: newJob.location,
    job_type: newJob.type,
    min_experience: newJob.minExperience,
    description: newJob.description,
    threshold: newJob.threshold,
    deadline: newJob.deadline || null,
    salary: newJob.salary,
    status: newJob.status,
    skills: newJob.requiredSkills,
  });
  return newJob;
}

export function updateJob(id, updates) {
  const index = cache.jobs.findIndex((j) => j.id === id);
  if (index === -1) throw new Error('Job not found.');

  cache.jobs[index] = { ...cache.jobs[index], ...updates, updatedAt: new Date().toISOString() };

  const map = {
    title: 'title', companyName: 'company_name', location: 'location', type: 'job_type',
    minExperience: 'min_experience', description: 'description', salary: 'salary',
    status: 'status', requiredSkills: 'skills',
  };
  const body = {};
  for (const [k, v] of Object.entries(map)) if (updates[k] !== undefined) body[v] = updates[k];
  if (updates.threshold !== undefined) body.threshold = Number(updates.threshold) || 80;
  if (updates.deadline !== undefined) body.deadline = updates.deadline || null;
  enqueue('PUT', `/jobs/${id}`, body);

  return cache.jobs[index];
}

export function deleteJob(id) {
  cache.jobs = cache.jobs.filter((j) => j.id !== id);
  cache.applications = cache.applications.filter((a) => a.jobId !== id);
  enqueue('DELETE', `/jobs/${id}`);
}

// --- APPLICATIONS ---

export function getApplications(filters = {}) {
  let apps = [...cache.applications];

  if (filters.jobId) apps = apps.filter((a) => a.jobId === filters.jobId);
  if (filters.candidateId) apps = apps.filter((a) => a.candidateId === filters.candidateId);
  if (filters.status && filters.status !== 'All') {
    apps = apps.filter((a) => a.status.toLowerCase() === filters.status.toLowerCase());
  }
  return apps;
}

export function getApplicationById(id) {
  return cache.applications.find((a) => a.id === id) || null;
}

export function createApplication({ jobId, candidateId, notes = '' }) {
  const existing = cache.applications.find((a) => a.jobId === jobId && a.candidateId === candidateId);
  if (existing) throw new Error('You have already submitted an application for this position.');

  const job = getJobById(jobId);
  const candidate = getUserById(candidateId);
  if (!job || !candidate) throw new Error('Invalid job or candidate reference.');

  const m = calculateMatchScore(candidate.skills || [], job.requiredSkills || []);
  const status = m.score >= (job.threshold || 80) ? 'Shortlisted' : 'Pending';

  const newApp = {
    id: `app-${Date.now()}`,
    jobId: job.id,
    candidateId: candidate.id,
    candidateName: candidate.name,
    candidateEmail: candidate.email,
    appliedDate: new Date().toISOString(),
    status,
    matchScore: m.score,
    matchedSkills: m.matchedSkills,
    missingSkills: m.missingSkills,
    notes: notes || '',
  };

  cache.applications.unshift(newApp);
  enqueue('POST', '/applications', {
    id: newApp.id,
    job_id: job.id,
    candidate_id: candidate.id,
    match_score: newApp.matchScore,
    matched_skills: newApp.matchedSkills,
    missing_skills: newApp.missingSkills,
    status: newApp.status,
    notes: newApp.notes,
  });
  return newApp;
}

export function updateApplicationStatus(id, newStatus, notes) {
  const index = cache.applications.findIndex((a) => a.id === id);
  if (index === -1) throw new Error('Application not found.');

  cache.applications[index] = {
    ...cache.applications[index],
    status: newStatus,
    notes: notes !== undefined ? notes : cache.applications[index].notes,
    updatedAt: new Date().toISOString(),
  };

  const body = { status: newStatus };
  if (notes !== undefined) body.notes = notes;
  enqueue('PUT', `/applications/${id}`, body);

  return cache.applications[index];
}

// Ranked applicants for a job (highest match score first)
export function getRankedCandidates(jobId) {
  const apps = getApplications({ jobId });
  const users = getUsers();

  const ranked = apps.map((app) => {
    const candidate = users.find((u) => u.id === app.candidateId) || {};
    return {
      ...app,
      candidateProfile: candidate,
      education: candidate.education || 'N/A',
      experienceYears: candidate.experienceYears || 0,
      skills: candidate.skills || [],
      phone: candidate.phone || '',
      resumeFile: candidate.resumeFile || null,
    };
  });

  ranked.sort((a, b) => {
    if (b.matchScore !== a.matchScore) return b.matchScore - a.matchScore;
    return new Date(b.appliedDate) - new Date(a.appliedDate);
  });

  return ranked.map((item, idx) => ({ ...item, rank: idx + 1 }));
}

// Demo helper: logs out and reloads data from MySQL
export function resetToInitialData() {
  localStorage.removeItem(ACTIVE_USER_KEY);
  initStorage();
  return true;
}