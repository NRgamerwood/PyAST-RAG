"""
Main entry point for the Python-AST-RAG Demo.
Integration of Parser, Vector Store, and Gemini LLM.
"""

import os
import sys
import subprocess
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai

from src.parser import ASTParser
from src.vector_store import CodeBaseStore
from src.utils import get_all_python_files, read_file

# Load environment variables from .env file
load_dotenv()


def initialize_gemini():
    """Initializes the Gemini AI model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[!] Warning: GEMINI_API_KEY not found in environment variables or .env file.")
        print("    You can still use the index and search functions, but generation will be skipped.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        # Using gemini-3-flash-preview as requested
        return genai.GenerativeModel('gemini-3-flash-preview')
    except Exception as e:
        print(f"\n[!] Error initializing Gemini: {e}")
        return None


def ensure_data_ready():
    """Ensures the requests library is available in tests/data/requests."""
    repo_path = os.path.join("tests", "data", "requests")
    if not os.path.exists(repo_path):
        print(f"\nRequests library not found at {repo_path}. Cloning now...")
        os.makedirs(os.path.dirname(repo_path), exist_ok=True)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "https://github.com/psf/requests.git", repo_path],
                check=True,
                capture_output=True
            )
            print("Cloned successfully.")
        except Exception as e:
            print(f"Error cloning repository: {e}")
            sys.exit(1)
    return repo_path


def indexing_phase(repo_path: str, store: CodeBaseStore):
    """Parses all files in the repo and adds them to the vector store."""
    print(f"\n--- Indexing Phase ---")
    python_files = get_all_python_files(repo_path)
    parser = ASTParser()
    
    all_chunks = []
    print(f"Found {len(python_files)} Python files. Parsing...")
    
    for file_path in python_files:
        try:
            content = read_file(file_path)
            chunks = parser.parse_source(content, file_path)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"  [!] Skip {file_path} due to error: {e}")
            
    print(f"Adding {len(all_chunks)} chunks to Vector Store (ChromaDB)...")
    store.add_chunks(all_chunks)
    print(f"Indexing complete. Successfully indexed {len(all_chunks)} code chunks.")


def ask_code(query: str, store: CodeBaseStore, model: Optional[genai.GenerativeModel]):
    """
    RAG Pipeline:
    1. Retrieval: Search relevant code chunks.
    2. Context: Format chunks into a prompt.
    3. Generation: Get answer from LLM.
    """
    # 1. Retrieval
    print(f"\n[Step 1] Retrieving relevant code snippets for: '{query}'")
    chunks = store.search(query, n_results=5)
    
    if not chunks:
        print("No relevant code snippets found.")
        return
    
    # 2. Context Preparation
    context_parts = []
    for i, chunk in enumerate(chunks):
        rel_path = os.path.relpath(chunk.metadata.file_path, os.getcwd())
        parent_info = f" (Class: {chunk.metadata.parent_name})" if chunk.metadata.parent_name else ""
        header = f"Snippet {i+1} | File: {rel_path} | Name: {chunk.metadata.name}{parent_info}"
        part = f"{header}\n```python\n{chunk.content}\n```"
        context_parts.append(part)
    
    context_code = "\n\n".join(context_parts)
    
    # 3. Generation
    prompt = f"""你是资深 Python 专家。以下是根据用户的提问检索到的相关代码片段：
---
{context_code}
---
用户的问题是：{query}
请根据以上代码片段，详细回答用户的问题。如果代码中没有相关信息，请诚实回答。"""

    if model:
        print("[Step 2] Generating answer using Gemini...")
        try:
            response = model.generate_content(prompt)
            print("\n" + "="*60)
            print("AI ANSWER:")
            print("="*60)
            print(response.text)
            print("="*60)
        except Exception as e:
            print(f"\n[!] Error during generation: {e}")
    else:
        print("\n[Step 2] (Mock Generation) API Key missing.")
        print(f"Retrieved {len(chunks)} snippets. Preview of the first snippet:")
        print(f"--- {chunks[0].metadata.name} ---\n{chunks[0].content[:100]}...")


def main():
    # Setup
    repo_path = ensure_data_ready()
    store = CodeBaseStore(collection_name="requests_rag", persist_directory="./chroma_db")
    model = initialize_gemini()
    
    # Indexing
    # Check if we should re-index (optional: for this demo we index every time or check counts)
    # ChromaDB add is idempotent if IDs match, but we can check if it's empty.
    if store.collection.count() == 0:
        indexing_phase(repo_path, store)
    else:
        print(f"\nUsing existing index with {store.collection.count()} chunks.")
    
    # Interactive Loop
    print("\n" + "*"*50)
    print("Welcome to Python-AST-RAG Demo!")
    print("You can ask questions about the 'requests' library codebase.")
    print("Type 'exit' or 'quit' to end the session.")
    print("*"*50)
    
    while True:
        try:
            query = input("\n[Question]: ").strip()
            if not query:
                continue
            if query.lower() in ['exit', 'quit', 'q']:
                break

            #调用检索和生成
            ask_code(query, store, model)

        # 捕获 Ctrl+C (KeyboardInterrupt) 和 Ctrl+D/管道结束 (EOFError)
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting...")
            break

        # 捕获其他意料之外的错误
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            
    print("\nGoodbye! Thank you for using PyAST-RAG.")


if __name__ == "__main__":
    main()
