#!/usr/bin/env python3
"""Rebuild FAISS index from scratch."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
from dotenv import load_dotenv

load_dotenv()

def rebuild_index():
    """Rebuild FAISS index from all PDFs in data/ folder."""
    print("Rebuilding FAISS index...")
    
    # Import after loading env vars
    from backend.rag.rag_pipeline import ingest_pdf, get_embeddings
    from backend.core.utils import get_all_pdfs, ensure_folders
    from langchain_community.vectorstores import FAISS
    
    ensure_folders()
    
    # Remove existing index
    faiss_path = os.getenv("FAISS_INDEX_PATH", "faiss_index")
    if os.path.exists(faiss_path):
        shutil.rmtree(faiss_path)
        print(f"Removed existing index at {faiss_path}")
    
    # Get all PDFs
    pdfs = get_all_pdfs()
    if not pdfs:
        print("No PDF files found in data/ folder")
        print("Add some PDF files to the data/ folder first")
        return False
    
    print(f"Found {len(pdfs)} PDF files:")
    for pdf in pdfs:
        print(f"   - {os.path.basename(pdf)}")
    
    # Process each PDF
    total_chunks = 0
    try:
        for i, pdf_path in enumerate(pdfs, 1):
            print(f"\nProcessing {i}/{len(pdfs)}: {os.path.basename(pdf_path)}")
            chunks = ingest_pdf(pdf_path)
            total_chunks += chunks
            print(f"   Added {chunks} chunks")
            
        print(f"\nSuccessfully rebuilt FAISS index with {total_chunks} total chunks")
        return True
        
    except Exception as e:
        print(f"\nError rebuilding index: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = rebuild_index()
    if not success:
        exit(1)