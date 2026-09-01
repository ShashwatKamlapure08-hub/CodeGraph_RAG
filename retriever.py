import os
import json
from typing import List, Dict, Any
from vector_store import CodeVectorStore

class GraphAugmentedRetriever:
    def __init__(self, vector_store: CodeVectorStore, repo_graph_path: str = "repo_graph.json"):
        self.vector_store = vector_store
        self.repo_graph_path = repo_graph_path
        self.graph_data = self._load_graph()

    def _load_graph(self) -> Dict[str, Any]:
        """Loads repository structural dependencies from JSON graph."""
        if os.path.exists(self.repo_graph_path):
            with open(self.repo_graph_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"files": {}, "dependency_edges": []}

    def hybrid_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Combines AST keyword symbol matching with vector similarity search."""
        vector_results = self.vector_store.query_similar_code(query, n_results=top_k * 2)
        
        retrieved_docs = []
        seen_ids = set()

        docs = vector_results.get("documents", [[]])[0]
        metadatas = vector_results.get("metadatas", [[]])[0]
        distances = vector_results.get("distances", [[]])[0] if "distances" in vector_results else [0.0] * len(docs)

        query_words = set(query.lower().split())

        for doc, meta, dist in zip(docs, metadatas, distances):
            doc_id = f"{meta['file_path']}::{meta['symbol_name']}"
            if doc_id in seen_ids:
                continue

            symbol_name = meta["symbol_name"].lower()
            score = 1.0 - dist if dist else 0.5

            # Exact match keyword boost for AST identifiers
            if any(word in symbol_name for word in query_words):
                score += 0.5

            retrieved_docs.append({
                "score": score,
                "file_path": meta["file_path"],
                "symbol_name": meta["symbol_name"],
                "type": meta["type"],
                "start_line": meta["start_line"],
                "end_line": meta["end_line"],
                "text": doc,
                "context_dependencies": []
            })
            seen_ids.add(doc_id)

        retrieved_docs.sort(key=lambda x: x["score"], reverse=True)
        return retrieved_docs[:top_k]

    def graph_augmented_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Performs hybrid retrieval and expands context using repo dependency edges."""
        base_results = self.hybrid_search(query, top_k=top_k)
        edges = self.graph_data.get("dependency_edges", [])

        for result in base_results:
            src_file = result["file_path"]
            
            # Find related edges connected to this source file
            related_edges = [
                e for e in edges if e.get("source") == src_file or e.get("target") == src_file
            ]
            
            dep_summaries = []
            for edge in related_edges[:3]:  # Limit context expansion size
                dep_type = edge.get("type", "dependency")
                symbol = edge.get("symbol", "")
                if edge.get("source") == src_file:
                    dep_summaries.append(f"Imports/Calls '{symbol}' from {edge.get('target')}")
                else:
                    dep_summaries.append(f"Referenced by {edge.get('source')}")

            result["context_dependencies"] = dep_summaries

        return base_results


if __name__ == "__main__":
    store = CodeVectorStore()
    retriever = GraphAugmentedRetriever(store)

    test_queries = [
        "extract AST nodes or function signatures",
        "build dependency graph and map relationships",
        "scan repository files recursively"
    ]

    print("==================================================")
    print("        RETRIEVAL BENCHMARK VERIFICATION          ")
    print("==================================================")

    for q in test_queries:
        print(f"\nQUERY: '{q}'")
        results = retriever.graph_augmented_search(q, top_k=2)
        for idx, r in enumerate(results, 1):
            print(f"  [{idx}] {r['symbol_name']} ({r['file_path']}: L{r['start_line']}-L{r['end_line']}) | Score: {r['score']:.2f}")
            if r["context_dependencies"]:
                print(f"      Graph Context: {r['context_dependencies']}")
