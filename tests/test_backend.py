#!/usr/bin/env python3
"""Test script to verify backend setup and dependencies."""

import sys
import os

def test_imports():
    """Test if all required packages are importable."""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✓ FastAPI")
    except ImportError as e:
        print(f"✗ FastAPI: {e}")
        return False
        
    try:
        import langchain
        print("✓ LangChain")
    except ImportError as e:
        print(f"✗ LangChain: {e}")
        return False
        
    try:
        from langchain_groq import ChatGroq
        print("✓ LangChain-Groq")
    except ImportError as e:
        print(f"✗ LangChain-Groq: {e}")
        return False
        
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        print("✓ LangChain Text Splitters")
    except ImportError as e:
        print(f"✗ LangChain Text Splitters: {e}")
        return False
        
    try:
        import faiss
        print("✓ FAISS")
    except ImportError as e:
        print(f"✗ FAISS: {e}")
        return False
        
    return True

def test_env_vars():
    """Test if required environment variables are set."""
    print("\nTesting environment variables...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["GROQ_API_KEY", "JWT_SECRET", "ADMIN_PASSWORD"]
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {'*' * len(value[:4]) + '...'}")
        else:
            print(f"✗ {var}: Not set")
            all_good = False
            
    return all_good

def test_groq_connection():
    """Test Groq API connection."""
    print("\nTesting Groq API connection...")
    
    try:
        from langchain_groq import ChatGroq
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("✗ GROQ_API_KEY not found in environment")
            return False
            
        llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key)
        response = llm.invoke("Say hello in one word")
        print(f"✓ Groq API working: {response.content[:20]}...")
        return True
        
    except Exception as e:
        print(f"✗ Groq API connection failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Backend Health Check")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Environment Variables", test_env_vars), 
        ("Groq API Connection", test_groq_connection)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
        
    print("\n" + "=" * 50)
    print("SUMMARY:")
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\nAll tests passed! Backend should work properly.")
        return 0
    else:
        print("\nSome tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())