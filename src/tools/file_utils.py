#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件工具模块
"""

import json
import yaml
import csv
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """加载JSON文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        加载的数据字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        return {}

def save_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
    """保存数据到JSON文件
    
    Args:
        file_path: 文件路径
        data: 要保存的数据
        indent: 缩进空格数
        
    Returns:
        是否保存成功
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False

def load_yaml_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """加载YAML文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        加载的数据字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load YAML file {file_path}: {e}")
        return {}

def save_yaml_file(file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
    """保存数据到YAML文件
    
    Args:
        file_path: 文件路径
        data: 要保存的数据
        
    Returns:
        是否保存成功
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        logger.error(f"Failed to save YAML file {file_path}: {e}")
        return False

def load_csv_file(file_path: Union[str, Path]) -> List[Dict[str, str]]:
    """加载CSV文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        数据列表，每行作为一个字典
    """
    try:
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    except Exception as e:
        logger.error(f"Failed to load CSV file {file_path}: {e}")
        return []

def save_csv_file(file_path: Union[str, Path], data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> bool:
    """保存数据到CSV文件
    
    Args:
        file_path: 文件路径
        data: 要保存的数据列表
        fieldnames: 字段名列表
        
    Returns:
        是否保存成功
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not fieldnames and data:
            fieldnames = list(data[0].keys())
        
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        logger.error(f"Failed to save CSV file {file_path}: {e}")
        return False

def load_pickle_file(file_path: Union[str, Path]) -> Any:
    """加载pickle文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        加载的数据
    """
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        logger.error(f"Failed to load pickle file {file_path}: {e}")
        return None

def save_pickle_file(file_path: Union[str, Path], data: Any) -> bool:
    """保存数据到pickle文件
    
    Args:
        file_path: 文件路径
        data: 要保存的数据
        
    Returns:
        是否保存成功
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"Failed to save pickle file {file_path}: {e}")
        return False

def ensure_directory(directory_path: Union[str, Path]) -> bool:
    """确保目录存在
    
    Args:
        directory_path: 目录路径
        
    Returns:
        是否成功创建或目录已存在
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        return False

def get_file_extension(file_path: Union[str, Path]) -> str:
    """获取文件扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件扩展名（包含点号）
    """
    return Path(file_path).suffix

def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节）
    """
    try:
        return Path(file_path).stat().st_size
    except Exception as e:
        logger.error(f"Failed to get file size for {file_path}: {e}")
        return 0

def list_files(directory_path: Union[str, Path], pattern: str = "*") -> List[Path]:
    """列出目录中的文件
    
    Args:
        directory_path: 目录路径
        pattern: 文件匹配模式
        
    Returns:
        文件路径列表
    """
    try:
        directory = Path(directory_path)
        if not directory.exists():
            return []
        
        return list(directory.glob(pattern))
    except Exception as e:
        logger.error(f"Failed to list files in {directory_path}: {e}")
        return []

def copy_file(source_path: Union[str, Path], dest_path: Union[str, Path]) -> bool:
    """复制文件
    
    Args:
        source_path: 源文件路径
        dest_path: 目标文件路径
        
    Returns:
        是否复制成功
    """
    try:
        import shutil
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        return True
    except Exception as e:
        logger.error(f"Failed to copy file from {source_path} to {dest_path}: {e}")
        return False

def move_file(source_path: Union[str, Path], dest_path: Union[str, Path]) -> bool:
    """移动文件
    
    Args:
        source_path: 源文件路径
        dest_path: 目标文件路径
        
    Returns:
        是否移动成功
    """
    try:
        import shutil
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source_path, dest_path)
        return True
    except Exception as e:
        logger.error(f"Failed to move file from {source_path} to {dest_path}: {e}")
        return False

def delete_file(file_path: Union[str, Path]) -> bool:
    """删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否删除成功
    """
    try:
        Path(file_path).unlink()
        return True
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}: {e}")
        return False

def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """读取文本文件
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
        
    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read text file {file_path}: {e}")
        return ""

def write_text_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
    """写入文本文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
        
    Returns:
        是否写入成功
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to write text file {file_path}: {e}")
        return False 