#!/usr/bin/env python3
"""
Quick debug script to verify current state
"""

def check_wizard_file():
    wizard_file = "frontend/src/Wizard.tsx"
    
    print("🔍 Checking current Wizard.tsx content...")
    
    try:
        with open(wizard_file, 'r') as f:
            content = f.read()
            
        # Check for the critical fix
        has_hardcoded = "http://localhost:8000/sse" in content
        has_relative = "new EventSource(`/sse?" in content or "new EventSource(sseUrl)" in content
        has_debug_logs = "Creating EventSource with URL" in content
        
        print(f"❌ Still has hardcoded URL: {has_hardcoded}")
        print(f"✅ Has relative URL: {has_relative}")  
        print(f"✅ Has debug logs: {has_debug_logs}")
        
        if has_hardcoded:
            print("\n🚨 CRITICAL: Still found hardcoded URL in file!")
            # Find the line
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if "http://localhost:8000/sse" in line:
                    print(f"   Line {i}: {line.strip()}")
        
        if has_relative and has_debug_logs:
            print("\n✅ File changes look correct!")
        else:
            print("\n❌ Something is wrong with the file changes")
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    check_wizard_file()