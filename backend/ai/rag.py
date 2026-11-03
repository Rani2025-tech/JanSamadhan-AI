import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
import numpy as np
from ai.embeddings import get_embedding, compute_similarity

class KnowledgeBaseRAG:
    def __init__(self, kb_dir: Optional[str] = None):
        if not kb_dir:
            kb_dir = str(Path(__file__).resolve().parent.parent / "kb")
        self.kb_dir = kb_dir
        self.faqs: List[Dict[str, Any]] = []
        self.faq_embeddings: List[np.ndarray] = []
        self._load_and_index()

    def _load_and_index(self):
        self.faqs = []
        self.faq_embeddings = []
        kb_path = Path(self.kb_dir)
        if not kb_path.exists():
            return

        for file in kb_path.glob("*.md"):
            try:
                content = file.read_text(encoding="utf-8")
                # Split by ## Q
                sections = re.split(r'\n(?=##\s*Q\d*:|\n##\s*Question)', content)
                for sec in sections:
                    lines = sec.strip().split("\n")
                    if not lines:
                        continue
                    q_line = lines[0].strip("# ").strip()
                    ans_text = "\n".join(lines[1:]).strip()
                    if q_line and ans_text:
                        full_txt = f"{q_line} {ans_text}"
                        self.faqs.append({
                            "question": q_line,
                            "answer": ans_text,
                            "source": file.name,
                            "full_text": full_txt
                        })
                        self.faq_embeddings.append(get_embedding(full_txt))
            except Exception as e:
                print(f"Error reading KB file {file}: {e}")

    def search_faq(self, query: str, threshold: float = 0.45) -> Optional[Dict[str, Any]]:
        """Search public-service FAQs using Multilingual RAG vector similarity."""
        if not self.faqs or not self.faq_embeddings:
            return None

        try:
            q_vec = get_embedding(query)
            best_idx = -1
            best_score = 0.0

            for idx, f_vec in enumerate(self.faq_embeddings):
                sim = compute_similarity(q_vec, f_vec)
                if sim > best_score:
                    best_score = sim
                    best_idx = idx

            if best_score >= threshold and best_idx >= 0:
                matched_faq = self.faqs[best_idx]
                return {
                    "question": matched_faq["question"],
                    "answer": matched_faq["answer"],
                    "source": matched_faq["source"],
                    "similarity": round(best_score, 2)
                }
        except Exception:
            return None
        return None

rag_engine = KnowledgeBaseRAG()

