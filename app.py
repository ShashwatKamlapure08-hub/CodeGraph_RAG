import streamlit as st
import os
import json
from repo_scanner import scan_repository
from graph_builder import build_dependency_graph
from vector_store import CodeVectorStore
from retriever import GraphAugmentedRetriever
from llm_engine import ReActRepoAgent
from patch_generator import PatchSynthesizer

# Page Configuration
st.set_page_config(
    page_title="RepoMind — Codebase QA & Bug Fixer",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for Crisp White, Green, and Black Aesthetic
st.markdown("""
<style>
    .main-header {
        font-size: 4rem !important;
        font-weight: 800;
        color: #24292e;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #586069;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #2ea043;
        color: white;
        font-weight: 600;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #2c974b;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<p class="main-header">⚡ REPOMIND ’26</p>',unsafe_allow_html=True)
st.markdown('<p class="sub-header">AST-Aware Codebase Intelligence, Hybrid Retrieval, and Automated Patch Generation.</p>', unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("### ⚙️ Repository Control")
repo_path = st.sidebar.text_input("Target Repository Path", value=".")
index_button = st.sidebar.button("Index Codebase")

if index_button:
    with st.spinner("Scanning AST, building dependency graph, and embedding into ChromaDB..."):
        try:
            scanned_graph = scan_repository(repo_path)
            with open("repo_graph.json", "w", encoding="utf-8") as f:
                json.dump(scanned_graph, f)
            
            build_dependency_graph("repo_graph.json")
            store = CodeVectorStore()
            indexed_count = store.index_codebase("repo_graph.json")
            
            st.sidebar.success(f"Indexed {indexed_count} code symbols successfully!")
        except Exception as e:
            st.sidebar.error(f"Error during indexing: {e}")

# Main Interface Tabs
tab1, tab2, tab3 = st.tabs(["💬 Codebase QA & Search", "🛠️ Automated Patch Generator", "📁 Repository Symbol Explorer"])

with tab1:
    st.markdown("### Codebase Intelligence & Search")
    user_query = st.text_area("Enter your technical question or code analysis query:", height=100, placeholder="e.g., How are function calls extracted across files and mapped into graph edges?")
    
    if st.button("Run Analysis"):
        if not user_query.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Executing hybrid retrieval and generating AI reasoning..."):
                try:
                    agent = ReActRepoAgent()
                    response = agent.run(user_query)
                    st.markdown("#### 💡 AI Analysis Result")
                    st.write(response)
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.markdown("### Automated Git Patch Synthesizer")
    bug_description = st.text_area("Describe the bug or requested code fix:", height=100, placeholder="e.g., Add a safety fallback in CodeASTParser if docstring is missing or None.")
    
    if st.button("Synthesize Patch"):
        if not bug_description.strip():
            st.warning("Please describe the bug.")
        else:
            with st.spinner("Synthesizing unified git diff patch..."):
                try:
                    agent = ReActRepoAgent()
                    synthesizer = PatchSynthesizer(agent)
                    result = synthesizer.generate_patch(bug_description)
                    
                    if result["has_valid_patch"]:
                        st.success("Patch generated successfully!")
                        st.code(result["patch_code"], language="diff")
                        if st.button("Save to fix.patch"):
                            synthesizer.save_patch_file(result["patch_code"])
                            st.info("Saved to 'fix.patch'. Run `git apply fix.patch` in terminal.")
                    else:
                        st.warning("Agent responded, but could not format a clean git diff block.")
                        st.write(result["raw_agent_output"])
                except Exception as e:
                    st.error(f"Error: {e}")

with tab3:
    st.markdown("### 📁 Repository Symbol Explorer")
    st.markdown("Inspect parsed classes, functions, parameters, and docstrings for any file in your codebase.")
    
    graph_path = "repo_graph.json"
    if os.path.exists(graph_path):
        with open(graph_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
        
        files_dict = graph_data.get("files", {})
        file_list = list(files_dict.keys())
        
        if file_list:
            selected_file = st.selectbox("Select a Python file to inspect:", file_list)
            file_data = files_dict[selected_file]
            
            col1, col2 = st.columns(2)
            col1.metric("Functions Defined", len(file_data.get("functions", [])))
            col2.metric("Classes Defined", len(file_data.get("classes", [])))
            
            st.markdown("---")
            st.markdown("#### 🛠️ Functions & Methods")
            functions = file_data.get("functions", [])
            if functions:
                for fn in functions:
                    with st.expander(f"def {fn.get('name')}(...) [Lines {fn.get('start_line')}–{fn.get('end_line')}]"):
                        st.markdown(f"**Returns:** `{fn.get('returns')}`")
                        st.markdown(f"**Docstring:** {fn.get('docstring') or '*None*'}")
                        params = fn.get("args", [])
                        if params:
                            st.markdown("**Parameters:**")
                            for p in params:
                                st.code(f"{p.get('name')}: {p.get('type')}", language="python")
            else:
                st.info("No top-level functions found in this file.")
            
            st.markdown("#### 📦 Classes")
            classes = file_data.get("classes", [])
            if classes:
                for cls in classes:
                    with st.expander(f"class {cls.get('name')} [Lines {cls.get('start_line')}–{cls.get('end_line')}]"):
                        st.markdown(f"**Bases:** `{cls.get('bases')}`")
                        st.markdown(f"**Docstring:** {cls.get('docstring') or '*None*'}")
            else:
                st.info("No classes found in this file.")
        else:
            st.warning("No files found in the graph data.")
    else:
        st.info("No 'repo_graph.json' found. Please click 'Index Codebase' in the sidebar first.")
