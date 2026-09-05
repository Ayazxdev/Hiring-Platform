import httpx
import asyncio
import os
import json
from datetime import datetime, timedelta

# E2E Comprehensive Test script for Fair Hiring Network
API_BASE_URL = "http://localhost:8012"

async def test_health(client):
    print("\n--- 1. Testing Health Check ---")
    response = await client.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}, Response: {response.json()}")
    assert response.status_code == 200
    return True

async def test_company_signup_and_login(client):
    print("\n--- 2. Testing Company Signup & Login ---")
    timestamp = int(datetime.now().timestamp())
    company_email = f"hr_{timestamp}@acmecorp.tech"
    password = "SecureCompanyPassword123!"
    
    # Signup
    signup_payload = {
        "name": f"Acme Corp {timestamp}",
        "email": company_email,
        "password": password
    }
    signup_res = await client.post(f"{API_BASE_URL}/auth/company/signup", json=signup_payload)
    print(f"Signup Status: {signup_res.status_code}, Body: {signup_res.text}")
    assert signup_res.status_code == 200, f"Company signup failed: {signup_res.text}"
    company_data = signup_res.json()
    company_id = company_data["company_id"]
    
    # Login
    login_payload = {
        "email": company_email,
        "password": password
    }
    login_res = await client.post(f"{API_BASE_URL}/auth/company/login", json=login_payload)
    print(f"Login Status: {login_res.status_code}, Body: {login_res.text}")
    assert login_res.status_code == 200, f"Company login failed: {login_res.text}"
    
    return company_id, company_email

async def test_analyze_bias(client):
    print("\n--- 3. Testing Real-time Job Description Bias Analysis ---")
    payload = {
        "description": "We are seeking a rockstar young ninja developer who fits our bro-culture and comes from an Ivy League school."
    }
    res = await client.post(f"{API_BASE_URL}/company/analyze_bias", json=payload)
    print(f"Bias Audit Status: {res.status_code}")
    data = res.json()
    print(f"Audit Result: {json.dumps(data, indent=2)}")
    assert res.status_code == 200
    return data

async def test_create_and_list_jobs(client, company_id):
    print("\n--- 4. Testing Job Creation (Bias Audit & Extraction) ---")
    job_payload = {
        "company_id": company_id,
        "title": "Senior Machine Learning Engineer",
        "description": "We are looking for an experienced ML engineer with 5+ years of experience in Python, PyTorch, and distributed systems. Passionate about fair algorithms.",
        "required_skills": ["Python", "PyTorch", "NLP", "AWS"],
        "published": True,
        "max_participants": 5
    }
    create_res = await client.post(f"{API_BASE_URL}/api/jobs", json=job_payload)
    print(f"Job Create Status: {create_res.status_code}, Body: {create_res.text}")
    assert create_res.status_code in [200, 201], f"Job creation failed: {create_res.text}"
    job_data = create_res.json()
    job_id = job_data.get("job_id") or job_data.get("id")
    print(f"Created Job ID: {job_id}")

    # List jobs
    list_res = await client.get(f"{API_BASE_URL}/api/jobs")
    print(f"List Jobs Status: {list_res.status_code}, Total Jobs: {len(list_res.json())}")
    assert list_res.status_code == 200

    # Get single job
    get_res = await client.get(f"{API_BASE_URL}/api/jobs/{job_id}")
    print(f"Get Job Status: {get_res.status_code}, Title: {get_res.json().get('title')}")
    assert get_res.status_code == 200

    return job_id

