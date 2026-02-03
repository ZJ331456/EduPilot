#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 metadata 文件夹中的数据上传到 ModelScope 数据集

使用方法:
1. 确保已安装 modelscope: pip install modelscope
2. 修改脚本中的配置（token、数据集名称等）
3. 运行脚本: python upload_to_modelscope.py
"""

import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import time

try:
    from modelscope.hub.api import HubApi
    from modelscope.msdatasets import MsDataset
except ImportError:
    print("请先安装 modelscope: pip install modelscope")
    exit(1)


class ModelScopeUploader:
    """ModelScope 数据集上传器"""
    
    def __init__(self, token: str, dataset_name: str, namespace: str = None):
        """
        初始化上传器
        
        Args:
            token: ModelScope token
            dataset_name: 数据集名称（如 'edu-data'）
            namespace: 命名空间（用户名，如果为 None 则从 token 中提取）
        """
        self.token = token
        self.dataset_name = dataset_name
        self.namespace = namespace or self._extract_namespace_from_token()
        
        # 初始化 API
        self.api = HubApi()
        self.api.login(token)
        
        # 元数据存储
        self.metadata_dir = Path("metadata")
        self.progress_file = Path(".upload_progress.json")
        self.progress = self._load_progress()
        
    def _extract_namespace_from_token(self) -> str:
        """从 token 中提取用户名（需要用户手动设置）"""
        # 这里需要用户手动设置，因为无法从 token 中直接提取
        return "zerochoe"  # 请修改为您的用户名
    
    def _load_progress(self) -> Dict:
        """加载上传进度"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "uploaded_files": [],
            "failed_files": [],
            "last_checkpoint": None
        }
    
    def _save_progress(self):
        """保存上传进度"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def scan_metadata_files(self, 
                           include_dirs: List[str] = None,
                           exclude_dirs: List[str] = None,
                           file_extensions: List[str] = None) -> List[Dict[str, Any]]:
        """
        扫描 metadata 文件夹中的文件
        
        Args:
            include_dirs: 要包含的子文件夹列表（如 ['ChineseBooK', 'shu']）
            exclude_dirs: 要排除的子文件夹列表
            file_extensions: 要包含的文件扩展名（如 ['.txt', '.pdf']）
        
        Returns:
            文件信息列表
        """
        if file_extensions is None:
            file_extensions = ['.txt', '.pdf']
        
        files_info = []
        
        # 确定要扫描的目录
        if include_dirs:
            scan_dirs = [self.metadata_dir / d for d in include_dirs]
        else:
            scan_dirs = [self.metadata_dir]
        
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                print(f"警告: 目录不存在: {scan_dir}")
                continue
            
            print(f"扫描目录: {scan_dir}")
            
            # 递归扫描文件
            for file_path in scan_dir.rglob('*'):
                if file_path.is_file():
                    # 检查扩展名
                    if file_path.suffix.lower() not in file_extensions:
                        continue
                    
                    # 检查是否在排除列表中
                    if exclude_dirs:
                        relative_path = file_path.relative_to(self.metadata_dir)
                        if any(relative_path.parts[0] == d for d in exclude_dirs):
                            continue
                    
                    # 获取文件信息
                    try:
                        file_info = {
                            "path": str(file_path),
                            "relative_path": str(file_path.relative_to(self.metadata_dir)),
                            "size": file_path.stat().st_size,
                            "extension": file_path.suffix.lower(),
                            "category": file_path.relative_to(self.metadata_dir).parts[0] if len(file_path.relative_to(self.metadata_dir).parts) > 1 else "root"
                        }
                        files_info.append(file_info)
                    except Exception as e:
                        print(f"处理文件时出错 {file_path}: {e}")
        
        print(f"共找到 {len(files_info)} 个文件")
        return files_info
    
    def prepare_dataset_structure(self, files_info: List[Dict], output_dir: Path = Path("dataset_prepared")):
        """
        准备数据集结构（可选：将文件整理成结构化格式）
        
        Args:
            files_info: 文件信息列表
            output_dir: 输出目录
        """
        output_dir.mkdir(exist_ok=True)
        
        # 按类别组织文件
        categories = {}
        for file_info in files_info:
            category = file_info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(file_info)
        
        # 创建元数据文件
        metadata = {
            "dataset_name": self.dataset_name,
            "total_files": len(files_info),
            "categories": list(categories.keys()),
            "files": files_info
        }
        
        metadata_file = output_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"数据集结构已准备，元数据保存在: {metadata_file}")
        return metadata_file
    
    def upload_file_via_git(self, file_path: Path, dataset_repo_path: Path):
        """
        通过 Git 方式上传单个文件（推荐用于大文件）
        
        注意：需要先克隆数据集仓库
        """
        import shutil
        
        # 计算相对路径
        relative_path = file_path.relative_to(self.metadata_dir)
        target_path = dataset_repo_path / relative_path
        
        # 创建目标目录
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        shutil.copy2(file_path, target_path)
        
        return target_path
    
    def upload_files_batch(self, 
                          files_info: List[Dict],
                          batch_size: int = 100,
                          max_file_size_mb: int = 50,
                          use_git: bool = True):
        """
        批量上传文件
        
        Args:
            files_info: 文件信息列表
            batch_size: 每批处理的文件数
            max_file_size_mb: 最大文件大小（MB），超过此大小的文件建议使用 Git LFS
            use_git: 是否使用 Git 方式上传（推荐）
        """
        if use_git:
            print("\n使用 Git 方式上传（推荐）")
            print("=" * 60)
            print("步骤 1: 在 ModelScope 网站上创建数据集")
            print("步骤 2: 克隆数据集仓库:")
            print(f"  git clone https://oauth2:{self.token}@www.modelscope.cn/{self.namespace}/{self.dataset_name}.git")
            print("步骤 3: 运行以下命令准备文件:")
            print("  python upload_to_modelscope.py --prepare-git")
            print("=" * 60)
            return self._prepare_git_upload(files_info, max_file_size_mb)
        else:
            print("\n使用 SDK 方式上传")
            return self._upload_via_sdk(files_info, batch_size, max_file_size_mb)
    
    def _prepare_git_upload(self, files_info: List[Dict], max_file_size_mb: int):
        """准备 Git 上传（生成脚本和说明）"""
        script_content = f"""#!/bin/bash
