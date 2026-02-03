#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速上传示例 - 将 metadata 数据上传到 ModelScope

这是一个简化版本，可以直接运行
"""

from upload_to_modelscope import ModelScopeUploader

# ==================== 配置区域 ====================
# 请修改以下配置为您的实际信息

MODELSCOPE_TOKEN = 'ms-f149c52c-ae24-4c84-a26e-75a1e5f9e3a8'  # 您的 token
DATASET_NAME = 'edu-data'  # 数据集名称
NAMESPACE = 'zerochoe'  # 您的用户名

# 上传选项
INCLUDE_DIRS = None  # 要包含的文件夹，如 ['ChineseBooK', 'shu']，None 表示全部
EXCLUDE_DIRS = None  # 要排除的文件夹，如 ['ChinaTextbook']
FILE_TYPES = ['.txt', '.pdf']  # 要上传的文件类型
MAX_FILE_SIZE_MB = 50  # 超过此大小的文件使用 Git LFS

# ==================== 执行上传 ====================

def main():
    print("=" * 60)
    print("ModelScope 数据集上传工具")
    print("=" * 60)
    
    # 创建上传器
    uploader = ModelScopeUploader(
        token=MODELSCOPE_TOKEN,
        dataset_name=DATASET_NAME,
        namespace=NAMESPACE
    )
    
    # 扫描文件
    print("\n[1/4] 扫描 metadata 文件夹...")
    files_info = uploader.scan_metadata_files(
        include_dirs=INCLUDE_DIRS,
        exclude_dirs=EXCLUDE_DIRS,
        file_extensions=FILE_TYPES
    )
    
    if not files_info:
        print("❌ 未找到任何文件！请检查配置。")
        return
    
    # 显示统计
    print("\n[2/4] 文件统计:")
    total_size = sum(f['size'] for f in files_info)
    print(f"  📁 总文件数: {len(files_info):,}")
    print(f"  💾 总大小: {total_size / (1024**3):.2f} GB")
    
    categories = {}
    for f in files_info:
        cat = f['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n  📊 按类别统计:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"    - {cat}: {count:,} 个文件")
    
    # 创建元数据
    print("\n[3/4] 创建数据集元数据...")
    uploader.create_dataset_metadata_file(files_info)
    
    # 生成上传脚本
    print("\n[4/4] 生成 Git 上传脚本...")
    uploader.upload_files_batch(
        files_info, 
        use_git=True, 
        max_file_size_mb=MAX_FILE_SIZE_MB
    )
    
    print("\n" + "=" * 60)
    print("✅ 准备完成！")
    print("=" * 60)
    print("\n下一步操作:")
    print("1. 检查生成的 upload_script.sh (Linux/Mac) 或 upload_script.bat (Windows)")
    print("2. 执行脚本进行实际上传")
    print("3. 在 ModelScope 网站上验证上传结果")
    print("\n提示: 如果数据量很大，建议分批上传")


if __name__ == "__main__":
    main()