async def test_candidate_signup_and_login(client):
    print("\n--- 5. Testing Candidate Signup & Login ---")
    timestamp = int(datetime.now().timestamp())
    candidate_email = f"jane.doe.{timestamp}@example.com"
    password = "SecurePassword123!"

    # Signup
    signup_payload = {
        "name": "Jane Doe",
        "email": candidate_email,
        "gender": "Female",
        "college": "State University",
        "password": password,
        "engineer_level": "Senior"
    }
    signup_res = await client.post(f"{API_BASE_URL}/auth/candidate/signup", json=signup_payload)
    print(f"Candidate Signup Status: {signup_res.status_code}, Body: {signup_res.text}")
    assert signup_res.status_code == 200, f"Candidate signup failed: {signup_res.text}"
    cand_data = signup_res.json()
    anon_id = cand_data["anon_id"]
    candidate_id = cand_data["id"]

    # Login
    login_payload = {
        "email": candidate_email,
        "password": password
    }
    login_res = await client.post(f"{API_BASE_URL}/auth/candidate/login", json=login_payload)
    print(f"Candidate Login Status: {login_res.status_code}, Body: {login_res.text}")
    assert login_res.status_code == 200, f"Candidate login failed: {login_res.text}"

    return candidate_id, anon_id

async def test_submit_application(client, anon_id, job_id):
    print("\n--- 6. Testing Application Submission (Triggers Multi-Agent Pipeline) ---")
    app_payload = {
        "anon_id": anon_id,
        "job_id": job_id,
        "resume_text": "Senior Machine Learning Engineer with 6 years experience in Python, PyTorch, and NLP. Designed low-latency model serving pipelines on AWS and Docker.",
        "github_url": "https://github.com/torvalds",
        "linkedin_url": "https://linkedin.com/in/test-candidate",
        "leetcode_url": "https://leetcode.com/test-candidate",
        "codeforces_url": "https://codeforces.com/profile/test-candidate",
        "run_pipeline": True
    }
    res = await client.post(f"{API_BASE_URL}/api/applications", json=app_payload)
    print(f"Application Submission Status: {res.status_code}, Body: {res.text}")
    assert res.status_code in [200, 201], f"Application submission failed: {res.text}"
    app_data = res.json()
    app_id = app_data["application_id"]
    print(f"Created Application ID: {app_id}, Initial Pipeline Status: {app_data.get('pipeline_status')}")
    return app_id

async def poll_pipeline_completion(client, app_id, max_retries=45):
    print(f"\n--- 7. Polling Multi-Agent Pipeline Execution for Application {app_id} ---")
    for attempt in range(1, max_retries + 1):
        res = await client.get(f"{API_BASE_URL}/api/applications/{app_id}")
        assert res.status_code == 200
        data = res.json()
        p_status = data.get("pipeline_status")
        app_status = data.get("status")
        score = data.get("match_score")
        print(f"Attempt {attempt}/{max_retries}: Pipeline Status='{p_status}', App Status='{app_status}', Match Score={score}")
        
        if p_status in ["completed", "failed", "rejected", "needs_review"]:
            print(f"Pipeline finished with final status: {p_status}!")
            print(f"Details: {json.dumps(data, indent=2)}")
            return data
            
        await asyncio.sleep(3)
        
    raise TimeoutError(f"Pipeline polling timed out after {max_retries * 3} seconds")

async def test_passport_and_verification(client, anon_id):
    print("\n--- 8. Testing Passport Credential & Cryptographic Verification ---")
    res = await client.get(f"{API_BASE_URL}/passport/{anon_id}")
    print(f"Passport Status: {res.status_code}, Body: {res.text}")
    assert res.status_code == 200
    creds = res.json()
    if creds:
        cred = creds[0]
        print(f"Retrieved Passport Credential: Hash={cred.get('hash_sha256')}")
        verify_payload = {
            "credential": cred.get("credential"),
            "signature_b64": cred.get("signature_b64")
        }
        v_res = await client.post(f"{API_BASE_URL}/passport/verify", json=verify_payload)
        print(f"Cryptographic Verification: {v_res.status_code}, Body: {v_res.json()}")
        assert v_res.status_code == 200
        assert v_res.json().get("verified") is True
        print("Ed25519 Cryptographic Verification PASSED!")
    else:
        print("Note: No passport credential generated yet.")

async def test_candidate_views(client, anon_id):
    print("\n--- 9. Testing Candidate Dashboard & Applications View ---")
    stats_res = await client.get(f"{API_BASE_URL}/candidate/{anon_id}/stats")
    print(f"Candidate Stats: {stats_res.status_code}, Body: {stats_res.json()}")
    assert stats_res.status_code == 200

    apps_res = await client.get(f"{API_BASE_URL}/candidate/{anon_id}/applications")
    print(f"Candidate Applications: {apps_res.status_code}, Count: {len(apps_res.json())}")
    assert apps_res.status_code == 200

