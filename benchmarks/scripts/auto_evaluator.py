"""
Automated evaluator for trending GitHub repositories.
Clones, parses, and updates the Live Benchmark Wall and History Archive.
"""

import os
import shutil
import subprocess
from datetime import datetime
from src.trending_fetcher import get_trending_python_repos
from src.parser import ASTParser
from src.utils import get_all_python_files, read_file
from benchmarks.scripts.update_global_metrics import count_loc_in_dir, update_metrics_json, update_readme_placeholders


def log_to_conquered_history(name: str, loc: int, chunks: int):
    """将处理成功的库永久追加到历史记录文件中，不限制数量。"""
    history_path = "benchmarks/CONQUERED.md"
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    
    # 如果文件不存在，创建表头
    if not os.path.exists(history_path):
        with open(history_path, "w", encoding="utf-8") as f:
            f.write("# 📜 PyAST-RAG Conquered History Archive\n\n")
            f.write("> 这是一个自动生成的永久档案，记录了所有经过 PyAST-RAG 压力测试的开源项目。\n\n")
            f.write("| Date | Repository | LOC | Chunks | Status |\n")
            f.write("| :--- | :--- | :--- | :---: | :---: |\n")

    # 追加新记录 (Append 模式)
    with open(history_path, "a", encoding="utf-8") as f:
        f.write(f"| {timestamp} | [{name}](https://github.com/{name}) | {loc:,} | {chunks} | ✅ |\n")


def update_readme_wall(entry: str):
    """更新 README.md 中的实时展示墙，仅保留最近的 15 条记录。"""
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
        lines.append(f"\n{wall_header}\n")
        lines.append("| Time | Repository | Chunks | Syntax % | Meta Density |\n")
        lines.append("| :--- | :--- | :---: | :---: | :---: |\n")
        header_idx = len(lines) - 3

    # 在表头下方插入新数据 (header_idx + 3 是第一行数据的位置)
    lines.insert(header_idx + 3, entry + "\n")

    # --- 自动截断逻辑：防止 README 爆炸 ---
    # 查找表格结束的位置（通常是下一个标题或文件末尾）
    table_start = header_idx + 3
    table_end = table_start
    for i in range(table_start, len(lines)):
        if lines[i].startswith("##") or lines[i].strip() == "":
            table_end = i
            break
        table_end = i + 1

    # 如果数据行数超过 15 行，删除旧的（底部）记录
    max_display = 15
    current_rows = table_end - table_start
    if current_rows > max_display:
        del lines[table_start + max_display : table_end]

    with open(readme_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def evaluate_repo(name: str, url: str) -> tuple[str, int, int]:
    """克隆仓库，运行指标分析。返回 (markdown行, 代码行数, 分块总数)。"""
    temp_dir = f"temp_eval_{name.replace('/', '_')}"
    print(f"   [>] Evaluating {name}...")
    
    try:
        # 使用浅克隆 (depth 1) 节省空间和时间
        subprocess.run(
            ["git", "clone", "--depth", "1", url, temp_dir],
            check=True,
            capture_output=True,
            timeout=180  # 稍微延长克隆时间上限至 3 分钟
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
                    meta_dict = c.metadata.model_dump()
                    total_meta_fields += len([v for v in meta_dict.values() if v is not None])
            except Exception:
                continue

        avg_meta = (total_meta_fields / total_chunks) if total_chunks > 0 else 0
        loc = count_loc_in_dir(temp_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 格式化 README 中的展示行
        entry = f"| {timestamp} | [{name}](https://github.com/{name}) | {total_chunks} | 100% | {avg_meta:.1f} |"
        return entry, loc, total_chunks

    except Exception as e:
        print(f"      [!] Error evaluating {name}: {e}")
        return "", 0, 0
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    print(f"🚀 Starting Auto-Evolution Cycle: {datetime.now()}")
    
    # 获取 Trending 列表（已设置为 50）
    repos = get_trending_python_repos(limit=50)
    if not repos:
        print("  [!] No repos fetched. Exiting.")
        return

    for name, url, size in repos:
        # 执行评估，获取详细数据
        entry, loc, chunks = evaluate_repo(name, url)
        
        if entry:
            # 1. 更新 README 展示墙（动态滚动）
            update_readme_wall(entry)
            
            # 2. 永久归档到历史记录文件
            log_to_conquered_history(name, loc, chunks)
            
            # 3. 更新全局指标（JSON 和 README 总 LOC）
            metrics_data = update_metrics_json(name, loc)
            update_readme_placeholders(metrics_data)
            
            print(f"   [+] Success: {name} (LOC: {loc}, Chunks: {chunks})")

    print(f"🏁 Cycle complete at {datetime.now()}")


if __name__ == "__main__":
    main()