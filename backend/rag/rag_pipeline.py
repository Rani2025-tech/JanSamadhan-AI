import os
from dotenv import load_dotenv
from backend.core.llm_wrapper import chat, chat_stream, LLMCompat

try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_core.prompts import PromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    from langchain_community.embeddings import FastEmbedEmbeddings
except ImportError:
    PyPDFLoader = None
    RecursiveCharacterTextSplitter = None
    FAISS = None
    PromptTemplate = None
    RunnablePassthrough = None
    StrOutputParser = None
    FastEmbedEmbeddings = None

load_dotenv()

GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_index")

# ── Global Cache ─────────────────────────────────────────────────
_embeddings_cache  = None
_vectorstore_cache = None
_llm_cache         = None

def get_embeddings():
    global _embeddings_cache
    if _embeddings_cache is None:
        print("Loading embeddings model (first time only)...")
        # FastEmbedEmbeddings uses ONNX runtime (~50MB RAM vs ~400MB for PyTorch)
        _embeddings_cache = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    return _embeddings_cache

def load_vectorstore() -> FAISS:
    global _vectorstore_cache
    if _vectorstore_cache is None:
        print("Loading FAISS index (first time only)...")
        try:
            # allow_dangerous_deserialization=True is safe here because the
            # FAISS index is generated internally by this app (rebuild_index.py)
            # and never loaded from untrusted external sources.
            _vectorstore_cache = FAISS.load_local(
                FAISS_INDEX_PATH,
                get_embeddings(),
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            print(f"FAISS load error: {e}")
            raise RuntimeError(
                f"Failed to load FAISS index from '{FAISS_INDEX_PATH}'. "
                f"Run 'python rebuild_index.py' to rebuild it. Error: {e}"
            )
    return _vectorstore_cache

def get_llm():
    global _llm_cache
    if _llm_cache is None:
        print("Initializing LLM (first time only)...")
        _llm_cache = LLMCompat()
    return _llm_cache

# ── Shared Prompt ─────────────────────────────────────────────────
if PromptTemplate is not None:
    PROMPT = PromptTemplate.from_template("""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are JanSamadhan, a helpful and empathetic AI assistant for citizen grievances and public civic services.
Be warm, polite and responsive. For greetings like "hi", "hello", "hey" — respond warmly and introduce yourself as JanSamadhan.
When answering civic queries, use the guidance and procedures from the context below.
Do NOT invent contact details, department names, or rules not supported by context.
Provide clear, actionable steps for the citizen to register or resolve their issue.
If context is missing, guide the citizen politely on general grievance filing procedures.
Always reply in the language requested by the citizen instruction below.
{lang_instruction}
<|eot_id|><|start_header_id|>user<|end_header_id|>
Context:
{context}

Question: {question}

Remember: Be empathetic, clear, and helpful. Always assist citizens with their grievance questions.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>""")
else:
    PROMPT = None

from backend.core.messages import t

LANGUAGE_INSTRUCTIONS = {
    "en": "Answer in English with complete details.",
    "hi": "Answer in Hindi language only. Use Devanagari script. Provide complete details with specific numbers, amounts, and names. Do not use any English words.",
    "or": "Answer in Odia language only. Use Odia script (ଓଡ଼ିଆ ଲିପି). Provide complete details with specific numbers, amounts, and names. Do not use any English words. Write everything in Odia.",
    "mr": "Answer in Marathi language only. Use Devanagari script (मराठी). Provide complete details with specific numbers, amounts, and names.",
    "te": "Answer in Telugu language only. Use Telugu script (తెలుగు). Provide complete details with specific numbers, amounts, and names.",
    "ta": "Answer in Tamil language only. Use Tamil script (தமிழ்). Provide complete details with specific numbers, amounts, and names.",
    "bn": "Answer in Bengali language only. Use Bengali script (বাংলা). Provide complete details with specific numbers, amounts, and names."
}

# ── Shared helper functions ───────────────────────────────────────
def translate_for_search(question: str, lang: str) -> str:
    return t(question, lang)

def format_docs(docs):
    return "\n".join(doc.page_content for doc in docs)

def prepare_prompt(question: str, language: str):
    from backend.core.utils import detect_language
    lang = detect_language(question) if language == "auto" else language
    search_question = translate_for_search(question, lang)
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(lang, "Answer in English.")

    vectorstore = load_vectorstore()
    retriever   = vectorstore.as_retriever(search_kwargs={"k": 10})
    docs        = retriever.invoke(search_question)
    context     = format_docs(docs)

    final_prompt = PROMPT.format(
        context=context,
        question=question,
        lang_instruction=lang_instruction
    )
    return final_prompt

# ── PDF Ingestion ─────────────────────────────────────────────────
def ingest_pdf(pdf_path: str):
    loader   = PyPDFLoader(pdf_path)
    docs     = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks   = splitter.split_documents(docs)

    if not chunks:
        print(f"WARNING: No text extracted from {pdf_path} — skipping (likely a scanned/image PDF).")
        return 0

    embeddings = get_embeddings()

    if os.path.exists(FAISS_INDEX_PATH):
        try:
            existing = FAISS.load_local(
                FAISS_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            existing.add_documents(chunks)
            existing.save_local(FAISS_INDEX_PATH)
            print(f"Merged {len(chunks)} chunks into existing FAISS index")
        except Exception as e:
            print(f"Existing index corrupted, rebuilding from scratch: {e}")
            vectorstore = FAISS.from_documents(chunks, embeddings)
            vectorstore.save_local(FAISS_INDEX_PATH)
        # Reset cache so new docs are picked up
        global _vectorstore_cache
        _vectorstore_cache = None
    else:
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local(FAISS_INDEX_PATH)
        print(f"Created new FAISS index with {len(chunks)} chunks")

    return len(chunks)

# ── Answer functions ──────────────────────────────────────────────
def get_answer(question: str, language: str = "auto") -> str:
    try:
        import html as _html
        final_prompt = prepare_prompt(question, language)
        content = chat(final_prompt)
        content = result.content if hasattr(result, 'content') else str(result)
        return _html.unescape(content)
    except Exception as e:
        print(f"Error in get_answer: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def get_answer_stream(question: str, language: str = "auto"):
    try:
        import html as _html
        final_prompt = prepare_prompt(question, language)
        for token in chat_stream(final_prompt):
            content = token.content if hasattr(token, 'content') else str(token)
            yield _html.unescape(content)
    except Exception as e:
        print(f"Error in get_answer_stream: {str(e)}")
        import traceback
        traceback.print_exc()
        yield f"Error: {str(e)}"
