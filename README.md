# ⚡ RepoMind — AST-Aware Codebase Intelligence & Patch Generator

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20Demo-ff4b4b?style=for-the-badge&logo=streamlit)](https://codegraphrag-svk008.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![ChromaDB](https://img.shields.io/badge/Vector%20DB-ChromaDB-orange?style=for-the-badge)](https://www.trychroma.com/)
[![Groq API](https://img.shields.io/badge/LLM-Groq%20Llama%203-green?style=for-the-badge)](https://groq.com/)

> **RepoMind** bridges the gap between raw source code and artificial intelligence. By combining Abstract Syntax Tree (AST) structural parsing, persistent vector storage, dependency graph mapping, and a Llama-3-powered ReAct agent, RepoMind enables developers to query complex codebases, inspect internal symbol hierarchies, and generate production-ready unified `git diff` patches automatically.

---

## 🔗 Live Application
Try the live application without installing anything locally:
👉 **[https://codegraphrag-svk008.streamlit.app/](https://codegraphrag-svk008.streamlit.app/)**

---

## 🎯 Motivation & Why We Built This

Navigating and understanding legacy or large-scale codebases is one of the biggest bottlenecks in software engineering:
1. **Context Fracturing in Standard RAG:** Standard LLM wrappers rely on naive text chunking (e.g., splitting by fixed 1000-character windows). This breaks class structures, splits functions in half, and loses cross-file variable scopes.
2. **Slow Developer Onboarding:** Engineers spend hours opening dozens of files manually just to understand function calls, dependencies, and execution paths.
3. **Manual Patching Effort:** Identifying a bug and writing boilerplate fixes or diff files takes up valuable development time.

### **The Solution**
RepoMind solves these issues by parsing Python files directly at the **syntactic level** using Abstract Syntax Trees (`ast`). It extracts structural metadata (functions, parameters, classes, inheritance, docstrings, line numbers), maps inter-file dependency graphs, embeds structural chunks into **ChromaDB**, and passes them to a **ReAct (Reasoning + Acting) Agent**.

---

## 🛠️ Technology Stack & Component Roles

| Technology / Tool | Purpose & Role in RepoMind |
| :--- | :--- |
| **Python `ast` Engine** | Standard library parser used to inspect Python source code syntactically without executing it. Extracts exact classes, functions, docstrings, and parameter types. |
| **ChromaDB** | Vector Database used to store and index code snippets alongside structural metadata for fast cosine-similarity semantic retrieval. |
| **Groq API (Llama 3)** | High-speed LLM inference engine providing low-latency reasoning for our ReAct agent loop. |
| **Streamlit** | Frontend web UI providing an interactive, tabbed dashboard with a clean GitHub-inspired light aesthetic. |
| **ReAct Framework** | Interleaved *Thought $\rightarrow$ Action $\rightarrow$ Observation* execution loop that iteratively gathers context across dependency graphs before generating answers or code diffs. |
| **Unified Git Diff Synthesizer** | Engine that formats AI-generated code fixes into strict `.patch` formats readable by standard `git apply`. |

---

## 📂 Interactive Tabs & Example Scenarios

### **Tab 1: 💬 Codebase QA & Search**
* **Concept:** Perform hybrid retrieval across your codebase combining vector semantic search with AST dependency graphs to get accurate, hallucination-free answers.
* **How it works:** Input a question $\rightarrow$ Hybrid Retriever queries ChromaDB & `repo_graph.json` $\rightarrow$ ReAct Agent analyzes context $\rightarrow$ Synthesizes answer with exact file references and line numbers.
* **Example Queries to Try:**
  1. *"How are function calls extracted across files and mapped into graph edges?"*
  2. *"Explain the relationship between `retriever.py` and `vector_store.py`."*
  3. *"Where is the vector database initialized, and what metadata fields are stored during ingestion?"*
  4. *"What error handling exists if an imported module cannot be parsed by `code_parser.py`?"*

---

### **Tab 2: 🛠️ Automated Patch Generator**
* **Concept:** Input a natural language description of a bug or feature request, and receive an automatically synthesized `git diff` patch that can be applied directly to the codebase.
* **How it works:** Input bug description $\rightarrow$ Agent retrieves relevant source code $\rightarrow$ Reasons over logic flaws $\rightarrow$ Outputs unified `git diff` $\rightarrow$ Option to save directly to `fix.patch`.
* **Example Bug Descriptions to Try:**
  1. *"Add a safety fallback in `CodeASTParser` if a docstring is missing or returns `None`."*
  2. *"Ensure `graph_builder.py` resolves relative imports correctly when generating file adjacency edges."*
  3. *"Add docstring and parameter type checks to `vector_store.py` to prevent indexing empty code chunks."*
  4. *"Add error handling for missing Groq API keys with a clear user alert in `llm_engine.py`."*

---

### **Tab 3: 📁 Repository Symbol Explorer**
* **Concept:** An architectural code navigator that allows developers to inspect functions, parameters, return types, classes, inheritance bases, and docstrings across every scanned file.
* **How it works:** Select any file from the repository dropdown $\rightarrow$ Instantly view structured metrics, expanded function metadata, and class definitions extracted directly by the AST engine.
* **Example Usage Scenarios:**
  * **Docstring Audit:** Select `repo_scanner.py` to check which functions are missing documentation.
  * **Parameter & Type Inspection:** Inspect `code_parser.py` to review function signatures and line-number ranges.
  * **Architecture Mapping:** Select `app.py` to verify top-level UI imports and layout blocks.

---

## 🔄 System Architecture & Data Flow

```
   +------------------------------------------------------------------------+
   |                     RepoMind Pipeline Architecture                      |
   +------------------------------------------------------------------------+
                                       |
                                       v
                             [ Target Repository ]
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
         [ Python AST Parser ]                    [ Dependency Scanner ]
         - Function bounds                        - File imports
         - Class inheritance                      - Module relationships
         - Parameters & docstrings                         |
                   |                                       v
                   v                              [ repo_graph.json ]
         [ ChromaDB Vector Store ]                         |
                   |                                       |
                   +-------------------+-------------------+
                                       |
                                       v
                         [ Hybrid Context Retriever ]
                                       |
                                       v
                            [ ReAct Agent (Groq) ]
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
         [ Codebase QA Answer ]                   [ Unified git diff Patch ]
```

---

## 🚀 Local Installation & Setup Guide

Want to run RepoMind locally on your machine? Follow these simple steps:

### **1. Clone the Repository**
```bash
git clone https://github.com/ShashwatKamlapure008-hub/CodeGraph_RAG.git
cd CodeGraph_RAG
```

### **2. Create and Activate a Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Set Up Environment Variables**
Create a `.env` file in the root directory (or export it in your shell):
```env
GROQ_API_KEY=your_groq_api_key_here
```

### **5. Launch the Streamlit App**
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 🔮 Future Scope & Roadmap

- [ ] **Multi-Language Parsing:** Extend AST parsing support to JavaScript/TypeScript, Go, and Rust using `tree-sitter`.
- [ ] **Automated PR Creation:** Integrate GitHub REST API to automatically create Pull Requests directly from generated `.patch` files.
- [ ] **Interactive 3D Graph Visualization:** Implement interactive D3.js or PyVis force-directed network graphs to visualize multi-repo architecture.
- [ ] **CI/CD Integration:** Package RepoMind into a GitHub Action that audits incoming PRs for missing docstrings, architectural anomalies, and context regressions.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
