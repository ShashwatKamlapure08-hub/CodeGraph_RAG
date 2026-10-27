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
    page_title="RepoMind - Codebase QA & Bug Fixer",
    page_icon="⚡",
    layout="wide"
)

# App Header
st.title("⚡ RepoMind: AST-Aware Codebase QA & Automated Bug Fixer")
st.markdown("Transform any Python codebase into an intelligent, graph-augmented retrieval & AI reasoning pipeline.")

# Sidebar Configuration
st.sidebar.header("🛠️ Repository Control")
repo_path = st.sidebar.text_input("Target Repository Path", value=".")
index_button = st.sidebar.button("Index Codebase", type="primary")

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
tab1, tab2, tab3 = st.tabs(["💬 Codebase QA & Search", "🛠️ Automated Patch Generator", "📊 Graph & Stats View"])

with tab1:
    st.header("Ask RepoMind")
    st.markdown("Query your codebase using hybrid semantic search and graph-augmented LLM reasoning.")
    
    user_query = st.text_area("Enter your technical question or code analysis query:", height=100, placeholder="e.g., How are function calls extracted across files?")
    
    if st.button("Run Analysis", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Executing hybrid retrieval and generating LLM response..."):
                try:
                    agent = ReActRepoAgent()
                    response = agent.run(user_query)
                    st.subheader("💡 AI Reasoning & Answer")
                    st.write(response)
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.header("Automated Git Patch Generator")
    st.markdown("Describe a bug or feature modification. RepoMind will output a unified `git diff` patch.")
    
    bug_description = st.text_area("Describe the bug or requested code fix:", height=100, placeholder="e.g., Add a safety fallback in CodeASTParser if docstring is missing.")
    
    if st.button("Synthesize Patch", type="primary"):
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
                        
                        # Save button option
                        if st.button("Save to fix.patch"):
                            synthesizer.save_patch_file(result["patch_code"])
                            st.info("Saved to 'fix.patch'. Run `git apply fix.patch` in terminal.")
                    else:
                        st.warning("Agent responded, but could not format a clean git diff block.")
                        st.write(result["raw_agent_output"])
                except Exception as e:
                    st.error(f"Error: {e}")

with tab3:
    st.header("📊 Repository Knowledge Graph Stats")
    graph_path = "repo_graph.json"
    if os.path.exists(graph_path):
        with open(graph_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Files Scanned", graph_data.get("total_files", 0))
        col2.metric("Dependency Edges Mapped", len(graph_data.get("dependency_edges", [])))
        col3.metric("Vector Database", "Active (ChromaDB)")
        
        with st.expander("View Raw Graph JSON Metadata"):
            st.json(graph_data)
    else:
        st.info("No 'repo_graph.json' found. Use the sidebar to index your codebase first.")
