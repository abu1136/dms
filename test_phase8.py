#!/usr/bin/env python3
"""
Phase 8 Feature Testing Script
Tests: Role-based filtering, admin filters, created_by display, audit log visibility, skeleton preview
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
REGULAR_USER = "test"
REGULAR_PASS = "test"

def login(username, password):
    """Login and return token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        token = response.json().get("access_token")
        return token
    return None

def get_documents(token, filters=None):
    """Get documents with optional filters"""
    headers = {"Authorization": f"Bearer {token}"}
    params = filters or {}
    response = requests.get(f"{BASE_URL}/api/documents", headers=headers, params=params)
    return response

def get_users(token):
    """Get list of users"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    return response

def get_audit_logs(token):
    """Try to get audit logs"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/audit", headers=headers)
    return response

def create_document(token, title, template_id, content):
    """Create a document"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": title,
        "template_id": template_id,
        "content": content
    }
    response = requests.post(f"{BASE_URL}/api/documents", headers=headers, json=data)
    return response

def run_tests():
    print("=" * 60)
    print("PHASE 8 FEATURE TEST SUITE")
    print("=" * 60)
    
    # Test 1: Admin Login
    print("\n[TEST 1] Admin Login")
    admin_token = login(ADMIN_USER, ADMIN_PASS)
    if admin_token:
        print("✅ Admin login successful")
    else:
        print("❌ Admin login failed")
        return
    
    # Test 2: Regular User Login
    print("\n[TEST 2] Regular User Login")
    user_token = login(REGULAR_USER, REGULAR_PASS)
    if user_token:
        print("✅ Regular user login successful")
    else:
        print("❌ Regular user login failed")
        return
    
    # Test 3: Get users for filter
    print("\n[TEST 3] Get Users for Admin Filter")
    users_response = get_users(admin_token)
    if users_response.status_code == 200:
        users = users_response.json()
        print(f"✅ Retrieved {len(users)} users")
        for u in users[:3]:
            print(f"   - {u['username']} (ID: {u['id']})")
    else:
        print(f"❌ Failed to get users: {users_response.status_code}")
    
    # Test 4: Create test document
    print("\n[TEST 4] Create Test Document as Admin")
    # Get first template
    templates_response = requests.get(f"{BASE_URL}/api/templates", 
                                     headers={"Authorization": f"Bearer {admin_token}"})
    if templates_response.status_code == 200:
        templates = templates_response.json()
        if templates:
            template_id = templates[0]['id']
            doc_response = create_document(admin_token, 
                                          "Test Document 1",
                                          template_id,
                                          "<p><b>Bold text</b> and <i>italic</i></p><ul><li>Item 1</li></ul>")
            if doc_response.status_code == 201:
                doc = doc_response.json()
                print(f"✅ Document created: {doc['title']} (ID: {doc['id']})")
                print(f"   Created by: {doc.get('requested_by', {}).get('username', 'Unknown')}")
            else:
                print(f"❌ Failed to create document: {doc_response.status_code}")
                print(doc_response.text)
    
    # Test 5: Admin sees all documents
    print("\n[TEST 5] Admin Document List (should see all)")
    admin_docs = get_documents(admin_token)
    if admin_docs.status_code == 200:
        docs = admin_docs.json()
        print(f"✅ Admin retrieved {len(docs)} documents")
        for doc in docs[:3]:
            created_by = doc.get('requested_by', {})
            print(f"   - {doc['title']} (by: {created_by.get('username', 'Unknown')})")
    else:
        print(f"❌ Failed: {admin_docs.status_code}")
    
    # Test 6: Regular user sees only their documents
    print("\n[TEST 6] Regular User Document List (should see only own)")
    user_docs = get_documents(user_token)
    if user_docs.status_code == 200:
        docs = user_docs.json()
        print(f"✅ Regular user retrieved {len(docs)} documents")
        for doc in docs:
            print(f"   - {doc['title']} (by: {doc.get('requested_by', {}).get('username', 'Unknown')})")
    else:
        print(f"❌ Failed: {user_docs.status_code}")
    
    # Test 7: Admin filter by user
    print("\n[TEST 7] Admin Filter by User")
    if users:
        user_id = users[0]['id']
        filtered_docs = get_documents(admin_token, {"created_by": user_id})
        if filtered_docs.status_code == 200:
            docs = filtered_docs.json()
            print(f"✅ Filtered documents for user {users[0]['username']}: {len(docs)} docs")
        else:
            print(f"❌ Failed: {filtered_docs.status_code}")
    
    # Test 8: Admin filter by date range
    print("\n[TEST 8] Admin Filter by Date Range")
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    filtered_docs = get_documents(admin_token, {
        "date_from": str(today),
        "date_to": str(tomorrow)
    })
    if filtered_docs.status_code == 200:
        docs = filtered_docs.json()
        print(f"✅ Filtered documents by date ({today} to {tomorrow}): {len(docs)} docs")
    else:
        print(f"❌ Failed: {filtered_docs.status_code}")
    
    # Test 9: Audit logs - Admin can access
    print("\n[TEST 9] Audit Logs - Admin Access")
    admin_audit = get_audit_logs(admin_token)
    if admin_audit.status_code == 200:
        logs = admin_audit.json()
        print(f"✅ Admin can access audit logs: {len(logs)} entries")
    else:
        print(f"❌ Admin audit access failed: {admin_audit.status_code}")
    
    # Test 10: Audit logs - Regular user cannot access
    print("\n[TEST 10] Audit Logs - Regular User Access (should fail)")
    user_audit = get_audit_logs(user_token)
    if user_audit.status_code == 403:
        print(f"✅ Regular user correctly denied access to audit logs (403)")
    elif user_audit.status_code == 200:
        print(f"⚠️ WARNING: Regular user can access audit logs (security issue)")
    else:
        print(f"❌ Unexpected response: {user_audit.status_code}")
    
    # Test 11: Check schema includes requested_by
    print("\n[TEST 11] Document Response Schema (verify requested_by)")
    admin_docs = get_documents(admin_token)
    if admin_docs.status_code == 200:
        docs = admin_docs.json()
        if docs:
            doc = docs[0]
            if 'requested_by' in doc:
                print(f"✅ Document includes 'requested_by' field")
                requested_by = doc['requested_by']
                if requested_by:
                    print(f"   Username: {requested_by.get('username')}")
                    print(f"   Email: {requested_by.get('email')}")
                    print(f"   ID: {requested_by.get('id')}")
            else:
                print(f"❌ Document missing 'requested_by' field")
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
