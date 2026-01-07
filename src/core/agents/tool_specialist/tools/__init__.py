#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块
提供各种外部工具的实现，如计算器、网络搜索等
"""

from .calculator import CalculatorTool
from .web_search import WebSearchTool

__all__ = ["CalculatorTool", "WebSearchTool"]

