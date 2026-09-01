from typing import List, Dict, Any
from vector_store import CodeVectorStore

class HybridCodeRetriever:
    def __init__(self, vector_store: CodeVectorStore):
        self.vector_store = vector_store

    def hybrid_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Combines AST keyword symbol matching with vector similarity search."""
        # 1. Vector similarity search
        vector_results = self.vector_store.query_similar_code(query, n_results=top_k * 2)
        
        retrieved_docs = []
        seen_ids = set()

        docs = vector_results.get("documents", [[]])[0]
        metadatas = vector_results.get("metadatas", [[]])[0]
        distances = vector_results.get("distances", [[]])[0] if "distances" in vector_results else [0.0] * len(docs)

        # 2. Extract potential symbol target keywords from the user query
        query_words = set(query.lower().split())

        for doc, meta, dist in zip(docs, metadatas, distances):
            doc_id = f"{meta['file_path']}::{meta['symbol_name']}"
            if doc_id in seen_ids:
                continue

            symbol_name = meta["symbol_name"].lower()
            
            # Base score derived from cosine distance (or default ranking)
            score = 1.0 - dist if dist else 0.5

            # 3. Exact AST Keyword Match Boost: If query explicitly mentions a symbol name
            if any(word in symbol_name for word in query_words):
                score += 0.5  # Keyword boost

            retrieved_docs.append({
                "score": score,
                "file_path": meta["file_path"],
                "symbol_name": meta["symbol_name"],
                "type": meta["type"],
                "start_line": meta["start_line"],
                "end_line": meta["end_line"],
                "text": doc
            })
            seen_ids.add(doc_id)

        # Sort combined results by adjusted score
        retrieved_docs.sort(key=lambda x: x["score"], reverse=True)
        return retrieved_docs[:top_k]

if __name__ == "__main__":
    store = CodeVectorStore()
    retriever = HybridCodeRetriever(store)

    # Test Hybrid Query combining natural language with exact symbol keyword
    test_query = "extract_function_calls helper function"
    results = retriever.hybrid_search(test_query, top_k=2)

    print("\n--- Day 10 Hybrid Retrieval Results ---")
    for r in results:
        print(f"Score: {r['score']:.2f} | [{r['type'].upper()}] {r['symbol_name']} ({r['file_path']}: L{r['start_line']}-L{r['end_line']})")