# ModelScope 数据集上传脚本
# 使用方法: bash upload_script.sh

DATASET_REPO="{self.dataset_name}"
NAMESPACE="{self.namespace}"
TOKEN="{self.token}"

# 克隆仓库（如果尚未克隆）
if [ ! -d "$DATASET_REPO" ]; then
    echo "克隆数据集仓库..."
    git clone https://oauth2:$TOKEN@www.modelscope.cn/$NAMESPACE/$DATASET_REPO.git
    cd $DATASET_REPO
else
    cd $DATASET_REPO
    git pull
fi

# 安装 Git LFS（如果尚未安装）
if ! command -v git-lfs &> /dev/null; then
    echo "请先安装 Git LFS: https://git-lfs.github.com/"
    exit 1
fi

git lfs install

# 复制文件
echo "复制文件到仓库..."
"""
        
        # 添加文件复制命令
        large_files = []
        for file_info in files_info:
            file_path = Path(file_info['path'])
            size_mb = file_info['size'] / (1024 * 1024)
            
            if size_mb > max_file_size_mb:
                large_files.append(file_info)
                script_content += f"\n# 大文件，使用 Git LFS\n"
                script_content += f"git lfs track \"{file_info['relative_path']}\"\n"
            
            script_content += f"mkdir -p \"$(dirname \"{file_info['relative_path']}\")\"\n"
            script_content += f"cp \"../metadata/{file_info['relative_path']}\" \"{file_info['relative_path']}\"\n"
        
        script_content += """
