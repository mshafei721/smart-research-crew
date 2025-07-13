#!/usr/bin/env python3
"""
Manual test script to verify SSE functionality
"""
import asyncio
import aiohttp
import json


async def test_sse():
    """Test SSE endpoint manually"""
    url = "http://localhost:8000/sse"
    params = {
        "topic": "Artificial Intelligence in Healthcare",
        "guidelines": "Focus on recent developments and practical applications",
        "sections": "Introduction,Current Applications,Future Prospects"
    }
    
    print("🚀 Testing SSE endpoint...")
    print(f"Topic: {params['topic']}")
    print(f"Sections: {params['sections']}")
    print("-" * 60)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            print(f"Status: {response.status}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print("-" * 60)
            
            async for line in response.content:
                text = line.decode('utf-8').strip()
                if text.startswith('data:'):
                    try:
                        data = json.loads(text[5:])  # Remove 'data: ' prefix
                        print(f"\n📍 Event Type: {data.get('type')}")
                        
                        if data['type'] == 'status':
                            print(f"   Status: {data.get('message')}")
                            print(f"   Progress: {data.get('progress')}%")
                        
                        elif data['type'] == 'section_start':
                            print(f"   Section: {data.get('section')}")
                            print(f"   Number: {data.get('section_number')}/{data.get('total_sections')}")
                        
                        elif data['type'] == 'section_complete':
                            print(f"   Section: {data.get('section')}")
                            print(f"   Content Length: {len(data.get('content', ''))} chars")
                            print(f"   Sources: {len(data.get('sources', []))} sources")
                            print(f"   Progress: {data.get('progress')}%")
                        
                        elif data['type'] == 'report_complete':
                            print(f"   Report Length: {len(data.get('content', ''))} chars")
                            print(f"   Sections Completed: {data.get('sections_completed')}/{data.get('total_sections')}")
                            print(f"   Progress: {data.get('progress')}%")
                            print("\n✅ Research complete!")
                            break
                        
                        elif data['type'] == 'error':
                            print(f"   ❌ Error: {data.get('message')}")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse event: {e}")
                        print(f"Raw line: {text}")


if __name__ == "__main__":
    print("Note: Make sure the backend server is running with:")
    print("  cd backend && python crew.py --server")
    print()
    
    try:
        asyncio.run(test_sse())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")