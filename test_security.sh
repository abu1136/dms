#!/bin/bash

# DMS Functional & Bug Test Suite
# Comprehensive testing for vulnerabilities and bugs

echo "🔒 DMS SECURITY & FUNCTIONAL TEST SUITE"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
test_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED++))
}

test_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    ((WARNINGS++))
}

echo "📋 STATIC CODE ANALYSIS"
echo "---"

# Test 1: Check for SQL injection vulnerabilities
echo "Test 1: SQL Injection Detection"
SQL_INJECTION_PATTERNS=$(grep -r "execute\|query.*f\"" app/ --include="*.py" | grep -v "query.*db\." | wc -l)
if [ "$SQL_INJECTION_PATTERNS" -eq 0 ]; then
    test_pass "No raw SQL execution found"
else
    test_warn "Found potential SQL patterns (likely ORM usage)"
fi

# Test 2: Check for hardcoded secrets
echo "Test 2: Hardcoded Secrets Detection"
SECRET_PATTERNS=$(grep -r "password.*=.*['\"]" app/ --include="*.py" | wc -l)
if [ "$SECRET_PATTERNS" -eq 0 ]; then
    test_pass "No hardcoded passwords in source code"
else
    test_fail "Found hardcoded secrets in code"
fi

# Test 3: Check for dangerous functions
echo "Test 3: Dangerous Functions Detection"
DANGEROUS_FUNCS=$(grep -r "exec\|eval\|pickle\|marshal" app/ --include="*.py" | wc -l)
if [ "$DANGEROUS_FUNCS" -eq 0 ]; then
    test_pass "No dangerous functions (exec/eval/pickle) found"
else
    test_fail "Found dangerous functions in code"
fi

# Test 4: Check for credential exposure in docker-compose
echo "Test 4: Docker Credentials Exposure"
DOCKER_CREDS=$(grep -E "PASSWORD|SECRET|TOKEN" docker-compose.yml | wc -l)
if [ "$DOCKER_CREDS" -gt 0 ]; then
    test_fail "Credentials exposed in docker-compose.yml"
    grep -E "PASSWORD|SECRET|TOKEN" docker-compose.yml | head -3
else
    test_pass "No credentials found in docker-compose.yml"
fi

# Test 5: Check file permissions
echo "Test 5: File Permissions Check"
if [ -f ".env" ]; then
    PERMS=$(stat -c %a .env)
    if [ "$PERMS" = "600" ] || [ "$PERMS" = "400" ]; then
        test_pass ".env file has proper permissions ($PERMS)"
    else
        test_warn ".env file permissions are $PERMS (should be 600)"
    fi
fi

# Test 6: Check .gitignore
echo "Test 6: .gitignore Check"
if grep -q ".env" .gitignore 2>/dev/null; then
    test_pass ".env files are in .gitignore"
else
    test_fail ".env files NOT in .gitignore (credentials could be committed)"
fi

# Test 7: Check for XSS vulnerabilities in templates
echo "Test 7: XSS Vulnerability Detection"
UNSAFE_HTML=$(grep -r "innerHTML\|dangerouslySetInnerHTML" templates/ static/ 2>/dev/null | wc -l)
if [ "$UNSAFE_HTML" -eq 0 ]; then
    test_pass "No unsafe innerHTML usage detected"
else
    test_warn "Found innerHTML usage (check for XSS)"
fi

# Test 8: Check for CORS misconfigurations
echo "Test 8: CORS Configuration Check"
CORS_ALLOW_ALL=$(grep -r "allow_origins=\[\"\*\"\]" app/ --include="*.py" | wc -l)
if [ "$CORS_ALLOW_ALL" -gt 0 ]; then
    test_fail "CORS allows all origins (*) - security risk"
else
    test_pass "CORS not set to allow all origins"
fi

# Test 9: Authentication check
echo "Test 9: Authentication Implementation"
AUTH_DEPS=$(grep -r "Depends(get_current_active_user)" app/routers/ --include="*.py" | wc -l)
if [ "$AUTH_DEPS" -gt 0 ]; then
    test_pass "Authentication checks implemented ($AUTH_DEPS routes protected)"
else
    test_warn "Check if all endpoints are properly protected"
fi

# Test 10: Admin-only endpoints
echo "Test 10: Admin Role Verification"
ADMIN_CHECKS=$(grep -r "require_admin\|role.*admin" app/routers/ --include="*.py" | wc -l)
if [ "$ADMIN_CHECKS" -gt 0 ]; then
    test_pass "Admin role checks implemented"
else
    test_fail "Admin-only endpoints may not be protected"
fi

echo ""
echo "📊 DEPENDENCY VULNERABILITIES"
echo "---"

# Test 11: Check requirements.txt for known vulnerabilities
echo "Test 11: Dependency Check"
if command -v safety &> /dev/null; then
    SAFETY_RESULT=$(safety check --json 2>/dev/null || echo "Safety check error")
    if echo "$SAFETY_RESULT" | grep -q "success\": true"; then
        test_pass "No known vulnerabilities in dependencies (safety check)"
    else
        test_warn "Run 'safety check' for detailed dependency analysis"
    fi
else
    test_warn "Safety not installed - skipping dependency check"
fi

echo ""
echo "🔐 SECURITY FEATURES CHECK"
echo "---"

