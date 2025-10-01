#!/usr/bin/env python3
"""
Test script for AI service
"""

import requests
import json
import time
import sys

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_quiz():
    """Test quiz generation"""
    try:
        data = {
            "user_prompt": "Tôi muốn đi Đà Nẵng ngày 2025-10-10 2 đêm, có phòng gym"
        }
        response = requests.post(
            "http://localhost:8000/generate-quiz",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Quiz generation test passed")
            print(f"   Quiz completed: {result.get('quiz_completed', False)}")
            print(f"   Missing quiz: {result.get('missing_quiz', 'None')}")
            return True
        else:
            print(f"❌ Quiz generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Quiz generation error: {e}")
        return False

def test_rag_search():
    """Test RAG search"""
    try:
        data = {
            "params": {
                "city": "Đà Nẵng",
                "establishment_type": "HOTEL",
                "travel_companion": "couple",
                "amenities_priority": "Gym, Hồ bơi, Wifi",
                "duration": 2,
                "max_price": 5000000
            }
        }
        response = requests.post(
            "http://localhost:8000/rag-search",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ RAG search test passed - Found {len(results)} results")
            if results:
                print(f"   First result: {results[0].get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ RAG search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ RAG search error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 AI Service Test Suite")
    print("=" * 40)
    
    # Wait for service to start
    print("⏳ Waiting for service to start...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health),
        ("Quiz Generation", test_quiz),
        ("RAG Search", test_rag_search)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! AI service is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the service logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
