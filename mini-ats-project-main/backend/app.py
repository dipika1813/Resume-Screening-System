"""Mini ATS REST API backed by the MySQL schema in database_schema.sql."""
from datetime import date, datetime
from decimal import Decimal
import json
import os
import uuid

import bcrypt
from flask import Flask, jsonify, request
from flask_cors import CORS
from mysql.connector import IntegrityError

from db import get_db_connection

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")}})


def public_user(row):
    if row is None:
        return None
    result = dict(row)
    result.pop("password_hash", None)
    result["companyName"] = result.pop("company_name", None) or ""
    result["experienceYears"] = float(result.pop("experience_years", 0) or 0)
    result["graduationYear"] = result.pop("graduation_year", None) or ""
    result["createdAt"] = result.pop("created_at", None)
    result["updatedAt"] = result.pop("updated_at", None)
    filename = result.pop("resume_file_name", None)
    filesize = result.pop("resume_file_size", None)
    uploaded = result.pop("resume_uploaded_at", None)
    result["resumeFile"] = ({"name": filename, "size": filesize, "uploadedAt": uploaded} if filename else None)
    result["skills"] = result.pop("skills", [])
    return result


def json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8")
    return value


def rows(sql, params=()):
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        result = cursor.fetchall()
        cursor.close()
        return result
    finally:
        connection.close()


def one(sql, params=()):
    result = rows(sql, params)
    return result[0] if result else None


def execute(sql, params=()):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        connection.commit()
        inserted = cursor.lastrowid
        cursor.close()
        return inserted
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def fail(message, status=400):
    return jsonify({"success": False, "error": message}), status


def payload():
    return request.get_json(silent=True) or {}


def skills_for(table, foreign_key, record_id):
    return [r["skill_name"] for r in rows(
        f"SELECT skill_name FROM {table} WHERE {foreign_key} = %s ORDER BY id", (record_id,)
    )]


def set_skills(table, foreign_key, record_id, names):
    names = list(dict.fromkeys(str(n).strip() for n in (names or []) if str(n).strip()))
    execute(f"DELETE FROM {table} WHERE {foreign_key} = %s", (record_id,))
    for name in names:
        execute(f"INSERT INTO {table} ({foreign_key}, skill_name) VALUES (%s, %s)", (record_id, name))


def user_with_skills(row):
    result = public_user(row)
    result["skills"] = skills_for("User_Skills", "user_id", row["id"])
    return result


def job_shape(row):
    result = dict(row)
    result["recruiterId"] = result.pop("recruiter_id")
    result["companyName"] = result.pop("company_name")
    result["companyInitials"] = "".join(w[0] for w in result["companyName"].split() if w)[:2].upper()
    result["type"] = result.pop("job_type")
    result["minExperience"] = result.pop("min_experience")
    result["requiredSkills"] = skills_for("Job_Skills", "job_id", result["id"])
    for old, new in (("created_at", "createdAt"), ("updated_at", "updatedAt")):
        result[new] = result.pop(old, None)
    return result


def application_shape(row, include_profile=False):
    result = dict(row)
    for old, new in (("job_id", "jobId"), ("candidate_id", "candidateId"), ("candidate_name", "candidateName"),
                     ("candidate_email", "candidateEmail"), ("match_score", "matchScore"), ("applied_date", "appliedDate"),
                     ("updated_at", "updatedAt"), ("matched_skills", "matchedSkills"), ("missing_skills", "missingSkills")):
        result[new] = result.pop(old, None)
    for key in ("matchedSkills", "missingSkills"):
        if isinstance(result[key], str):
            result[key] = json.loads(result[key])
    if include_profile:
        candidate = one("SELECT * FROM Users WHERE id = %s", (result["candidateId"],))
        profile = user_with_skills(candidate) if candidate else {}
        result["candidateProfile"] = profile
        result["education"] = profile.get("education") or "N/A"
        result["experienceYears"] = profile.get("experienceYears", 0)
        result["skills"] = profile.get("skills", [])
        result["phone"] = profile.get("phone") or ""
        result["resumeFile"] = profile.get("resumeFile")
    return result


@app.get("/api/health")
def health():
    try:
        result = one("SELECT DATABASE() AS database_name")
        return jsonify(success=True, database=result["database_name"])
    except Exception:
        app.logger.exception("Database health check failed")
        return fail("Database connection failed. Check backend/.env and MySQL.", 503)


@app.post("/api/auth/login")
def login():
    data = payload()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    row = one("SELECT * FROM Users WHERE LOWER(email) = %s", (email,))
    if not row:
        return fail("Invalid email or password.", 401)
    try:
        valid = bcrypt.checkpw(password.encode(), row["password_hash"].encode())
    except (ValueError, TypeError):
        valid = False
    if not valid:
        return fail("Invalid email or password. Seed accounts have placeholder hashes; create a new account to sign in.", 401)
    return jsonify(success=True, user=user_with_skills(row))