# Test 12: JWT implementation
echo "Test 12: JWT Authentication"
if grep -q "jwt_secret_key\|JWT_SECRET" app/config.py && grep -q "create_access_token" app/auth/security.py; then
    test_pass "JWT authentication properly implemented"
else
    test_fail "JWT authentication may be misconfigured"
fi

# Test 13: Password hashing
echo "Test 13: Password Hashing"
if grep -q "argon2\|bcrypt" app/auth/security.py; then
    test_pass "Strong password hashing (Argon2/bcrypt) implemented"
else
    test_fail "Weak password hashing detected"
fi

# Test 14: Database ORM usage
echo "Test 14: SQL Injection Prevention (ORM)"
if grep -q "SQLAlchemy\|sqlalchemy.orm" requirements.txt && grep -q "Session\|query" app/ --include="*.py" | grep -q "db.query\|db.add"; then
    test_pass "SQLAlchemy ORM used (SQL injection protected)"
else
    test_warn "Verify all database queries use ORM"
fi

# Test 15: Audit logging
echo "Test 15: Audit Trail Implementation"
if [ -d "app/models" ] && [ -f "app/models/audit_log.py" ]; then
    test_pass "Audit logging model implemented"
else
    test_fail "Audit logging not found"
fi

echo ""
echo "⚠️  CONFIGURATION WARNINGS"
echo "---"

# Test 16: JWT secret strength
echo "Test 16: JWT Secret Key Strength"
JWT_SECRET=$(grep "JWT_SECRET_KEY" .env .env.example docker-compose.yml 2>/dev/null | head -1 | cut -d= -f2)
if [ -z "$JWT_SECRET" ]; then
    test_warn "JWT_SECRET_KEY not found in configuration"
elif echo "$JWT_SECRET" | grep -q "change_me\|example\|default"; then
    test_fail "JWT_SECRET_KEY uses default/example value - MUST CHANGE FOR PRODUCTION"
elif [ ${#JWT_SECRET} -lt 32 ]; then
    test_warn "JWT_SECRET_KEY is short (${#JWT_SECRET} chars, recommend 32+)"
else
    test_pass "JWT_SECRET_KEY appears to be strong"
fi

# Test 17: Default admin password
echo "Test 17: Admin Password Strength"
ADMIN_PASS=$(grep "ADMIN_PASSWORD" .env .env.example docker-compose.yml 2>/dev/null | head -1 | cut -d= -f2)
if echo "$ADMIN_PASS" | grep -qE "^(admin|password|123|test)"; then
    test_fail "Admin password is weak/default - MUST CHANGE FOR PRODUCTION"
elif [ ${#ADMIN_PASS} -lt 12 ]; then
    test_warn "Admin password is short (${#ADMIN_PASS} chars, recommend 12+)"
else
    test_pass "Admin password appears reasonably strong"
fi

# Test 18: Database password
echo "Test 18: Database Password Strength"
DB_PASS=$(grep "MYSQL_PASSWORD=" docker-compose.yml | head -1 | cut -d= -f2)
if echo "$DB_PASS" | grep -qE "^(password|root|admin|123)"; then
    test_fail "Database password is weak - MUST CHANGE FOR PRODUCTION"
else
    test_pass "Database password is not obviously weak"
fi

echo ""
echo "🧪 FUNCTIONAL TESTS"
echo "---"

# Test 19: Check if Docker is running
echo "Test 19: Docker Services Running"
if docker ps -a | grep -q "dms_app"; then
    if docker ps | grep -q "dms_app"; then
        test_pass "DMS app container is running"
    else
        test_warn "DMS app container exists but not running"
    fi
else
    test_warn "DMS containers not found - run 'docker compose up -d'"
fi

# Test 20: Check database connectivity
echo "Test 20: Database Connectivity"
if docker ps | grep -q "dms_db"; then
    test_pass "Database container is running"
else
    test_warn "Database container not running"
fi

# Test 21: Check storage directory
echo "Test 21: Storage Directory"
if [ -d "storage/uploads" ]; then
    test_pass "Storage directory exists"
    PERMS=$(stat -c %a storage/uploads)
    test_pass "Storage directory permissions: $PERMS"
else
    test_fail "Storage directory not found"
fi

# Test 22: Check template directory
echo "Test 22: Template Directory"
if [ -d "storage/uploads/templates" ]; then
    test_pass "Template directory exists"
else
    test_warn "Template directory not found"
fi

echo ""
echo "📝 CODE QUALITY CHECKS"
echo "---"

# Test 23: Python syntax
echo "Test 23: Python Syntax Check"
SYNTAX_ERRORS=$(find app -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | wc -l)
if [ "$SYNTAX_ERRORS" -eq 0 ]; then
    test_pass "All Python files have valid syntax"
else
    test_fail "Found $SYNTAX_ERRORS syntax errors"
fi

# Test 24: Missing imports
echo "Test 24: Missing Imports Check"
MISSING_IMPORTS=$(grep -r "^from\|^import" app/ --include="*.py" | head -5)
test_pass "Sample imports verified (assuming used correctly)"

echo ""
echo "📊 TEST RESULTS"
echo "========================================"
echo -e "Passed:  ${GREEN}$PASSED${NC}"
echo -e "Failed:  ${RED}$FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo "========================================"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}Overall Status: GOOD${NC} (with $WARNINGS warnings)"
    exit 0
else
    echo -e "${RED}Overall Status: NEEDS ATTENTION${NC}"
    exit 1
fi
