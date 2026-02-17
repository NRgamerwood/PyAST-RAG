"""
Script to update global project metrics (Total Repos, Total LOC) and README placeholders.
"""

import os
import json
import re
import sys
from src.utils import get_all_python_files


def count_loc_in_dir(directory: str) -> int:
    """Counts effective lines of code (non-empty, non-comment) in a directory."""
    loc = 0
    files = get_all_python_files(directory)
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
                for line in fp:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        loc += 1
        except Exception:
            continue
    return loc


def update_metrics_json(repo_name: str, loc: int):
    """Updates the persistent metrics.json file."""
    metrics_path = "benchmarks/results/metrics.json"
    
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            data = json.load(f)
    else:
        data = {"total_repos": 0, "total_loc": 0, "conquered_repos": []}
    
    if repo_name not in data["conquered_repos"]:
        data["total_repos"] += 1
        data["total_loc"] += loc
        data["conquered_repos"].append(repo_name)
        
        with open(metrics_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    return data


def update_readme_placeholders(data: dict):
    """Replaces placeholders in README.md with actual stats."""
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return
        
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update Repo Count
    content = re.sub(r'<!-- REPO_COUNT -->\d*', f'<!-- REPO_COUNT -->{data["total_repos"]}', content)
    
    # 2. Update LOC Count (with comma formatting)
    content = re.sub(r'<!-- LOC_COUNT -->[\d,]*', f'<!-- LOC_COUNT -->{data["total_loc"]:,}', content)
    
    # 3. Update Conquered List (Last 5 repos)
    repo_links = [f"- 🏆 `{r}`" for r in data["conquered_repos"][-5:]]
    list_content = "\n".join(repo_links)
    
    # Use re.DOTALL to match across lines if needed, 
    # but here we just look for the placeholder and what follows until next heading or end
    placeholder = "<!-- CONQUERED_LIST -->"
    if placeholder in content:
        parts = content.split(placeholder)
        # We assume there's a limit or marker after the list. 
        # For simplicity, we'll just replace the placeholder with the list.
        # Actually, let's look for a closing marker if we want to be clean.
        content = parts[0] + placeholder + "\n" + list_content + "\n" + parts[1].split("\n\n")[1] if "\n\n" in parts[1] else parts[0] + placeholder + "\n" + list_content

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python update_global_metrics.py <repo_name> <directory>")
        sys.exit(1)
        
    r_name = sys.argv[1]
    r_dir = sys.argv[2]
    
    print(f"📊 Calculating LOC for {r_name} in {r_dir}...")
    current_loc = count_loc_in_dir(r_dir)
    print(f"   Done. LOC: {current_loc}")
    
    updated_data = update_metrics_json(r_name, current_loc)
    update_readme_placeholders(updated_data)
    print("✅ README and metrics.json updated.")
