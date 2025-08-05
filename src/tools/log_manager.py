#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理工具
提供日志文件的清理、压缩、分析等功能
"""

import os
import gzip
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from config.logging_config import get_logger

class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.logger = get_logger("hw_agent.log_manager")
        
        # 确保日志目录存在
        self.log_dir.mkdir(exist_ok=True)
    
    def get_log_files(self) -> List[Path]:
        """获取所有日志文件"""
        log_files = []
        for file_path in self.log_dir.glob("*.log*"):
            if file_path.is_file():
                log_files.append(file_path)
        return sorted(log_files)
    
    def get_log_file_info(self, file_path: Path) -> Dict[str, Any]:
        """获取日志文件信息"""
        stat = file_path.stat()
        return {
            'name': file_path.name,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'created': datetime.fromtimestamp(stat.st_ctime)
        }
    
    def list_log_files(self) -> List[Dict[str, Any]]:
        """列出所有日志文件信息"""
        log_files = self.get_log_files()
        file_info_list = []
        
        for file_path in log_files:
            file_info = self.get_log_file_info(file_path)
            file_info_list.append(file_info)
        
        return file_info_list
    
    def compress_log_file(self, file_path: Path) -> Optional[Path]:
        """压缩日志文件"""
        if not file_path.exists():
            self.logger.warning(f"Log file not found: {file_path}")
            return None
        
        # 创建压缩文件名
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除原文件
            file_path.unlink()
            
            self.logger.info(f"Compressed log file: {file_path} -> {compressed_path}")
            return compressed_path
            
        except Exception as e:
            self.logger.error(f"Failed to compress log file {file_path}: {e}")
            return None
    
    def decompress_log_file(self, compressed_path: Path) -> Optional[Path]:
        """解压日志文件"""
        if not compressed_path.exists():
            self.logger.warning(f"Compressed log file not found: {compressed_path}")
            return None
        
        # 创建解压文件名
        decompressed_path = compressed_path.with_suffix('').with_suffix('.log')
        
        try:
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            self.logger.info(f"Decompressed log file: {compressed_path} -> {decompressed_path}")
            return decompressed_path
            
        except Exception as e:
            self.logger.error(f"Failed to decompress log file {compressed_path}: {e}")
            return None
    
    def clean_old_logs(self, days: int = 30, compress: bool = True) -> List[Path]:
        """清理旧日志文件"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_files = []
        
        for file_path in self.get_log_files():
            file_info = self.get_log_file_info(file_path)
            
            if file_info['modified'] < cutoff_date:
                if compress and not file_path.suffix.endswith('.gz'):
                    # 压缩文件
                    compressed_path = self.compress_log_file(file_path)
                    if compressed_path:
                        cleaned_files.append(compressed_path)
                else:
                    # 直接删除
                    try:
                        file_path.unlink()
                        cleaned_files.append(file_path)
                        self.logger.info(f"Deleted old log file: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete log file {file_path}: {e}")
        
        return cleaned_files
    
    def rotate_logs(self, max_size_mb: int = 100) -> List[Path]:
        """轮转大日志文件"""
        max_size_bytes = max_size_mb * 1024 * 1024
        rotated_files = []
        
        for file_path in self.get_log_files():
            if file_path.suffix.endswith('.gz'):
                continue  # 跳过已压缩的文件
            
            file_info = self.get_log_file_info(file_path)
            
            if file_info['size'] > max_size_bytes:
                # 创建备份文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f'.{timestamp}.log')
                
                try:
                    # 重命名文件
                    file_path.rename(backup_path)
                    
                    # 压缩备份文件
                    compressed_path = self.compress_log_file(backup_path)
                    if compressed_path:
                        rotated_files.append(compressed_path)
                    
                    self.logger.info(f"Rotated log file: {file_path} -> {compressed_path}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to rotate log file {file_path}: {e}")
        
        return rotated_files
    
    def analyze_log_file(self, file_path: Path, lines: int = 100) -> Dict[str, Any]:
        """分析日志文件"""
        if not file_path.exists():
            return {'error': 'File not found'}
        
        try:
            # 读取文件内容
            if file_path.suffix.endswith('.gz'):
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    content = f.read()
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            lines_list = content.split('\n')
            total_lines = len(lines_list)
            
            # 统计日志级别
            level_counts = {}
            for line in lines_list:
                for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                    if level in line:
                        level_counts[level] = level_counts.get(level, 0) + 1
                        break
            
            # 获取最后几行
            last_lines = lines_list[-lines:] if len(lines_list) > lines else lines_list
            
            return {
                'file_name': file_path.name,
                'total_lines': total_lines,
                'file_size_mb': self.get_log_file_info(file_path)['size_mb'],
                'level_counts': level_counts,
                'last_lines': last_lines
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def search_logs(self, keyword: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """搜索日志文件"""
        results = []
        
        for file_path in self.get_log_files():
            try:
                # 读取文件内容
                if file_path.suffix.endswith('.gz'):
                    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                        content = f.read()
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                lines = content.split('\n')
                matches = []
                
                for i, line in enumerate(lines, 1):
                    if case_sensitive:
                        if keyword in line:
                            matches.append({'line_number': i, 'content': line})
                    else:
                        if keyword.lower() in line.lower():
                            matches.append({'line_number': i, 'content': line})
                
                if matches:
                    results.append({
                        'file_name': file_path.name,
                        'matches': matches,
                        'total_matches': len(matches)
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to search in log file {file_path}: {e}")
        
        return results
    
    def get_log_summary(self) -> Dict[str, Any]:
        """获取日志摘要"""
        log_files = self.get_log_files()
        total_size = sum(self.get_log_file_info(f)['size'] for f in log_files)
        
        return {
            'total_files': len(log_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files': [self.get_log_file_info(f) for f in log_files]
        }

def main():
    """主函数 - 命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description='日志管理工具')
    parser.add_argument('--log-dir', default='logs', help='日志目录')
    parser.add_argument('--action', choices=['list', 'clean', 'rotate', 'compress', 'analyze'], 
                       required=True, help='执行的操作')
    parser.add_argument('--days', type=int, default=30, help='清理天数（用于clean操作）')
    parser.add_argument('--max-size', type=int, default=100, help='最大文件大小MB（用于rotate操作）')
    parser.add_argument('--file', help='要分析的文件名（用于analyze操作）')
    parser.add_argument('--keyword', help='搜索关键词')
    
    args = parser.parse_args()
    
    log_manager = LogManager(args.log_dir)
    
    if args.action == 'list':
        files = log_manager.list_log_files()
        print("日志文件列表:")
        for file_info in files:
            print(f"  {file_info['name']} - {file_info['size_mb']}MB - {file_info['modified']}")
    
    elif args.action == 'clean':
        cleaned = log_manager.clean_old_logs(args.days)
        print(f"清理了 {len(cleaned)} 个旧日志文件")
    
    elif args.action == 'rotate':
        rotated = log_manager.rotate_logs(args.max_size)
        print(f"轮转了 {len(rotated)} 个大日志文件")
    
    elif args.action == 'compress':
        files = log_manager.get_log_files()
        for file_path in files:
            if not file_path.suffix.endswith('.gz'):
                log_manager.compress_log_file(file_path)
        print("压缩完成")
    
    elif args.action == 'analyze':
        if args.file:
            file_path = Path(args.log_dir) / args.file
            analysis = log_manager.analyze_log_file(file_path)
            print(json.dumps(analysis, indent=2, ensure_ascii=False, default=str))
        else:
            summary = log_manager.get_log_summary()
            print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    main() 