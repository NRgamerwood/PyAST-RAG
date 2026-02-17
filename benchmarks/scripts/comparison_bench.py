"""
Benchmark comparison between LangChain's RecursiveCharacterTextSplitter 
and our AST-based PyAST-RAG.
"""

import os
from src.parser import ASTParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_llm_response(prompt):
    """Fetches response from Gemini LLM."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: No API Key found. Please set GEMINI_API_KEY in .env."

    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"LLM Error: {str(e)}"


def run_benchmark():
    """Runs the comparison benchmark."""
    target_file = "tests/data/requests/requests/sessions.py"
    if not os.path.exists(target_file):
        alt_path = "tests/data/requests/src/requests/sessions.py"
        if os.path.exists(alt_path):
            target_file = alt_path
        else:
            print(f"Error: Target file {target_file} not found.")
            return

    query = "在 Session 类中，request 方法是如何处理参数并调用底层 dispatch 的？"

    with open(target_file, 'r', encoding='utf-8') as f:
        source_code = f.read()

    print(f"🚀 Starting Benchmark on: {target_file}")
    print(f"❓ Query: {query}\n")

    # --- 🟢 Baseline: LangChain ---
    print("Running Baseline: LangChain...")
    lc_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        add_start_index=True
    )
    lc_chunks = lc_splitter.split_text(source_code)
    lc_context = next((c for c in lc_chunks if "def request" in c), "No matching chunk found.")

    # --- 🟢 Ours: PyAST-RAG ---
    print("Running PyAST-RAG...")
    parser = ASTParser()
    ast_chunks = parser.parse_source(source_code, target_file)
    ast_context_obj = next(
        (c for c in ast_chunks if c.metadata.name == "request" and c.metadata.parent_name == "Session"),
        None
    )

    if ast_context_obj:
        ast_context = ast_context_obj.content
    else:
        ast_context = "PyAST-RAG could not find the specific chunk."

    # --- 🤖 LLM Judgement ---
    prompt_template = """
你是资深代码专家。请根据提供的代码片段回答用户问题。
如果代码片段不完整或信息不足，请明确指出。

代码片段：
---
{context}
---

问题：{query}
"""

    print("\n--- [Baseline: LangChain] Response ---")
    print(get_llm_response(prompt_template.format(context=lc_context, query=query)))

    print("\n--- [Ours: PyAST-RAG] Response ---")
    print(get_llm_response(prompt_template.format(context=ast_context, query=query)))


if __name__ == "__main__":
    run_benchmark()
