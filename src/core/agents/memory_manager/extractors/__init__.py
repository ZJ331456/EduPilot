#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取器模块 - 负责从文本中提取结构化信息
"""

from .triple_extractor import TripleExtractor
from .profile_insight_generator import ProfileInsightGenerator

__all__ = [
    'TripleExtractor',
    'ProfileInsightGenerator'
]

