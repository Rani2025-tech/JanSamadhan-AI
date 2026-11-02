import sys
import os

def test_imports():
    print("Testing imports...")
    
    try:
        import fastapi
        print("[OK] FastAPI")
    except ImportError as e:
        print(f"[FAIL] FastAPI: {e}")
        return False
        
    try:
        from langchain_groq import ChatGroq
        print("[OK] LangChain-Groq")
    except ImportError as e:
        print(f"[FAIL] LangChain-Groq: {e}")
        return False
        
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        print("[OK] LangChain Text Splitters")
    except ImportError as e:
        print(f"[FAIL] LangChain Text Splitters: {e}")
        return False
        
    try:
        import faiss
        print("[OK] FAISS")
    except ImportError as e:
        print(f"[FAIL] FAISS: {e}")
        return False
        
    return True

def test_env_vars():
    print("\\nTesting environment variables...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["GROQ_API_KEY", "JWT_SECRET", "ADMIN_PASSWORD"]
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"[OK] {var}: ****...")
        else:
            print(f"[FAIL] {var}: Not set")
            all_good = False
            
    return all_good

def test_groq_connection():
    print("\\nTesting Groq API connection...")
    
    try:
        from langchain_groq import ChatGroq
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("[FAIL] GROQ_API_KEY not found")
            return False
            
        llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key)
        response = llm.invoke("Hello")
        print("[OK] Groq API working")
        return True
        
    except Exception as e:
        print(f"[FAIL] Groq API: {e}")
        return False

if __name__ == "__main__":
    print("Backend Health Check")
    print("=" * 50)
    
    tests = [test_imports, test_env_vars, test_groq_connection]
    results = []
    
    for test in tests:
        results.append(test())
        
    print("\\n" + "=" * 50)
    print("SUMMARY:")
    
    if all(results):
        print("All tests PASSED!")
        sys.exit(0)
    else:
        print("Some tests FAILED!")
        sys.exit(1)