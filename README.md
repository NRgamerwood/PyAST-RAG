# Python-AST-RAG

针对 Python 代码库优化的 RAG（检索增强生成）工具，利用 AST（抽象语法树）实现结构化代码切分和依赖追踪。

## Why this project?
传统的 RAG 工具通常按字符数或固定窗口大小切分代码，这破坏了代码的语义结构（例如，一个函数可能被切成两半）。
**Python-AST-RAG** 通过解析 Python 的 AST，确保每个代码块（Chunk）都是一个完整的函数或类，并自动追踪其所属的类（parent_name）和内部依赖项，从而提供更精准的代码上下文检索。

## 核心架构
```mermaid
graph TD
    A[源代码文件] --> B(AST Parser)
    B --> C{代码切分策略}
    C -->|FunctionDef| D[Code Chunk]
    C -->|ClassDef| D[Code Chunk]
    D --> E[Vector Store]
    D --> F[Metadata: dependencies, parent_name, etc.]
```

## 安装指南
```bash
git clone https://github.com/NRgamerwood/python-ast-rag.git
cd python-ast-rag
pip install -r requirements.txt
```

## 快速开始
```python
from src.parser import ASTParser

source_code = """
class MyClass:
    def hello(self):
        print("Hello World")
"""

parser = ASTParser()
chunks = parser.parse_source(source_code, "example.py")

for chunk in chunks:
    print(f"Name: {chunk.metadata.name}")
    print(f"Type: {chunk.metadata.node_type}")
    print(f"Parent: {chunk.metadata.parent_name}")
    print(f"Content:\n{chunk.content}")
```

## 项目结构
```text
python-ast-rag/
├── src/
│   ├── parser.py       # AST 解析核心逻辑
│   ├── vector_store.py # 向量数据库交互
│   └── utils.py        # 辅助工具
├── tests/              # 单元测试
├── examples/           # 示例代码库
├── requirements.txt
└── README.md
```

## 贡献指南
请遵循 PEP 8 规范，并确保所有新功能都有对应的单元测试。
Git 提交请使用 Conventional Commits 规范。
