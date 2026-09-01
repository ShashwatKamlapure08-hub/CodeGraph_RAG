import os
import json
import re
from typing import List, Dict, Any
from groq import Groq
from vector_store import CodeVectorStore
from retriever import GraphAugmentedRetriever

class ReActRepoAgent:
    def __init__(self, model_name: str = "openai/gpt-oss-20b"):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is missing. Set it before running.")
        self.client = Groq(api_key=api_key)
        self.model_name = model_name
        self.vector_store = CodeVectorStore()
        self.retriever = GraphAugmentedRetriever(self.vector_store)

    def _format_context(self, context_items: List[Dict[str, Any]]) -> str:
        """Formats retrieved context snippets for prompt injection."""
        formatted = ""
        for idx, item in enumerate(context_items, 1):
            formatted += f"\n[Doc {idx}] Symbol: {item['symbol_name']} | File: {item['file_path']} (Lines {item['start_line']}-{item['end_line']})\n"
            if item.get("context_dependencies"):
                formatted += f"Graph Relations: {', '.join(item['context_dependencies'])}\n"
            formatted += f"Snippet:\n{item['text']}\n"
        return formatted

    def generate_direct_response(self, prompt_text: str, context_items: List[Dict[str, Any]]) -> str:
        """Direct completion generation that prevents unwanted tool-triggering behaviors."""
        formatted_context = self._format_context(context_items)
        
        full_prompt = f"""You are RepoMind, an expert software engineer.
Analyze the request using the AST Context provided and respond clearly.

AST CONTEXT:
{formatted_context}

REQUEST:
{prompt_text}"""

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a precise software engineering code assistant."},
                {"role": "user", "content": full_prompt}
            ],
            model=self.model_name,
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content

    def run(self, query: str) -> str:
        """Runs baseline retrieval and generates structured answer."""
        context = self.retriever.graph_augmented_search(query, top_k=2)
        return self.generate_direct_response(query, context)


if __name__ == "__main__":
    agent = ReActRepoAgent()
    user_query = "How are function calls extracted across files and mapped into graph edges?"
    print(agent.run(user_query))
