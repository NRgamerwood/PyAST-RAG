"""
Statistical benchmark script to compare function integrity between 
LangChain's fixed-size chunking and PyAST-RAG.
"""

import os
import matplotlib.pyplot as plt
from src.parser import ASTParser
from src.utils import get_all_python_files, read_file


def run_stats_benchmark():
    """Scans the requests library and calculates how many functions are broken by fixed-size chunking."""
    repo_path = "tests/data/requests"
    if not os.path.exists(repo_path):
        print(f"Error: Repository not found at {repo_path}")
        return

    python_files = get_all_python_files(repo_path)
    parser = ASTParser()
    
    total_functions = 0
    broken_functions_fixed_800 = 0
    
    CHUNK_SIZE = 800
    
    print(f"Scanning {len(python_files)} files in {repo_path}...")
    
    for file_path in python_files:
        try:
            content = read_file(file_path)
            # Use AST to extract all functions (including methods)
            chunks = parser.parse_source(content, file_path)
            
            for chunk in chunks:
                if chunk.metadata.node_type == "function":
                    total_functions += 1
                    if len(chunk.content) > CHUNK_SIZE:
                        broken_functions_fixed_800 += 1
        except Exception as e:
            print(f"  [!] Error parsing {file_path}: {e}")

    if total_functions == 0:
        print("No functions found. Benchmark aborted.")
        return

    # --- Generate Bar Chart ---
    print("Generating chart...")
    labels = ['Fixed-size (800)', 'PyAST-RAG']
    broken_counts = [broken_functions_fixed_800, 0]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, broken_counts, color=['#ff9999', '#66b3ff'])
    
    plt.ylabel('Number of Broken Functions (Semantic Context Lost)')
    plt.title(f'Comparison of Function Integrity (Requests Library)\nTotal Functions: {total_functions}')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5, int(yval), 
                 va='bottom', ha='center', fontsize=12, fontweight='bold')

    plt.figtext(0.5, 0.01, f"* A function is considered 'Broken' if its length exceeds {CHUNK_SIZE} characters.", 
                ha="center", fontsize=10, bbox={"facecolor":"orange", "alpha":0.1, "pad":5})

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save to benchmarks/results/
    output_dir = "benchmarks/results"
    os.makedirs(output_dir, exist_ok=True)
    output_image = os.path.join(output_dir, "benchmark_result.png")
    plt.savefig(output_image)
    print(f"\nSuccess: Benchmark chart saved as {output_image}")


if __name__ == "__main__":
    run_stats_benchmark()
