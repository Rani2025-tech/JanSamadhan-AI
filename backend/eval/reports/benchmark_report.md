# JanSamadhan AI & NLP Benchmark Suite Report

**Generated:** 2026-11-05 17:33:36  
**Benchmark Dataset Size:** n=10 complaints across 7 Indian languages  

---

## 1. Overall Category Classification & Latency

| Classifier / Engine | Accuracy | Raw Correct | Mean Latency | p95 Latency | Operational Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Rules (Offline Fallback)** | **90.0%** | 9/10 | 25.7 ms | 38.03 ms | Zero network dependency, keyword slot-filler |
| **scikit-learn Baseline** | **100.0%** | 10/10 | 2.75 ms | 12.05 ms | scikit-learn TF-IDF char n-grams + LogisticRegression |
| **Gemini Live LLM** | **90.0%** | 9/10 | 22.18 ms | 26.65 ms | Cloud LLM (structured JSON mode) |

---

## 2. Per-Language Accuracy Breakdown

| Language | **Rules (Offline Fallback)** | **scikit-learn Baseline** | **Gemini Live LLM** |
| :--- | :---: | :---: | :---: |
| **Odia** | 90.0% (9/10) | 100.0% (10/10) | 90.0% (9/10) |
| **Hindi** | — | — | — |
| **Bengali** | — | — | — |
| **Telugu** | — | — | — |
| **Tamil** | — | — | — |
| **Marathi** | — | — | — |
| **English** | — | — | — |

---

## 3. Per-Category Accuracy Breakdown

| Civic Category | **Rules (Offline Fallback)** | **scikit-learn Baseline** | **Gemini Live LLM** |
| :--- | :---: | :---: | :---: |
| **Water Supply** | 66.67% (2/3) | 100.0% (3/3) | 66.67% (2/3) |
| **Road Infrastructure** | 100.0% (2/2) | 100.0% (2/2) | 100.0% (2/2) |
| **Electricity** | 100.0% (2/2) | 100.0% (2/2) | 100.0% (2/2) |
| **Sanitation** | 100.0% (1/1) | 100.0% (1/1) | 100.0% (1/1) |
| **Public Health** | 100.0% (1/1) | 100.0% (1/1) | 100.0% (1/1) |
| **Ration / PDS** | 100.0% (1/1) | 100.0% (1/1) | 100.0% (1/1) |

---

## 4. Error Analysis (Discrepancy Samples)

### Rules (Offline Fallback) (Errors: 1/10)
| ID | Language | Input Text | Expected Category | Predicted | Conf |
| :--- | :--- | :--- | :--- | :--- | :---: |
| TEST-02 | Odia | "ପାଣିରେ କାଦୁଅ ଓ ଦୁର୍ଗନ୍ଧ ବାହାରୁଛି ପିଲାମାନେ ଅସୁସ୍ଥ ହ..." | Water Supply | Sanitation | 81.00% |

### scikit-learn Baseline (Errors: 0/10)
No classification discrepancies encountered on this test slice.

### Gemini Live LLM (Errors: 1/10)
| ID | Language | Input Text | Expected Category | Predicted | Conf |
| :--- | :--- | :--- | :--- | :--- | :---: |
| TEST-02 | Odia | "ପାଣିରେ କାଦୁଅ ଓ ଦୁର୍ଗନ୍ଧ ବାହାରୁଛି ପିଲାମାନେ ଅସୁସ୍ଥ ହ..." | Water Supply | Sanitation | 81.00% |
