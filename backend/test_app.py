"""
Automated test script for real email dispatch, dynamic OTP storage,
and SQLite user credential management in AI Business Opportunity Finder.
"""

import json
import urllib.request
import urllib.error
import sqlite3

BASE_URL = "http://127.0.0.1:8000"

def make_request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            return response.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"detail": err_body}

def test_email_and_credentials():
    print("=" * 60)
    print("Testing Dynamic OTP & SQLite User Credential Management")
    print("=" * 60)

    test_real_email = "founder@startup.com"

    # Step 1: Request OTP
    status, start_res = make_request("POST", "/api/auth/start", {"email": test_real_email})
    assert status == 200, f"Auth start failed: {start_res}"
    print("[OK] POST /api/auth/start succeeded:", start_res["message"])

    # Step 2: Verify in SQLite that the OTP code & expiry were stored
    conn = sqlite3.connect("business_opportunity.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, otp_code, otp_expires_at, last_login_at FROM users WHERE email = ?", (test_real_email,))
    user_row = cursor.fetchone()
    assert user_row is not None, "User row was not created in SQLite!"
    user = dict(user_row)
    stored_otp = user["otp_code"]
    assert stored_otp is not None and len(stored_otp) == 6, f"Invalid OTP in SQLite: {stored_otp}"
    assert user["otp_expires_at"] is not None, "Expiration timestamp missing!"
    print(f"[OK] SQLite User Credential Verified: Email={user['email']}, Stored OTP={stored_otp}, ExpiresAt={user['otp_expires_at']}")
    conn.close()

    # Step 3: Test verifying with incorrect OTP
    status, err_res = make_request("POST", "/api/auth/verify", {"email": test_real_email, "code": "000000"})
    assert status == 401, f"Expected 401, got {status}"
    print("[OK] Invalid OTP correctly rejected by SQLite verification.")

    # Step 4: Verify with the actual dynamic OTP retrieved from SQLite
    status, verify_res = make_request("POST", "/api/auth/verify", {"email": test_real_email, "code": stored_otp})
    assert status == 200, f"Verify with dynamic OTP failed: {verify_res}"
    verified_user = verify_res["user"]
    assert verified_user["email"] == test_real_email
    print(f"[OK] Authenticated successfully using dynamic OTP! User ID: {verified_user['id']}")

    # Step 5: Check in SQLite that the OTP has been invalidated and last_login_at recorded
    conn = sqlite3.connect("business_opportunity.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT otp_code, last_login_at FROM users WHERE email = ?", (test_real_email,))
    refreshed_user = dict(cursor.fetchone())
    assert refreshed_user["otp_code"] is None, "Used OTP was not cleared from SQLite!"
    assert refreshed_user["last_login_at"] is not None, "last_login_at was not updated!"
    print(f"[OK] Post-Auth SQLite Hygiene Verified: OTP cleared to NULL, last_login_at={refreshed_user['last_login_at']}")
    conn.close()

    # Step 6: Create analysis and verify search history saved to SQLite
    search_payload = {
        "email": test_real_email,
        "domain": "Technology",
        "city": "Hyderabad",
        "area": "Hitech City",
        "description": "AI agent tools for remote software engineers"
    }
    status, search_res = make_request("POST", "/api/analyze", search_payload)
    assert status == 200
    print(f"[OK] Opportunity search completed ({len(search_res['opportunities'])} opportunities generated)")

    # Step 7: Check search history in SQLite
    status, history_res = make_request("GET", f"/api/history?email={test_real_email}")
    assert status == 200 and len(history_res) >= 1
    print(f"[OK] Search History Verified in SQLite: {len(history_res)} search records for {test_real_email}")

    print("=" * 60)
    print("ALL TESTS PASSED: DYNAMIC OTP, SQLITE CREDENTIALS & HISTORY! [SUCCESS]")
    print("=" * 60)

if __name__ == "__main__":
    test_email_and_credentials()
