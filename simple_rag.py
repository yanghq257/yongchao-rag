import os
import jieba

# 文献存储路径（对应你创建的documents文件夹）
DOCS_DIR = "documents"


def load_documents():
    """加载所有涌潮参考文献"""
    documents = {}
    # 遍历documents文件夹里的所有txt文件
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".txt"):
            file_path = os.path.join(DOCS_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    documents[filename] = content
            except:
                # 兼容中文编码问题
                with open(file_path, "r", encoding="gbk") as f:
                    content = f.read()
                    documents[filename] = content
    return documents


def search_documents(keyword, documents):
    """根据关键词检索相关文献"""
    results = []
    # 分词（适配中文关键词）
    keyword_words = jieba.lcut(keyword)
    for doc_name, content in documents.items():
        # 检查关键词是否在文献中
        if any(word in content for word in keyword_words):
            # 截取前200字预览
            preview = content[:200] + "..." if len(content) > 200 else content
            results.append({
                "文献名称": doc_name,
                "内容预览": preview
            })
    return results


if __name__ == "__main__":
    print("===== 涌潮文献检索工具 =====")
    # 加载文献
    print("正在加载涌潮参考文献...")
    docs = load_documents()
    print(f"成功加载 {len(docs)} 篇文献\n")

    # 循环检索
    while True:
        keyword = input("请输入检索关键词（输入q退出）：")
        if keyword.lower() == "q":
            print("退出检索工具")
            break
        if not keyword:
            print("请输入有效关键词！")
            continue

        # 检索并展示结果
        results = search_documents(keyword, docs)
        if results:
            print(f"\n找到 {len(results)} 篇相关文献：")
            for i, res in enumerate(results, 1):
                print(f"\n{i}. {res['文献名称']}")
                print(f"   内容预览：{res['内容预览']}")
        else:
            print("\n未找到相关文献")
        print("-" * 50)