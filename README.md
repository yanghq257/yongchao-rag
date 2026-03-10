# 涌潮文献RAG项目
简单的检索增强生成（RAG）项目，包含8篇涌潮相关参考文献的检索功能。

## 项目内容
- `documents/`：存放8篇涌潮参考文献（文本格式）
- `simple_rag.py`：核心RAG检索代码（可根据关键词查找相关文献）
- `.gitignore`：忽略不需要上传的文件

## 使用方法
1. 安装Python依赖：`pip install python-docx jieba`
2. 运行检索：`python simple_rag.py`
3. 输入关键词（如「钱塘江涌潮」）即可检索相关文献