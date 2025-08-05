#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接读取概念数据库中的原始文档
绕过嵌入向量，直接显示文档内容
"""

import json
from pathlib import Path

# 使用相对路径指向项目根目录
project_root = Path(__file__).parent.parent
base_path = project_root / "concept_knowledge_bases"

def read_concept_docs(concept_name):
    """读取指定概念的原始文档"""
    concept_path = base_path / concept_name / "graphrag_cache"
    
    # 读取原始文档
    full_docs_path = concept_path / "kv_store_full_docs.json"
    text_chunks_path = concept_path / "kv_store_text_chunks.json"
    
    print(f"🔍 检查概念: {concept_name}")
    print(f"📁 路径: {concept_path}")
    print(f"📁 绝对路径: {concept_path.absolute()}")
    print(f"📁 路径存在: {concept_path.exists()}")
    print("=" * 60)
    
    # 检查文件是否存在
    print(f"📄 full_docs文件: {full_docs_path.exists()} - {full_docs_path}")
    print(f"📚 text_chunks文件: {text_chunks_path.exists()} - {text_chunks_path}")
    
    if full_docs_path.exists():
        try:
            print("\n📄 读取原始文档...")
            with open(full_docs_path, 'r', encoding='utf-8') as f:
                full_docs = json.load(f)
            
            print(f"📊 文档数量: {len(full_docs)}")
            print(f"📊 文档键: {list(full_docs.keys())}")
                
            for doc_id, doc_content in full_docs.items():
                print(f"\n🆔 文档ID: {doc_id}")
                print(f"🔍 内容类型: {type(doc_content)}")
                
                if isinstance(doc_content, dict):
                    print(f"🔑 字典键: {list(doc_content.keys())}")
                    content = doc_content.get('content', doc_content.get('text', doc_content.get('data', str(doc_content))))
                else:
                    content = str(doc_content)
                
                # 显示前500字符
                if content:
                    preview = content[:500] + "..." if len(content) > 500 else content
                    print(f"📝 内容预览: {preview}")
                    print(f"📏 总长度: {len(content)}字符")
                else:
                    print("⚠️ 内容为空或None")
                    
        except Exception as e:
            print(f"❌ 读取full_docs失败: {e}")
    else:
        print("❌ full_docs文件不存在")
    
    if text_chunks_path.exists():
        try:
            print(f"\n📚 读取文本块...")
            with open(text_chunks_path, 'r', encoding='utf-8') as f:
                text_chunks = json.load(f)
                
            print(f"🧩 总块数: {len(text_chunks)}")
            print(f"🔑 块键示例: {list(text_chunks.keys())[:3]}")
            
            for i, (chunk_id, chunk_data) in enumerate(list(text_chunks.items())[:3]):
                print(f"\n   块 {i+1} (ID: {chunk_id}):")
                print(f"   类型: {type(chunk_data)}")
                
                if isinstance(chunk_data, dict):
                    print(f"   字典键: {list(chunk_data.keys())}")
                    chunk_content = chunk_data.get('content', chunk_data.get('text', chunk_data.get('data', str(chunk_data))))
                else:
                    chunk_content = str(chunk_data)
                
                if chunk_content:
                    preview = chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content
                    print(f"   内容: {preview}")
                else:
                    print("   ⚠️ 块内容为空")
                    
        except Exception as e:
            print(f"❌ 读取text_chunks失败: {e}")
    else:
        print("❌ text_chunks文件不存在")

if __name__ == "__main__":
    # 测试三国史记
    read_concept_docs("三国史记")
    
    print("\n" + "=" * 80)
    print("💡 说明：这些是您数据库中的真实内容")
    print("❌ 但由于嵌入维度不匹配，无法通过向量检索访问")
    print("✅ 重新生成数据库后就能正常检索了")