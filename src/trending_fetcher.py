"""
Fetcher for trending Python repositories from GitHub.
"""

import requests
from datetime import datetime, timedelta
from typing import List, Tuple


def get_trending_python_repos(limit: int = 5, max_size_kb: int = 51200) -> List[Tuple[str, str, int]]:
    """
    Fetches top trending Python repositories from the last 7 days using GitHub API.
    
    Args:
        limit (int): Number of repositories to fetch.
        max_size_kb (int): Maximum repository size in KB (default 50MB).

    Returns:
        List[Tuple[str, str, int]]: A list of (full_name, clone_url, size_kb).
    """
    # Calculate date for 7 days ago
    last_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # GitHub Search API: Python repos created in the last week, sorted by stars
    query = f"language:python created:>{last_week}"
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
    
    try:
        # Use a generic User-Agent to avoid getting blocked
        headers = {"User-Agent": "Python-AST-RAG-Fetcher"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        items = response.json().get('items', [])
        results = []
        
        for repo in items:
            full_name = repo['full_name']
            clone_url = repo['clone_url']
            size = repo['size']  # Size in KB
            
            # 50MB Safety check
            if size > max_size_kb:
                print(f"  [!] Skip {full_name}: {size/1024:.1f}MB exceeds limit.")
                continue
                
            results.append((full_name, clone_url, size))
            if len(results) >= limit:
                break
                
        return results
    except Exception as e:
        print(f"  [!] Error fetching from GitHub API: {e}")
        return []


if __name__ == "__main__":
    print("Fetching top Python trending repos...")
    repos = get_trending_python_repos()
    for i, (name, url, size) in enumerate(repos):
        print(f"{i+1}. {name} | {url} ({size}KB)")
