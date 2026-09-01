import os
import json
from typing import List, Dict, Any
import chromadb

class CodeVectorStore:
    def __init__(self, db_dir: str = "./chroma_db", collection_name: str = "repo_codebase"):
        """Initializes persistent local ChromaDB storage and targets the codebase collection."""
        self.db_dir = db_dir
        self.client = chromadb.PersistentClient(path=self.db_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def prepare_chunks_from_graph(self, repo_graph_path: str = "repo_graph.json") -> List[Dict[str, Any]]:
        """Converts repo_graph AST nodes into vector storage documents with attached metadata."""
        if not os.path.exists(repo_graph_path):
            raise FileNotFoundError(f"{repo_graph_path} not found. Run graph_builder.py first.")

        with open(repo_graph_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        chunks = []
        files = graph_data.get("files", {})

        for file_path, data in files.items():
            # 1. Chunk top-level functions
            for fn in data.get("functions", []):
                doc_text = (
                    f"File: {file_path}\n"
                    f"Function: {fn['name']}\n"
                    f"Args: {fn['args']}\n"
                    f"Returns: {fn['returns']}\n"
                    f"Docstring: {fn['docstring']}"
                )
                chunks.append({
                    "id": f"{file_path}::func::{fn['name']}::{fn['start_line']}",
                    "text": doc_text,
                    "metadata": {
                        "file_path": file_path,
                        "symbol_name": fn["name"],
                        "type": "function",
                        "start_line": fn["start_line"],
                        "end_line": fn["end_line"]
                    }
                })

            # 2. Chunk classes and their nested methods
            for cls in data.get("classes", []):
                doc_text = (
                    f"File: {file_path}\n"
                    f"Class: {cls['name']}\n"
                    f"Bases: {cls['bases']}\n"
                    f"Docstring: {cls['docstring']}"
                )
                chunks.append({
                    "id": f"{file_path}::class::{cls['name']}::{cls['start_line']}",
                    "text": doc_text,
                    "metadata": {
                        "file_path": file_path,
                        "symbol_name": cls["name"],
                        "type": "class",
                        "start_line": cls["start_line"],
                        "end_line": cls["end_line"]
                    }
                })

                for method in cls.get("methods", []):
                    m_text = (
                        f"File: {file_path}\n"
                        f"Class: {cls['name']}\n"
                        f"Method: {method['name']}\n"
                        f"Args: {method['args']}\n"
                        f"Returns: {method['returns']}\n"
                        f"Docstring: {method['docstring']}"
                    )
                    chunks.append({
                        "id": f"{file_path}::method::{cls['name']}.{method['name']}::{method['start_line']}",
                        "text": m_text,
                        "metadata": {
                            "file_path": file_path,
                            "symbol_name": f"{cls['name']}.{method['name']}",
                            "type": "method",
                            "start_line": method["start_line"],
                            "end_line": method["end_line"]
                        }
                    })

        return chunks

    def index_codebase(self, repo_graph_path: str = "repo_graph.json") -> int:
        """Stores code chunks and metadata inside ChromaDB."""
        chunks = self.prepare_chunks_from_graph(repo_graph_path)
        if not chunks:
            print("No chunks found to index.")
            return 0

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        # Upsert documents into vector database
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(ids)

    def query_similar_code(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """Performs vector similarity search against indexed code."""
        return self.collection.query(
            query_texts=[query],
            n_results=n_results
        )


if __name__ == "__main__":
    # Test execution for Day 9
    store = CodeVectorStore()
    
    # Step 1: Index the codebase
    count = store.index_codebase("repo_graph.json")
    print(f"Indexed {count} code units into ChromaDB.")

    # Step 2: Test query retrieval
    query_str = "extract AST nodes or function signatures"
    results = store.query_similar_code(query_str, n_results=2)
    
    print("\n--- Similarity Search Test Result ---")
    if results and "documents" in results and results["documents"]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            print(f"[{meta['type'].upper()}] {meta['symbol_name']} ({meta['file_path']})")
            print(f"Text snippet:\n{doc}\n")