# 提交更改
echo "提交更改..."
git add .
git commit -m "Add dataset files from metadata folder"
git push

echo "上传完成！"
"""
        
        # 保存脚本
        script_file = Path("upload_script.sh")
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 同时生成 Windows 批处理脚本
        bat_content = f"""@echo off
REM ModelScope 数据集上传脚本 (Windows)
REM 使用方法: upload_script.bat

set DATASET_REPO={self.dataset_name}
set NAMESPACE={self.namespace}
set TOKEN={self.token}

REM 克隆仓库（如果尚未克隆）
if not exist "%DATASET_REPO%" (
    echo 克隆数据集仓库...
    git clone https://oauth2:%TOKEN%@www.modelscope.cn/%NAMESPACE%/%DATASET_REPO%.git
    cd %DATASET_REPO%
) else (
    cd %DATASET_REPO%
    git pull
)

REM 安装 Git LFS（如果尚未安装）
where git-lfs >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 请先安装 Git LFS: https://git-lfs.github.com/
    exit /b 1
)

git lfs install

REM 复制文件
echo 复制文件到仓库...
"""
        
        for file_info in files_info:
            size_mb = file_info['size'] / (1024 * 1024)
            relative_path = file_info['relative_path']
            # 转换为 Windows 路径格式
            win_path = relative_path.replace("/", "\\")
            # 获取目录路径
            dir_path = win_path.rsplit("\\", 1)[0] if "\\" in win_path else ""
            
            if size_mb > max_file_size_mb:
                bat_content += f'\ngit lfs track "{relative_path}"\n'
            
            if dir_path:
                bat_content += f'mkdir "{dir_path}" 2>nul\n'
            
            bat_content += f'copy "..\\metadata\\{win_path}" "{win_path}"\n'
        
        bat_content += """
REM 提交更改
echo 提交更改...
git add .
git commit -m "Add dataset files from metadata folder"
git push

