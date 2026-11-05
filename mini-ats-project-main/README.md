# Mini ATS — Resume Screening & Candidate Ranking System

**A Smart Recruitment Platform with Automated Skill Matching and Candidate Ranking**

![Project](https://img.shields.io/badge/Project-DBMS%20Mini%20Project-blue)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB)
![Styling](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC)
![Charts](https://img.shields.io/badge/Charts-Recharts-orange)
![Status](https://img.shields.io/badge/Status-Phase%201%20Prototype-success)

---

## 📌 Project Overview

Mini ATS (Applicant Tracking System) is a modern, responsive recruitment management platform designed to simplify the hiring process through automated resume screening, skill-based matching, and candidate ranking.

The system provides separate interfaces for candidates and recruiters, allowing candidates to explore job opportunities, manage their profiles, and evaluate their skill compatibility with job requirements. Recruiters can publish job openings, review applicants, compare candidate scores, and identify suitable candidates through an automated ranking mechanism.

The project is developed as a **Third-Year Engineering DBMS Mini Project**, with Phase 1 focusing on the frontend prototype and relational database architecture. The system is designed for future integration with a Python Flask backend and MySQL database.

### 🎯 Project Objectives

- Automate the initial candidate screening process.
- Reduce manual effort in evaluating candidate skills.
- Provide transparent and explainable candidate match scores.
- Rank applicants based on their compatibility with job requirements.
- Demonstrate relational database concepts through a practical recruitment application.
- Establish a scalable architecture for future backend and database integration.

---

## ✨ Key Features

### 1. Candidate Module
- Candidate registration and login.
- Personalized candidate dashboard.
- Profile management and profile completion tracking.
- Resume upload interface (prototype simulation).
- Skill selection and management.
- Job discovery with search and filtering.
- Skill-based job compatibility scores.
- One-click job application.
- Match results with matched and missing skill analysis.

### 2. Recruiter Module
- Recruiter authentication and dashboard.
- Job posting and management.
- Required skill configuration.
- Customizable shortlisting threshold.
- Applicant screening and candidate ranking.
- Automatic descending score-based ranking.
- Candidate profile inspection.
- Application status management.
- Recruitment analytics and visualizations.

### 3. Automated Skill Matching
- Compares candidate skills against required job skills.
- Calculates a percentage-based compatibility score.
- Identifies matched and missing skills.
- Automatically evaluates shortlisting eligibility based on the configured threshold.
- Uses a deterministic and explainable mathematical formula.

### 4. Interactive Dashboard & Analytics
- Applicant statistics and KPI cards.
- Applicant volume by job.
- Candidate match score distribution.
- Hiring funnel visualization.
- Recent applications and recruitment activity.

### 5. Academic Demonstration Features
- Preloaded candidate and recruiter demo accounts.
- Sample job listings and candidate profiles.
- One-click demo login functionality.
- Interactive screens for demonstrating the complete recruitment workflow.

---

## 🧮 Core Skill Matching Algorithm

The system uses a deterministic, rule-based skill matching algorithm to calculate the compatibility between a candidate's skills and a job's required skills.

### Matching Formula

**Match Score:**

`(Number of Matched Required Skills / Total Required Skills) × 100`

### Example

**Job Requirements:**
- Python
- SQL
- Django
- Git
- REST API

**Candidate Skills:**
- Python
- SQL
- Django
- Git

**Matching Results:**

| Metric | Result |
|---|---|
| Total Required Skills | 5 |
| Matched Skills | 4 |
| Missing Skills | 1 |
| Match Score | 80% |

**Calculation:**

`(4 / 5) × 100 = 80%`

**Shortlisting Decision:**

If the recruiter's configured shortlisting threshold is 80%, the candidate qualifies for shortlisting.

The algorithm also provides a transparent breakdown of matched and missing skills, making candidate evaluation easier to understand.

**Implementation:** `src/services/matchingService.js`

---

## 🗄️ Database Design — Relational DBMS Architecture

The application follows a relational database design consisting of six core tables.

The Phase 1 frontend data layer is structured to represent these relational entities and prepare for Phase 2 MySQL integration.

### Database Tables

| Table | Description |
|---|---|
| USERS | Stores candidate and recruiter information. |
| SKILLS | Maintains the master list of technical and professional skills. |
| USER_SKILLS | Maps skills to individual candidates. |
| JOBS | Stores job postings and recruiter information. |
| JOB_SKILLS | Maps required skills to job postings. |
| APPLICATIONS | Stores applications, match scores, and application statuses. |

### Entity Relationships

- A user can possess multiple skills.
- A skill can belong to multiple users.
- A recruiter can create multiple job postings.
- A job can require multiple skills.
- A candidate can apply for multiple jobs.
- Each application connects a candidate with a particular job.

The design demonstrates primary keys, foreign keys, and many-to-many relationships.

**Database schema:** `database_schema.sql`

**Frontend Data Access Layer:** `src/services/storageService.js`

---

## 📱 Application Screens

The platform includes nine interactive screens.

| No. | Screen | Route | Description |
|---|---|---|---|
| 1 | Landing Page | `/` | Project introduction, features, and recruitment workflow. |
| 2 | Login & Registration | `/login` | Candidate and recruiter authentication interfaces. |
| 3 | Candidate Dashboard | `/candidate/dashboard` | Candidate statistics, recommended jobs, and applications. |
| 4 | Resume & Skills | `/candidate/resume` | Candidate profile management and skill selection. |
| 5 | Job Listings | `/candidate/jobs` | Job search, filtering, match scores, and applications. |
| 6 | Recruiter Dashboard | `/recruiter/dashboard` | Recruitment KPIs, charts, and job management. |
| 7 | Post Job | `/recruiter/post-job` | Job creation and shortlisting threshold configuration. |
| 8 | Screening & Ranking | `/recruiter/screening` | Applicant ranking, score comparison, and status updates. |
| 9 | Match Results | `/candidate/match-results` | Skill compatibility, missing skills, and recommendations. |

---

## 👥 Demo Accounts

The application includes preconfigured accounts for academic demonstration.

**Demo Password:** `password123`

| Role | Name | Email | Skills |
|---|---|---|---|
| Recruiter | Admin Recruiter | recruiter@technova.com | N/A |
| Candidate | Rahul Sharma | rahul.sharma@example.com | Python, SQL, Git, Django |
| Candidate | Priya Patil | priya.patil@example.com | Python, SQL, Machine Learning |
| Candidate | Amit Deshmukh | amit.deshmukh@example.com | Java, MySQL, HTML, CSS |
| Candidate | Sneha Kulkarni | sneha.kulkarni@example.com | React, JavaScript, HTML, CSS |
| Candidate | Rohan Joshi | rohan.joshi@example.com | Python, Flask, Git, REST API |
| Candidate | Neha Singh | neha.singh@example.com | SQL, Power BI, Data Analysis |

Alternatively, use the one-click demo login options available on the login screen.

> **Note:** These are demonstration credentials only. They must not be used as production authentication credentials.

---

## 🛠️ Technology Stack

### Frontend

| Technology | Purpose |
|---|---|
| React.js | Component-based user interface development. |
| Vite | Frontend development server and build tooling. |
| JavaScript (ES6+) | Application logic and interactivity. |
| Tailwind CSS | Responsive styling and UI design. |
| Recharts | Dashboard analytics and data visualization. |
| React Router | Client-side navigation and route management. |
| HTML5 & CSS3 | Application structure and styling. |

### Backend & Database — Planned Phase 2 Integration

| Technology | Purpose |
|---|---|
| Python | Backend development. |
| Flask | REST API development. |
| MySQL | Relational database management. |
| SQL | Database queries and relational operations. |

---

## 📂 Project Structure

```text
Resume-Screening-System/
│
├── backend/
│   └── Python backend files
│
├── src/
│   ├── assets/
│   │
│   ├── components/
│   │   ├── candidate/
│   │   ├── common/
│   │   └── recruiter/
│   │
│   ├── context/
│   │   ├── AuthContext.jsx
│   │   └── ToastContext.jsx
│   │
│   ├── data/
│   │   └── initialData.js
│   │
│   ├── layouts/
│   │   ├── CandidateLayout.jsx
│   │   ├── MainLayout.jsx
│   │   └── RecruiterLayout.jsx
│   │
│   ├── pages/
│   │
│   ├── services/
│   │   ├── matchingService.js
│   │   └── storageService.js
│   │
│   ├── utils/
│   │   └── helpers.js
│   │
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
│
├── database_schema.sql
├── index.html
├── package.json
├── package-lock.json
├── postcss.config.js
├── tailwind.config.js
├── vite.config.js
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

Follow these instructions to run the frontend prototype locally.

### Prerequisites

Ensure the following tools are installed:

- Node.js (v18 or higher)
- npm (Node Package Manager)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/dipika1813/Resume-Screening-System.git
```

### 2. Navigate to the Project Directory

```bash
cd Resume-Screening-System
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Start the Development Server

```bash
npm run dev
```

Open the local URL displayed in your terminal. Depending on the Vite configuration, it may be:

`http://localhost:5173`

### 5. Build for Production

```bash
npm run build
```

This generates an optimized production build inside the `dist/` directory.

---

## 🔮 Future Scope — Phase 2

The next development phase focuses on integrating the frontend prototype with a Python Flask backend and MySQL database.

### 1. MySQL Database Integration
- Create the six relational database tables.
- Implement primary key and foreign key constraints.
- Establish relationships between users, skills, jobs, and applications.
- Implement CRUD operations using SQL.

### 2. Flask REST API Development

Planned API endpoints include:

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/login` | User authentication. |
| GET | `/api/jobs` | Retrieve available job postings. |
| POST | `/api/applications` | Submit candidate applications. |
| GET | `/api/jobs/<id>/rankings` | Retrieve ranked applicants. |

### 3. Resume Processing
- Implement actual PDF resume uploads.
- Extract resume text using Python libraries.
- Identify relevant candidate skills.
- Compare extracted skills with job requirements.

### 4. Authentication & Security
- Implement secure password hashing.
- Introduce token-based authentication.
- Add role-based access control.
- Secure API endpoints and user data.

### 5. Full-Stack Integration
- Replace frontend-only data persistence with Flask API requests.
- Connect React components to backend services.
- Integrate MySQL for persistent storage.
- Implement end-to-end recruitment workflows.

---

## 🎓 Academic Information

**Project:** Mini ATS — Resume Screening & Candidate Ranking System

**Project Type:** DBMS Mini Project

**Academic Level:** Third-Year Engineering

**Development Phase:** Phase 1 — Frontend Prototype

**Planned Backend:** Python Flask

**Planned Database:** MySQL

---

## 👩‍💻 Developer

**Dipika**

GitHub: [@dipika1813](https://github.com/dipika1813)

**Repository:** [Resume-Screening-System](https://github.com/dipika1813/Resume-Screening-System)

---

## 📄 License

This project is developed for academic and educational purposes. A formal open-source license can be added if the project is intended for public reuse and distribution.

---

**Mini ATS — Making Recruitment Smarter Through Transparent Skill-Based Screening.**
