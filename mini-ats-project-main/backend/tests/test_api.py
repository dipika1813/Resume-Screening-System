import json
import unittest
from unittest.mock import patch

import app as api


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()

    @patch.object(api, "one", return_value={"database_name": "mini_ats_db"})
    def test_health_reports_database(self, _one):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["database"], "mini_ats_db")

    def test_public_user_maps_schema_to_frontend_shape_and_hides_hash(self):
        result = api.public_user({
            "id": "usr-1", "name": "A", "email": "a@example.com", "password_hash": "secret",
            "company_name": "Acme", "experience_years": 1.5, "graduation_year": "2025",
            "created_at": None, "updated_at": None, "resume_file_name": "cv.pdf",
            "resume_file_size": "2 KB", "resume_uploaded_at": None,
        })
        self.assertNotIn("password_hash", result)
        self.assertEqual(result["companyName"], "Acme")
        self.assertEqual(result["experienceYears"], 1.5)
        self.assertEqual(result["resumeFile"]["name"], "cv.pdf")
        self.assertEqual(result["skills"], [])

    @patch.object(api, "one")
    def test_login_rejects_seed_placeholder_hash(self, mock_one):
        mock_one.return_value = {"id": "usr-1", "email": "a@example.com", "password_hash": "$2b$12$..."}
        response = self.client.post("/api/auth/login", json={"email": "a@example.com", "password": "password123"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("placeholder", response.json["error"])

    @patch.object(api, "execute")
    @patch.object(api, "one")
    @patch.object(api, "skills_for", side_effect=[["Python", "SQL"], ["Python"]])
    def test_application_uses_schema_skills_and_shortlist_threshold(self, _skills, mock_one, mock_execute):
        mock_one.side_effect = [
            {"id": "job-1", "threshold": 50},
            {"id": "usr-1", "name": "A", "email": "a@example.com"},
            {"id": "app-generated", "job_id": "job-1", "candidate_id": "usr-1", "candidate_name": "A",
             "candidate_email": "a@example.com", "match_score": 50, "matched_skills": '["Python"]',
             "missing_skills": '["SQL"]', "status": "Shortlisted", "notes": "", "applied_date": None,
             "updated_at": None},
        ]
        response = self.client.post("/api/applications", json={"jobId": "job-1", "candidateId": "usr-1"})
        self.assertEqual(response.status_code, 201)
        item = response.json["application"]
        self.assertEqual(item["matchScore"], 50)
        self.assertEqual(item["matchedSkills"], ["Python"])
        self.assertEqual(item["missingSkills"], ["SQL"])
        self.assertEqual(item["status"], "Shortlisted")
        self.assertEqual(json.loads(mock_execute.call_args.args[1][6]), ["Python"])

    @patch.object(api, "rows", return_value=[])
    def test_job_filters_are_parameterized(self, mock_rows):
        response = self.client.get("/api/jobs?status=Active&recruiterId=usr-1")
        self.assertEqual(response.status_code, 200)
        sql, params = mock_rows.call_args.args
        self.assertIn("recruiter_id=%s", sql)
        self.assertIn("status=%s", sql)
        self.assertEqual(params, ("usr-1", "Active"))


if __name__ == "__main__":
    unittest.main()
