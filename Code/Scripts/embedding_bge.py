import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
CODE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = CODE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(CODE_DIR / ".env", override=False)

if os.getenv("HF_OFFLINE", "1").lower() in {"1", "true", "yes", "on"}:
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")


def project_path_from_env(name: str, default: Path) -> Path:
    raw_value = os.getenv(name)
    path = Path(raw_value).expanduser() if raw_value else default
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from tqdm import tqdm

DATA_PATH = project_path_from_env("LEGAL_DATA_PATH", PROJECT_ROOT / "Data")
DB_SAVE_PATH = project_path_from_env("CHROMA_DB_PATH", PROJECT_ROOT / "Model" / "chroma_db")
MANIFEST_PATH = DB_SAVE_PATH / "chroma_manifest.json"


def scan_files():
    """Scan Data/ for all .txt files and return {relative_path: mtime}."""
    files = {}
    if not DATA_PATH.exists():
        return files
    for root, dirs, filenames in os.walk(DATA_PATH):
        for filename in filenames:
            if filename.endswith(".txt"):
                file_path = Path(root) / filename
                rel = str(file_path.relative_to(DATA_PATH))
                files[rel] = file_path.stat().st_mtime
    return files


def load_manifest():
    """Load the manifest of previously embedded files."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_manifest(manifest):
    """Save the manifest."""
    DB_SAVE_PATH.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def load_documents(file_list):
    """Load .txt files from Data/ and return langchain documents."""
    documents = []
    for rel_path in file_list:
        file_path = DATA_PATH / rel_path
        if not file_path.exists():
            continue
        try:
            loader = TextLoader(str(file_path), encoding='utf-8')
            docs = loader.load()
        except UnicodeDecodeError:
            loader = TextLoader(str(file_path), encoding='gbk')
            docs = loader.load()
        except Exception as e:
            print(f"  跳过损坏文件 {rel_path}: {e}")
            continue

        category_path = str(Path(rel_path).parent) if Path(rel_path).parent != Path(".") else "根目录"
        for d in docs:
            d.metadata["source"] = Path(rel_path).name
            d.metadata["category_path"] = category_path
            d.metadata["file_path"] = rel_path
        documents.extend(docs)
    return documents


def run_embedding():
    force_rebuild = "--force" in sys.argv or "--rebuild" in sys.argv

    current_files = scan_files()
    if not current_files:
        raise FileNotFoundError(
            f"未在 {DATA_PATH} 下找到 .txt 法律文档。\n"
            "请创建 Data 目录并放入法条、案例等文本文件。"
        )

    print(f"扫描到 {len(current_files)} 个法律文本文件")

    manifest = load_manifest() if not force_rebuild else {}
    db_exists = DB_SAVE_PATH.exists() and any(DB_SAVE_PATH.iterdir())

    if force_rebuild:
        if db_exists:
            print("检测到 --force，删除旧向量库后重建...")
            import shutil
            shutil.rmtree(DB_SAVE_PATH)
            db_exists = False
        manifest = {}

    # Figure out which files need processing
    new_files = []
    modified_files = []
    unchanged_files = []

    for rel_path, mtime in current_files.items():
        if rel_path not in manifest:
            new_files.append(rel_path)
        elif manifest[rel_path] != mtime:
            modified_files.append(rel_path)
        else:
            unchanged_files.append(rel_path)

    # Files that were embedded before but no longer exist → stale (ignore, can't clean from ChromaDB easily)
    stale_files = [f for f in manifest if f not in current_files]

    if not db_exists:
        # First build — process everything
        print("首次构建：将处理所有文件")
        to_process = list(current_files.keys())
    elif not new_files and not modified_files:
        print("所有文件均为最新，知识库无需更新。")
        if stale_files:
            print(f"注意：{len(stale_files)} 个文件已从 Data/ 中删除，但仍在向量库中（不影响检索）")
        print(f"当前知识库包含 {len(manifest)} 个文件")
        return
    else:
        print(f"  新增文件：{len(new_files)} 个")
        print(f"  修改文件：{len(modified_files)} 个")
        print(f"  未变文件：{len(unchanged_files)} 个（跳过）")
        if stale_files:
            print(f"  已删除文件：{len(stale_files)} 个（将在下次重建时清除）")
        to_process = new_files + modified_files

    print(f"\n本次需处理 {len(to_process)} 个文件")

    # Load and split documents
    documents = load_documents(to_process)
    print(f"加载了 {len(documents)} 份文档")

    if not documents:
        print("没有可处理的文档内容")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    split_docs = text_splitter.split_documents(documents)
    print(f"切分为 {len(split_docs)} 个文本块")

    # Initialize embedding model
    print("初始化 BGE-M3 嵌入模型...")
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    # Open (or create) ChromaDB
    DB_SAVE_PATH.mkdir(parents=True, exist_ok=True)
    vectordb = Chroma(persist_directory=str(DB_SAVE_PATH), embedding_function=embeddings)

    # Add in batches
    batch_size = 100
    for i in tqdm(range(0, len(split_docs), batch_size), desc="向量化进度"):
        batch_docs = split_docs[i: i + batch_size]
        vectordb.add_documents(documents=batch_docs)

    # Update manifest with newly processed files
    for rel_path in to_process:
        manifest[rel_path] = current_files[rel_path]
    save_manifest(manifest)

    total_embedded = len(manifest)
    print(f"\n知识库更新完成！")
    print(f"  本次新增/更新：{len(to_process)} 个文件，{len(split_docs)} 个文本块")
    print(f"  知识库总计：{total_embedded} 个文件")
    print(f"  存储位置：{DB_SAVE_PATH}")


if __name__ == "__main__":
    run_embedding()
