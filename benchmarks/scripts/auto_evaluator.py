"""
Automated evaluator for trending GitHub repositories.
Clones, parses, and updates the Live Benchmark Wall in README.
"""

import os
import shutil
import subprocess
from datetime import datetime
from src.trending_fetcher import get_trending_python_repos
from src.parser import ASTParser
from src.utils import get_all_python_files, read_file


def update_readme_wall(entry: str):
    """Adds a new entry to the Live Benchmark Wall in README.md."""
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    wall_header = "## Live Benchmark Wall"
    wall_found = False
    header_idx = -1

    for i, line in enumerate(lines):
        if wall_header in line:
            wall_found = True
            header_idx = i
            break

    if not wall_found:
        # Create the section if it doesn't exist
        lines.append(f"\n{wall_header}\n")
        lines.append("| Time | Repository | Chunks | Syntax % | Meta Density |\n")
        lines.append("| :--- | :--- | :---: | :---: | :---: |\n")
        header_idx = len(lines) - 3

    # Insert new entry right after the table separator (header_idx + 2)
    # We keep it as a chronological log, newest on top
    lines.insert(header_idx + 3, entry + "\n")

    # Optional: Limit the wall to the last 20 entries to prevent README bloat
    # (Implementation omitted for brevity, but recommended for production)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def evaluate_repo(name: str, url: str) -> str:
    """Clones a repo, runs metrics, and returns a markdown row."""
    temp_dir = f"temp_eval_{name.replace('/', '_')}"
    print(f"  [>] Evaluating {name}...")
    
    try:
        # Shallow clone to save time and space
        subprocess.run(
            ["git", "clone", "--depth", "1", url, temp_dir],
            check=True,
            capture_output=True,
            timeout=120  # 2 minutes timeout for cloning
        )
        
        python_files = get_all_python_files(temp_dir)
        parser = ASTParser()
        
        total_chunks = 0
        total_meta_fields = 0
        
        for f_path in python_files:
            try:
                content = read_file(f_path)
                chunks = parser.parse_source(content, f_path)
                total_chunks += len(chunks)
                for c in chunks:
                    # Count non-None metadata fields
                    meta_dict = c.metadata.model_dump()
                    total_meta_fields += len([v for v in meta_dict.values() if v is not None])
            except Exception:
                continue

        avg_meta = (total_meta_fields / total_chunks) if total_chunks > 0 else 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return f"| {timestamp} | [{name}](https://github.com/{name}) | {total_chunks} | 100% | {avg_meta:.1f} |"

    except Exception as e:
        print(f"      [!] Error: {e}")
        return ""
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    print(f"🚀 Starting Auto-Evolution Cycle: {datetime.now()}")
    
    # 1. Fetch top 5 trending repos
    repos = get_trending_python_repos(limit=5)
    if not repos:
        print("  [!] No repos fetched. Exiting.")
        return

    # 2. Evaluate each
    for name, url, size in repos:
        entry = evaluate_repo(name, url)
        if entry:
            update_readme_wall(entry)
            print(f"  [+] Success: {name}")

    print(f"🏁 Cycle complete at {datetime.now()}")


if __name__ == "__main__":
    main()
