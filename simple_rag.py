import os
import jieba
import warnings
import re
from PyPDF2 import PdfReader
from datetime import datetime

# ===================== 全局配置 =====================
SUPPORTED_FORMATS = ['.txt', '.pdf']  # 支持的文件格式
TXT_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'latin-1']  # TXT编码适配
CONTEXT_LENGTH = 100  # 关键词前后上下文长度
EXPORT_DIR = "检索结果导出"  # 导出文件保存目录

# ===================== 警告清理 =====================
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message=r".*Multiple definitions in dictionary.*")


def load_single_pdf(file_path: str) -> str:
    """读取单个PDF文件的文本内容（兼容中文）"""
    try:
        reader = PdfReader(file_path)
        pdf_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                page_text = re.sub(r'\s+', ' ', page_text)
                pdf_text += page_text.encode('utf-8', 'ignore').decode('utf-8') + " "
        return pdf_text.strip()
    except Exception as e:
        print(f"⚠️  读取PDF {os.path.basename(file_path)} 失败：{str(e)}")
        return ""


def load_single_txt(file_path: str) -> str:
    """读取单个TXT文件的文本内容（自动适配编码）"""
    for encoding in TXT_ENCODINGS:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read().strip()
                content = re.sub(r'\n+', '\n', content)
                return content.encode('utf-8', 'ignore').decode('utf-8')
        except Exception:
            continue
    print(f"⚠️  读取TXT {os.path.basename(file_path)} 失败：不支持的编码格式")
    return ""


def load_all_documents(doc_dir: str = "documents") -> tuple:
    """加载所有文献，返回(文献内容字典, TXT数量, PDF数量)"""
    doc_contents = {}  # key: 文件名, value: 文本内容
    txt_count = 0
    pdf_count = 0

    if not os.path.exists(doc_dir):
        print(f"❌ 文件夹 {doc_dir} 不存在！请先创建并放入TXT/PDF文献")
        return {}, 0, 0

    print(f"📂 正在扫描 {doc_dir} 文件夹中的文献...")
    for filename in os.listdir(doc_dir):
        file_path = os.path.join(doc_dir, filename)
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext not in SUPPORTED_FORMATS:
            continue

        # 加载全文
        if file_ext == ".txt":
            content = load_single_txt(file_path)
            file_type = "TXT"
            if content:
                txt_count += 1
        elif file_ext == ".pdf":
            content = load_single_pdf(file_path)
            file_type = "PDF"
            if content:
                pdf_count += 1
        else:
            continue

        # 跳过空内容
        if not content:
            print(f"⚠️  {filename} 内容为空，跳过")
            continue

        doc_contents[filename] = {
            "content": content,
            "file_type": file_type
        }

    total_docs = txt_count + pdf_count
    print(f"✅ 文献加载完成：共{total_docs}篇（TXT{txt_count}篇+PDF{pdf_count}篇）\n")
    return doc_contents, txt_count, pdf_count


def keyword_retrieval(query: str, doc_contents: dict) -> list:
    """关键词检索（本地离线，字面匹配+上下文提取）"""
    if not doc_contents or not query.strip():
        return []

    print(f"🔍 正在检索包含「{query}」的文献...")
    results = []
    # 分词获取关键词列表（过滤无意义单字）
    keyword_list = jieba.lcut(query.strip().lower())
    keyword_list = [word for word in keyword_list if word.strip() and len(word) >= 2]

    for filename, doc_info in doc_contents.items():
        content = doc_info["content"].lower()
        file_type = doc_info["file_type"]

        # 检查是否包含任意关键词
        has_keyword = any(keyword in content for keyword in keyword_list)
        if not has_keyword:
            continue

        # 提取关键词上下文并高亮
        original_content = doc_info["content"]
        highlighted_content = original_content
        # 高亮所有匹配的关键词
        for word in keyword_list:
            if len(word) < 2:
                continue
            # 忽略大小写匹配
            pattern = re.compile(re.escape(word), re.IGNORECASE)

            def replace_func(m):
                return f"★★{m.group(0)}★★"

            highlighted_content = pattern.sub(replace_func, highlighted_content)

        # 截取关键词前后各100字上下文
        if len(highlighted_content) > 200:
            highlight_pos = highlighted_content.find("★★")
            if highlight_pos != -1:
                start = max(0, highlight_pos - CONTEXT_LENGTH)
                end = min(len(highlighted_content), highlight_pos + CONTEXT_LENGTH)
                highlighted_content = "..." + highlighted_content[start:end] + "..."
            else:
                highlighted_content = highlighted_content[:200] + "..."

        # 计算匹配度（匹配的关键词数量/总关键词数量）
        match_count = sum(1 for keyword in keyword_list if keyword in content)
        match_score = round(match_count / len(keyword_list), 3) if keyword_list else 0

        results.append({
            "filename": filename,
            "file_type": file_type,
            "content_context": highlighted_content,
            "match_score": match_score  # 匹配度分数（0-1）
        })

    # 按匹配度排序
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results


def export_results_to_txt(keyword: str, results: list):
    """将检索结果导出为TXT文件"""
    # 创建导出目录（不存在则新建）
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = re.sub(r'[\\/:*?"<>|]', '_', keyword)
    export_filename = f"{EXPORT_DIR}/检索结果_{safe_keyword}_{timestamp}.txt"

    # 写入结果
    with open(export_filename, "w", encoding="utf-8") as f:
        f.write(f"===== 涌潮文献检索结果 =====\n")
        f.write(f"检索关键词：{keyword}\n")
        f.write(f"检索时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"匹配文献数量：{len(results)}\n")
        f.write("=" * 60 + "\n\n")

        for idx, res in enumerate(results, 1):
            f.write(f"{idx}. [{res['file_type']}] {res['filename']}\n")
            f.write(f"   匹配度分数：{res['match_score']}\n")
            f.write(f"   关键词上下文：{res['content_context']}\n")
            f.write("\n" + "-" * 60 + "\n\n")

    print(f"\n📁 检索结果已导出至：{export_filename}")


def main():
    """主函数：纯本地离线版文献检索工具"""
    print("=" * 60)
    print("===== 涌潮文献检索工具（纯本地离线版）=====")
    print("📌 核心功能：TXT/PDF混合检索 | 关键词高亮 | 匹配度排序 | 结果导出")
    print("📌 特点：无需网络 | 无需模型 | 本地离线运行")
    print("=" * 60 + "\n")

    # 加载所有文献
    doc_contents, txt_count, pdf_count = load_all_documents("documents")
    if not doc_contents:
        print("❌ 无有效文献可检索，程序退出")
        return

    # 交互式检索
    print("💡 输入关键词即可检索（输入q退出）")
    while True:
        keyword = input("\n请输入检索关键词：")
        if keyword.lower() == "q":
            print("👋 退出检索工具，再见！")
            break
        if not keyword.strip():
            print("⚠️  关键词不能为空，请重新输入")
            continue

        # 执行关键词检索
        results = keyword_retrieval(keyword, doc_contents)

        # 输出结果
        print(f"\n✅ 检索完成！找到 {len(results)} 篇相关文献（按匹配度排序）：")
        print("-" * 60)
        for idx, res in enumerate(results, 1):
            print(f"{idx}. [{res['file_type']}] {res['filename']}")
            print(f"   匹配度：{res['match_score']}")
            print(f"   上下文：{res['content_context']}\n")

        # 询问是否导出
        export_choice = input("是否导出检索结果到TXT文件？(y/n)：")
        if export_choice.lower() == "y":
            export_results_to_txt(keyword, results)
        print("-" * 60)


if __name__ == "__main__":
    main()