@app.post("/api/users")
def create_user():
    data = payload()
    required = ("name", "email", "password")
    if any(not str(data.get(k, "")).strip() for k in required):
        return fail("name, email, and password are required.")
    if data.get("role", "candidate") not in ("candidate", "recruiter"):
        return fail("role must be candidate or recruiter.")
    uid = f"usr-{uuid.uuid4().hex[:16]}"
    resume = data.get("resumeFile") or {}
    try:
        execute("""INSERT INTO Users (id,name,email,password_hash,role,company_name,phone,location,education,degree,
                   graduation_year,experience_years,bio,resume_file_name,resume_file_size,resume_uploaded_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (uid, data["name"].strip(), data["email"].strip().lower(),
                 bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode(), data.get("role", "candidate"),
                 data.get("companyName"), data.get("phone"), data.get("location"), data.get("education"), data.get("degree"),
                 data.get("graduationYear"), data.get("experienceYears", 0), data.get("bio"), resume.get("name"),
                 resume.get("size"), resume.get("uploadedAt")))
        set_skills("User_Skills", "user_id", uid, data.get("skills", []))
        return jsonify(success=True, user=user_with_skills(one("SELECT * FROM Users WHERE id=%s", (uid,)))), 201
    except IntegrityError:
        return fail("An account with this email address already exists.", 409)


@app.get("/api/users")
def get_users():
    result = []
    for row in rows("SELECT * FROM Users ORDER BY created_at DESC"):
        result.append(user_with_skills(row))
    return jsonify(result)


@app.get("/api/users/<user_id>")
def get_user(user_id):
    row = one("SELECT * FROM Users WHERE id=%s", (user_id,))
    return (jsonify(user_with_skills(row)), 200) if row else fail("User not found.", 404)


@app.patch("/api/users/<user_id>")
def update_user(user_id):
    data = payload()
    columns = {"name":"name", "companyName":"company_name", "phone":"phone", "location":"location", "education":"education",
               "degree":"degree", "graduationYear":"graduation_year", "experienceYears":"experience_years", "bio":"bio"}
    fields = [(columns[k], data[k]) for k in columns if k in data]
    resume = data.get("resumeFile")
    if isinstance(resume, dict):
        fields += [("resume_file_name", resume.get("name")), ("resume_file_size", resume.get("size")), ("resume_uploaded_at", resume.get("uploadedAt"))]
    if not one("SELECT id FROM Users WHERE id=%s", (user_id,)):
        return fail("User not found.", 404)
    if fields:
        clause = ", ".join(f"{column}=%s" for column, _ in fields)
        execute(f"UPDATE Users SET {clause} WHERE id=%s", tuple(v for _, v in fields) + (user_id,))
    if "skills" in data:
        set_skills("User_Skills", "user_id", user_id, data["skills"])
    return jsonify(user=user_with_skills(one("SELECT * FROM Users WHERE id=%s", (user_id,))))


@app.get("/api/skills")
def get_skills():
    return jsonify(rows("SELECT id,name,category FROM Skills ORDER BY name"))


@app.post("/api/skills")
def add_skill():
    data = payload()
    name = str(data.get("name", "")).strip()
    if not name:
        return fail("name is required.")
    existing = one("SELECT id,name,category FROM Skills WHERE LOWER(name)=LOWER(%s)", (name,))
    if existing:
        return jsonify(existing)
    sid = f"sk-{uuid.uuid4().hex[:16]}"
    try:
        execute("INSERT INTO Skills (id,name,category) VALUES (%s,%s,%s)", (sid, name, data.get("category", "Custom")))
    except IntegrityError:
        return jsonify(one("SELECT id,name,category FROM Skills WHERE LOWER(name)=LOWER(%s)", (name,))), 200
    return jsonify(id=sid, name=name, category=data.get("category", "Custom")), 201


@app.get("/api/jobs")
def get_jobs():
    clauses, params = [], []
    for key, column in (("recruiterId", "recruiter_id"), ("status", "status"), ("type", "job_type")):
        value = request.args.get(key)
        if value and value != "All":
            clauses.append(f"{column}=%s"); params.append(value)
    search = request.args.get("search", "").strip()
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    found = rows("SELECT * FROM Jobs" + where + " ORDER BY created_at DESC", tuple(params))
    if search:
        needle = search.casefold()
        found = [j for j in found if needle in j["title"].casefold() or needle in j["company_name"].casefold()
                 or needle in j["location"].casefold() or any(needle in s.casefold() for s in skills_for("Job_Skills", "job_id", j["id"]))]
    return jsonify([job_shape(j) for j in found])


@app.post("/api/jobs")
def create_job():
    data = payload()
    required = ("recruiterId", "companyName", "title", "location", "description")
    if any(not str(data.get(k, "")).strip() for k in required):
        return fail("recruiterId, companyName, title, location, and description are required.")
    jid = f"job-{uuid.uuid4().hex[:16]}"
    execute("""INSERT INTO Jobs (id,recruiter_id,company_name,title,location,job_type,min_experience,description,threshold,deadline,salary,status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (jid, data["recruiterId"], data["companyName"], data["title"], data["location"], data.get("type", "Full-Time"),
             data.get("minExperience", "0-2 years"), data["description"], data.get("threshold", 80), data.get("deadline") or None,
             data.get("salary"), data.get("status", "Active")))
    set_skills("Job_Skills", "job_id", jid, data.get("requiredSkills", []))
    return jsonify(job=job_shape(one("SELECT * FROM Jobs WHERE id=%s", (jid,)))), 201


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    row = one("SELECT * FROM Jobs WHERE id=%s", (job_id,))
    return (jsonify(job_shape(row)), 200) if row else fail("Job not found.", 404)


@app.patch("/api/jobs/<job_id>")
def update_job(job_id):
    data = payload()
    if not one("SELECT id FROM Jobs WHERE id=%s", (job_id,)):
        return fail("Job not found.", 404)
    columns = {"companyName":"company_name", "title":"title", "location":"location", "type":"job_type", "minExperience":"min_experience",
               "description":"description", "threshold":"threshold", "deadline":"deadline", "salary":"salary", "status":"status"}
    fields = [(columns[k], data[k] or None if k == "deadline" else data[k]) for k in columns if k in data]
    if fields:
        execute("UPDATE Jobs SET " + ", ".join(f"{c}=%s" for c,_ in fields) + " WHERE id=%s", tuple(v for _,v in fields)+(job_id,))
    if "requiredSkills" in data:
        set_skills("Job_Skills", "job_id", job_id, data["requiredSkills"])
    return jsonify(job=job_shape(one("SELECT * FROM Jobs WHERE id=%s", (job_id,))))


@app.delete("/api/jobs/<job_id>")
def delete_job(job_id):
    if not one("SELECT id FROM Jobs WHERE id=%s", (job_id,)):
        return fail("Job not found.", 404)
    execute("DELETE FROM Jobs WHERE id=%s", (job_id,))
    return jsonify(success=True)


@app.get("/api/applications")
def get_applications():
    clauses, params = [], []
    for key, column in (("jobId", "job_id"), ("candidateId", "candidate_id"), ("status", "status")):
        value = request.args.get(key)
        if value and value != "All":
            clauses.append(f"{column}=%s"); params.append(value)
    result = rows("SELECT * FROM Applications" + ((" WHERE " + " AND ".join(clauses)) if clauses else "") + " ORDER BY applied_date DESC", tuple(params))
    return jsonify([application_shape(a) for a in result])


@app.post("/api/applications")
def create_application():
    data = payload()
    job_id, candidate_id = data.get("jobId"), data.get("candidateId")
    job = one("SELECT * FROM Jobs WHERE id=%s", (job_id,)) if job_id else None
    candidate = one("SELECT * FROM Users WHERE id=%s", (candidate_id,)) if candidate_id else None
    if not job or not candidate:
        return fail("Invalid job or candidate reference.", 404)
    required = skills_for("Job_Skills", "job_id", job_id)
    actual = skills_for("User_Skills", "user_id", candidate_id)
    matched = [s for s in required if any(s.casefold() in x.casefold() or x.casefold() in s.casefold() for x in actual)]
    missing = [s for s in required if s not in matched]
    score = round(100 * len(matched) / len(required)) if required else 100
    status = "Shortlisted" if score >= job["threshold"] else "Pending"
    aid = f"app-{uuid.uuid4().hex[:16]}"
    try:
        execute("""INSERT INTO Applications (id,job_id,candidate_id,candidate_name,candidate_email,match_score,matched_skills,missing_skills,status,notes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (aid, job_id, candidate_id, candidate["name"], candidate["email"], score, json.dumps(matched), json.dumps(missing), status, data.get("notes", "")))
    except IntegrityError:
        return fail("You have already submitted an application for this position.", 409)
    return jsonify(application=application_shape(one("SELECT * FROM Applications WHERE id=%s", (aid,)))), 201


@app.patch("/api/applications/<application_id>")
def update_application(application_id):
    data = payload()
    fields = []
    if "status" in data:
        if data["status"] not in ("Pending", "Shortlisted", "Rejected"):
            return fail("status must be Pending, Shortlisted, or Rejected.")
        fields.append(("status", data["status"]))
    if "notes" in data:
        fields.append(("notes", data["notes"]))
    if not one("SELECT id FROM Applications WHERE id=%s", (application_id,)):
        return fail("Application not found.", 404)
    if fields:
        execute("UPDATE Applications SET " + ", ".join(f"{c}=%s" for c,_ in fields) + " WHERE id=%s", tuple(v for _,v in fields)+(application_id,))
    return jsonify(application=application_shape(one("SELECT * FROM Applications WHERE id=%s", (application_id,))))


@app.get("/api/jobs/<job_id>/ranked-candidates")
def ranked_candidates(job_id):
    result = rows("SELECT * FROM Applications WHERE job_id=%s ORDER BY match_score DESC, applied_date DESC", (job_id,))
    ranked = [application_shape(item, include_profile=True) for item in result]
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
    return jsonify(ranked)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1", port=int(os.getenv("PORT", "5000")))
