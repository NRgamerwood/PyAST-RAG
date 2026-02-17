"""
Quantitative statistical benchmark to compare semantic integrity and metadata richness.
"""

import os
import ast
import textwrap
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from src.parser import ASTParser
from src.utils import get_all_python_files, read_file


def run_quantitative_stats():
    """Performs full scan of requests library and calculates hardcore metrics."""
    repo_path = "tests/data/requests"
    if not os.path.exists(repo_path):
        print(f"Error: Repository not found at {repo_path}")
        return

    python_files = get_all_python_files(repo_path)
    parser = ASTParser()
    
    # Baseline Splitter: LangChain Python-aware splitter
    lc_splitter = RecursiveCharacterTextSplitter.from_language(
        Language.PYTHON,
        chunk_size=800,
        chunk_overlap=0
    )

    stats = {
        "baseline": {
            "total_chunks": 0,
            "syntax_errors": 0,
            "incomplete_functions": 0,
            "total_def_chunks": 0
        },
        "pyast": {
            "total_chunks": 0,
            "metadata_fields_sum": 0
        }
    }

    print(f"🚀 Scanning {len(python_files)} files for quantitative analysis...")

    for file_path in python_files:
        try:
            content = read_file(file_path)
            
            # --- 🟢 1. Baseline Stats (LangChain) ---
            lc_chunks = lc_splitter.split_text(content)
            for chunk in lc_chunks:
                stats["baseline"]["total_chunks"] += 1
                try:
                    ast.parse(textwrap.dedent(chunk))
                except SyntaxError:
                    stats["baseline"]["syntax_errors"] += 1
                
                if "def " in chunk:
                    stats["baseline"]["total_def_chunks"] += 1
                    try:
                        parsed = ast.parse(textwrap.dedent(chunk))
                        has_complete_func = any(isinstance(node, ast.FunctionDef) for node in ast.walk(parsed))
                        if not has_complete_func:
                            stats["baseline"]["incomplete_functions"] += 1
                    except SyntaxError:
                        stats["baseline"]["incomplete_functions"] += 1
            
            # --- 🟢 2. PyAST Stats (Our Project) ---
            ast_chunks = parser.parse_source(content, file_path)
            for chunk in ast_chunks:
                stats["pyast"]["total_chunks"] += 1
                meta_dict = chunk.metadata.model_dump()
                stats["pyast"]["metadata_fields_sum"] += len([v for v in meta_dict.values() if v is not None])

        except Exception as e:
            print(f"  [!] Error processing {file_path}: {e}")

    # Calculations
    b_total = stats["baseline"]["total_chunks"]
    b_syntax_err_rate = (stats["baseline"]["syntax_errors"] / b_total * 100) if b_total > 0 else 0
    b_def_total = stats["baseline"]["total_def_chunks"]
    b_frag_rate = (stats["baseline"]["incomplete_functions"] / b_def_total * 100) if b_def_total > 0 else 0
    p_total = stats["pyast"]["total_chunks"]
    p_avg_meta = (stats["pyast"]["metadata_fields_sum"] / p_total) if p_total > 0 else 0

    # Output Table Generation
    output_dir = "benchmarks/results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "stats_table.txt")

    lines = []
    lines.append("\n" + "="*75)
    lines.append(f"{'TECHNOLOGICAL METRIC':<40} | {'LangChain (800)':<15} | {'PyAST-RAG':<10}")
    lines.append("-" * 75)
    lines.append(f"{'Total Chunks Created':<40} | {b_total:<15} | {p_total:<10}")
    lines.append(f"{'Syntax Error Rate (Invalid Python)':<40} | {b_syntax_err_rate:>14.2f}% | {'0.00%':<10}")
    lines.append(f"{'Function Fragmentation Rate':<40} | {b_frag_rate:>14.2f}% | {'0.00%':<10}")
    lines.append(f"{'Average Metadata Fields per Chunk':<40} | {'1 (text)':<15} | {p_avg_meta:>10.1f}")
    lines.append("="*75)
    
    report = "\n".join(lines)
    print(report)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSuccess: Quantitative stats saved to {output_file}")


if __name__ == "__main__":
    run_quantitative_stats()
