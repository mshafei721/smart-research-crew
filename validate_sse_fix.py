#!/usr/bin/env python3
"""
Comprehensive validation script for SSE real-time updates fix.
This script validates all the changes made to fix the frontend SSE issues.
"""

import os
import sys
import subprocess
import requests
import asyncio
import aiohttp
import json
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step, status=""):
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔍"
    print(f"{status_icon} {step}" + (f" - {status}" if status else ""))

def check_file_exists(filepath):
    """Check if a file exists and return its status"""
    path = Path(filepath)
    return path.exists()

def check_file_contains(filepath, search_text):
    """Check if a file contains specific text"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            return search_text in content
    except:
        return False

def test_backend_health():
    """Test if backend server is healthy"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_frontend_access():
    """Test if frontend dev server is accessible"""
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        return response.status_code == 200
    except:
        return False

async def test_sse_endpoint():
    """Test SSE endpoint functionality"""
    try:
        url = "http://localhost:8000/sse"
        params = {
            "topic": "Test SSE Validation",
            "guidelines": "Quick test",
            "sections": "Introduction"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status != 200:
                    return False
                
                # Read first few events to verify it's working
                event_count = 0
                async for line in response.content:
                    text = line.decode('utf-8').strip()
                    if text.startswith('data:'):
                        event_count += 1
                        if event_count >= 3:  # Got enough events to confirm it works
                            return True
                            
                return event_count > 0
    except:
        return False

def main():
    print_header("SSE Real-Time Updates Fix Validation")
    
    # Phase 1: Critical CORS Fix Validation
    print_header("PHASE 1: CORS Fix Validation")
    
    wizard_file = "frontend/src/Wizard.tsx"
    
    # Check if hardcoded URL was removed
    has_hardcoded_url = check_file_contains(wizard_file, "http://localhost:8000/sse")
    has_relative_url = check_file_contains(wizard_file, 'new EventSource(`/sse?${params}`)')
    
    print_step("Removed hardcoded localhost URL", "PASS" if not has_hardcoded_url else "FAIL")
    print_step("Added relative URL for proxy", "PASS" if has_relative_url else "FAIL")
    
    if has_hardcoded_url:
        print("   ❌ Found hardcoded URL - CORS issue still present!")
    if has_relative_url:
        print("   ✅ Using relative URL - will use Vite proxy correctly")
    
    # Phase 2: Connection State Management
    print_header("PHASE 2: Connection State Management")
    
    has_connection_state = check_file_contains(wizard_file, "ConnectionState")
    has_error_types = check_file_contains(wizard_file, "SSEError")
    has_ref_management = check_file_contains(wizard_file, "evtSourceRef")
    has_cleanup = check_file_contains(wizard_file, "useEffect")
    
    print_step("Added connection state types", "PASS" if has_connection_state else "FAIL")
    print_step("Added error handling types", "PASS" if has_error_types else "FAIL") 
    print_step("Added EventSource ref management", "PASS" if has_ref_management else "FAIL")
    print_step("Added cleanup useEffect", "PASS" if has_cleanup else "FAIL")
    
    # Phase 3: Retry Logic and Error Boundaries
    print_header("PHASE 3: Retry Logic & Error Boundaries")
    
    has_retry_logic = check_file_contains(wizard_file, "connectWithRetry")
    has_retry_constants = check_file_contains(wizard_file, "MAX_RETRIES")
    has_error_boundary = check_file_exists("frontend/src/components/ErrorBoundary.tsx")
    
    print_step("Added retry logic", "PASS" if has_retry_logic else "FAIL")
    print_step("Added retry constants", "PASS" if has_retry_constants else "FAIL")
    print_step("Created error boundary component", "PASS" if has_error_boundary else "FAIL")
    
    # Phase 4: Runtime Testing
    print_header("PHASE 4: Runtime Validation")
    
    backend_healthy = test_backend_health()
    frontend_accessible = test_frontend_access()
    
    print_step("Backend server health", "PASS" if backend_healthy else "FAIL")
    print_step("Frontend dev server", "PASS" if frontend_accessible else "FAIL")
    
    if backend_healthy and frontend_accessible:
        print_step("Testing SSE endpoint...")
        try:
            sse_working = asyncio.run(test_sse_endpoint())
            print_step("SSE endpoint functionality", "PASS" if sse_working else "FAIL")
        except Exception as e:
            print_step("SSE endpoint functionality", "FAIL")
            print(f"   Error: {e}")
    else:
        print_step("SSE endpoint test", "SKIP - servers not running")
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    critical_fixes = [
        not has_hardcoded_url,  # Fixed CORS issue
        has_relative_url,       # Using proxy correctly
        backend_healthy,        # Backend working
        frontend_accessible     # Frontend accessible
    ]
    
    enhancement_fixes = [
        has_connection_state,   # Connection management
        has_error_types,        # Error handling
        has_retry_logic,        # Retry logic
        has_error_boundary      # Error boundaries
    ]
    
    critical_score = sum(critical_fixes)
    enhancement_score = sum(enhancement_fixes)
    
    print(f"Critical Fixes: {critical_score}/4 {'✅' if critical_score == 4 else '❌'}")
    print(f"Enhancement Fixes: {enhancement_score}/4 {'✅' if enhancement_score == 4 else '❌'}")
    
    if critical_score == 4:
        print("\n🎉 SUCCESS: Real-time updates should now work!")
        print("   The critical CORS issue has been fixed.")
        print("   Try the frontend at http://localhost:5173")
    else:
        print("\n⚠️  ISSUES FOUND: Some critical fixes are missing.")
        print("   Real-time updates may still not work properly.")
    
    print("\n📋 Next Steps:")
    print("1. Open browser to http://localhost:5173")
    print("2. Fill in research form and click 'Launch Research'")
    print("3. You should see:")
    print("   - Connection status indicator")
    print("   - Real-time progress updates")
    print("   - Sections appearing as they complete")
    print("   - Final report display")
    
    if enhancement_score < 4:
        print("\n🔧 Optional Enhancements Available:")
        if not has_connection_state:
            print("   - Add connection state management for better UX")
        if not has_retry_logic:
            print("   - Add automatic retry on connection failure")
        if not has_error_boundary:
            print("   - Add error boundary for graceful error handling")

if __name__ == "__main__":
    main()