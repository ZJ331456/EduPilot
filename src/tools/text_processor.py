#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理工具
"""

import re
import jieba
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """提取文本关键词
    
    Args:
        text: 输入文本
        top_k: 返回关键词数量
        
    Returns:
        关键词列表
    """
    # 使用jieba分词
    words = jieba.cut(text)
    
    # 过滤停用词和短词
    stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    
    keywords = []
    for word in words:
        word = word.strip()
        if len(word) > 1 and word not in stop_words and not word.isdigit():
            keywords.append(word)
    
    # 统计词频
    word_count = {}
    for word in keywords:
        word_count[word] = word_count.get(word, 0) + 1
    
    # 按频率排序
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, count in sorted_words[:top_k]]

def calculate_similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        相似度分数 (0.0-1.0)
    """
    # 使用序列匹配器计算相似度
    return SequenceMatcher(None, text1, text2).ratio()

def normalize_text(text: str) -> str:
    """标准化文本
    
    Args:
        text: 输入文本
        
    Returns:
        标准化后的文本
    """
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 移除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
    
    return text

def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """将文本分割成块
    
    Args:
        text: 输入文本
        chunk_size: 块大小
        overlap: 重叠大小
        
    Returns:
        文本块列表
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # 如果不是最后一块，尝试在句号处分割
        if end < len(text):
            # 寻找最近的句号
            last_period = text.rfind('。', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1
        
        chunk = text[start:end]
        chunks.append(chunk)
        
        # 计算下一块的起始位置（考虑重叠）
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def extract_entities(text: str) -> List[Dict[str, Any]]:
    """提取文本中的实体
    
    Args:
        text: 输入文本
        
    Returns:
        实体列表
    """
    entities = []
    
    # 提取人名（简单规则）
    name_pattern = r'([\u4e00-\u9fff]{2,4})'
    names = re.findall(name_pattern, text)
    for name in names:
        entities.append({
            'text': name,
            'type': 'PERSON',
            'start': text.find(name),
            'end': text.find(name) + len(name)
        })
    
    # 提取地名
    location_pattern = r'([\u4e00-\u9fff]+(?:省|市|县|区|镇|村))'
    locations = re.findall(location_pattern, text)
    for location in locations:
        entities.append({
            'text': location,
            'type': 'LOCATION',
            'start': text.find(location),
            'end': text.find(location) + len(location)
        })
    
    return entities

def classify_text_topic(text: str) -> str:
    """分类文本主题
    
    Args:
        text: 输入文本
        
    Returns:
        主题分类
    """
    # 简单的关键词匹配分类
    topics = {
        'technology': ['技术', '科技', '计算机', '软件', '硬件', '编程', '算法'],
        'education': ['教育', '学习', '学校', '老师', '学生', '课程', '知识'],
        'business': ['商业', '企业', '公司', '市场', '经济', '投资', '管理'],
        'health': ['健康', '医疗', '医生', '医院', '疾病', '治疗', '保健'],
        'sports': ['运动', '体育', '比赛', '运动员', '健身', '训练'],
        'entertainment': ['娱乐', '电影', '音乐', '游戏', '综艺', '明星']
    }
    
    text_lower = text.lower()
    scores = {}
    
    for topic, keywords in topics.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        scores[topic] = score
    
    if not any(scores.values()):
        return 'general'
    
    return max(scores, key=scores.get)

def assess_text_complexity(text: str) -> str:
    """评估文本复杂度
    
    Args:
        text: 输入文本
        
    Returns:
        复杂度级别 ('simple', 'medium', 'complex')
    """
    # 计算平均句子长度
    sentences = re.split(r'[。！？]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return 'simple'
    
    avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
    
    # 计算词汇多样性
    words = list(jieba.cut(text))
    unique_words = set(words)
    vocabulary_diversity = len(unique_words) / len(words) if words else 0
    
    # 综合评分
    complexity_score = avg_sentence_length * 0.6 + vocabulary_diversity * 100 * 0.4
    
    if complexity_score < 15:
        return 'simple'
    elif complexity_score < 25:
        return 'medium'
    else:
        return 'complex' 