async def test_company_views_and_matching(client, company_id, job_id):
    print("\n--- 10. Testing Company Dashboard, Applications & Matching Engine ---")
    # Company stats
    stats_res = await client.get(f"{API_BASE_URL}/company/{company_id}/stats")
    print(f"Company Stats: {stats_res.status_code}, Body: {stats_res.json()}")
    assert stats_res.status_code == 200

    # Company jobs
    jobs_res = await client.get(f"{API_BASE_URL}/company/{company_id}/jobs")
    print(f"Company Jobs: {jobs_res.status_code}, Count: {len(jobs_res.json())}")
    assert jobs_res.status_code == 200

    # Applications for this job
    apps_res = await client.get(f"{API_BASE_URL}/company/{company_id}/jobs/{job_id}/applications")
    print(f"Job Applications: {apps_res.status_code}, Count: {len(apps_res.json())}")
    assert apps_res.status_code == 200

    # Run matching
    match_res = await client.post(f"{API_BASE_URL}/company/{company_id}/jobs/{job_id}/run-matching")
    print(f"Run Matching Result: {match_res.status_code}, Body: {match_res.json()}")
    assert match_res.status_code == 200

    # Selected candidates
    selected_res = await client.get(f"{API_BASE_URL}/company/{company_id}/jobs/{job_id}/selected")
    print(f"Selected Candidates: {selected_res.status_code}, Count: {len(selected_res.json())}")
    assert selected_res.status_code == 200

    # Review queue
    review_res = await client.get(f"{API_BASE_URL}/company/{company_id}/review-queue")
    print(f"Review Queue: {review_res.status_code}, Cases: {len(review_res.json())}")
    assert review_res.status_code == 200

async def test_status_update(client, app_id):
    print("\n--- 11. Testing Application Status Update ---")
    update_payload = {
        "status": "matched",
        "feedback": "Passed automated multi-agent verification, shortlisted for interview."
    }
    patch_res = await client.patch(f"{API_BASE_URL}/api/applications/{app_id}/status", json=update_payload)
    print(f"Status Update: {patch_res.status_code}, Body: {patch_res.json()}")
    assert patch_res.status_code == 200
    assert patch_res.json().get("status") == "matched"

async def run_all_e2e_tests():
    print("=" * 70)
    print("STARTING COMPLETE END-TO-END VERIFICATION OF FAIR HIRING NETWORK")
    print("=" * 70)
    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            # 1. Health
            await test_health(client)

            # 2. Company Auth
            company_id, company_email = await test_company_signup_and_login(client)

            # 3. Real-time JD Bias Analysis
            await test_analyze_bias(client)

            # 4. Job Creation & Listing
            job_id = await test_create_and_list_jobs(client, company_id)

            # 5. Candidate Auth
            cand_id, anon_id = await test_candidate_signup_and_login(client)

            # 6. Application Submission
            app_id = await test_submit_application(client, anon_id, job_id)

            # 7. Polling Multi-Agent Pipeline
            await poll_pipeline_completion(client, app_id)

            # 8. Cryptographic Passport & Credential Verification
            await test_passport_and_verification(client, anon_id)

            # 9. Candidate Views & Stats
            await test_candidate_views(client, anon_id)

            # 10. Company Views & Matching Engine
            await test_company_views_and_matching(client, company_id, job_id)

            # 11. Application Status Update
            await test_status_update(client, app_id)

            print("\n" + "=" * 70)
            print("ALL 11 END-TO-END FEATURE FLOWS PASSED SUCCESSFULLY!")
            print("=" * 70)

        except httpx.ConnectError:
            print(f"\n[ERROR] Connection failed to {API_BASE_URL}. Ensure backend is running.")
            raise

if __name__ == "__main__":
    asyncio.run(run_all_e2e_tests())