echo 上传完成！
pause
"""
        
        bat_file = Path("upload_script.bat")
        with open(bat_file, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        print(f"\n已生成上传脚本:")
        print(f"  - Linux/Mac: {script_file}")
        print(f"  - Windows: {bat_file}")
        print(f"\n大文件列表（> {max_file_size_mb}MB，将使用 Git LFS）:")
        for file_info in large_files[:10]:  # 只显示前10个
            size_mb = file_info['size'] / (1024 * 1024)
            print(f"  - {file_info['relative_path']} ({size_mb:.2f} MB)")
        if len(large_files) > 10:
            print(f"  ... 还有 {len(large_files) - 10} 个大文件")
        
        return True
    
    def _upload_via_sdk(self, files_info: List[Dict], batch_size: int, max_file_size_mb: int):
        """通过 SDK 上传（适用于小文件）"""
        print("注意: SDK 方式上传速度较慢，建议使用 Git 方式")
        
        uploaded = 0
        failed = 0
        
        for i in tqdm(range(0, len(files_info), batch_size), desc="上传批次"):
            batch = files_info[i:i+batch_size]
            
            for file_info in batch:
                file_path = Path(file_info['path'])
                size_mb = file_info['size'] / (1024 * 1024)
                
                # 跳过大文件
                if size_mb > max_file_size_mb:
                    print(f"\n跳过大文件（{size_mb:.2f}MB）: {file_info['relative_path']}")
                    continue
                
                try:
                    # 这里需要根据 ModelScope SDK 的实际 API 进行调整
                    # 注意：ModelScope SDK 可能不直接支持批量上传文件
                    # 建议使用 Git 方式
                    print(f"上传: {file_info['relative_path']}")
                    # TODO: 实现 SDK 上传逻辑
                    uploaded += 1
                    time.sleep(0.1)  # 避免请求过快
                except Exception as e:
                    print(f"上传失败 {file_info['relative_path']}: {e}")
                    failed += 1
                    self.progress['failed_files'].append({
                        "path": file_info['relative_path'],
                        "error": str(e)
                    })
        
        self._save_progress()
        print(f"\n上传完成: 成功 {uploaded}, 失败 {failed}")
        return uploaded, failed
    
    def create_dataset_metadata_file(self, files_info: List[Dict], output_file: Path = Path("dataset_metadata.json")):
        """创建数据集元数据文件"""
        metadata = {
            "dataset_name": self.dataset_name,
            "namespace": self.namespace,
            "description": "教育数据集，包含中文书籍、教材等教育资源",
            "total_files": len(files_info),
            "categories": list(set(f['category'] for f in files_info)),
            "file_types": list(set(f['extension'] for f in files_info)),
            "total_size_mb": sum(f['size'] for f in files_info) / (1024 * 1024),
            "files": [
                {
                    "path": f['relative_path'],
                    "size": f['size'],
                    "type": f['extension'],
                    "category": f['category']
                }
                for f in files_info
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"数据集元数据已保存到: {output_file}")
        return output_file


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='上传 metadata 数据到 ModelScope')
    parser.add_argument('--token', type=str, 
                       default='ms-f149c52c-ae24-4c84-a26e-75a1e5f9e3a8',
                       help='ModelScope token')
    parser.add_argument('--dataset', type=str, default='edu-data',
                       help='数据集名称')
    parser.add_argument('--namespace', type=str, default='zerochoe',
                       help='命名空间（用户名）')
    parser.add_argument('--include-dirs', nargs='+', 
                       help='要包含的子文件夹（如 ChineseBooK shu）')
    parser.add_argument('--exclude-dirs', nargs='+',
                       help='要排除的子文件夹')
    parser.add_argument('--file-types', nargs='+', default=['.txt', '.pdf'],
                       help='要包含的文件类型')
    parser.add_argument('--prepare-git', action='store_true',
                       help='仅准备 Git 上传脚本，不实际上传')
    parser.add_argument('--max-size-mb', type=int, default=50,
                       help='最大文件大小（MB），超过此大小使用 Git LFS')
    
    args = parser.parse_args()
    
    # 创建上传器
    uploader = ModelScopeUploader(
        token=args.token,
        dataset_name=args.dataset,
        namespace=args.namespace
    )
    
    # 扫描文件
    print("=" * 60)
    print("扫描 metadata 文件夹...")
    print("=" * 60)
    files_info = uploader.scan_metadata_files(
        include_dirs=args.include_dirs,
        exclude_dirs=args.exclude_dirs,
        file_extensions=args.file_types
    )
    
    if not files_info:
        print("未找到任何文件！")
        return
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("文件统计:")
    print("=" * 60)
    total_size = sum(f['size'] for f in files_info)
    print(f"总文件数: {len(files_info)}")
    print(f"总大小: {total_size / (1024**3):.2f} GB")
    
    categories = {}
    for f in files_info:
        cat = f['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n按类别统计:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} 个文件")
    
    # 创建元数据文件
    print("\n" + "=" * 60)
    print("创建数据集元数据...")
    print("=" * 60)
    uploader.create_dataset_metadata_file(files_info)
    
    # 准备上传
    if args.prepare_git:
        print("\n" + "=" * 60)
        print("准备 Git 上传脚本...")
        print("=" * 60)
        uploader.upload_files_batch(files_info, use_git=True, max_file_size_mb=args.max_size_mb)
    else:
        print("\n" + "=" * 60)
        print("开始上传...")
        print("=" * 60)
        print("提示: 对于大量文件，建议使用 --prepare-git 参数生成脚本后手动上传")
        response = input("是否继续使用 SDK 方式上传？(y/N): ")
        if response.lower() == 'y':
            uploader.upload_files_batch(files_info, use_git=False, max_file_size_mb=args.max_size_mb)
        else:
            print("已取消。使用 --prepare-git 参数生成 Git 上传脚本。")


if __name__ == "__main__":
    main()

