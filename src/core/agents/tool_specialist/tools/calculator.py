#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算器工具
提供安全的数学计算功能
"""

import math
import re
import logging
from typing import Optional, Dict, Any


class CalculatorTool:
    """计算器工具
    
    提供安全的数学表达式计算功能，支持基本运算和常用数学函数
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # 允许的数学函数
        self.allowed_functions = {
            "sqrt": math.sqrt,
            "pow": math.pow,
            "abs": abs,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }
    
    def is_calculation_request(self, query: str) -> bool:
        """判断是否是计算请求
        
        Args:
            query: 用户查询
            
        Returns:
            是否是计算请求
        """
        # 计算相关的关键词
        calculation_keywords = [
            "计算", "多少", "等于", "结果", "答案",
            "+", "-", "*", "/", "×", "÷",
            "sqrt", "pow", "sin", "cos", "tan",
            "log", "平方", "立方", "开方"
        ]
        
        # 检查是否包含计算关键词和数字
        has_keyword = any(k in query for k in calculation_keywords)
        has_number = any(char.isdigit() for char in query)
        
        return has_keyword and has_number
    
    def extract_expression(self, query: str) -> Optional[str]:
        """从查询中提取数学表达式
        
        Args:
            query: 用户查询
            
        Returns:
            提取的数学表达式，如果无法提取则返回None
        """
        # 先尝试提取完整的函数调用表达式
        # 匹配函数调用：函数名(参数)
        function_pattern = r'(?:sqrt|pow|sin|cos|tan|log|log10|exp|abs)\s*\([^)]+\)'
        function_matches = re.findall(function_pattern, query, re.IGNORECASE)
        
        if function_matches:
            # 如果找到函数调用，尝试提取包含函数的完整表达式
            # 构建一个更复杂的模式来匹配包含函数的表达式
            expression_parts = []
            
            # 提取所有函数调用
            for func_match in function_matches:
                expression_parts.append(func_match)
            
            # 提取数字、运算符和括号
            remaining = query
            for func_match in function_matches:
                remaining = remaining.replace(func_match, '', 1)
            
            # 从剩余部分提取数字和运算符
            math_pattern = r'[0-9\+\-\*\/\(\)\.\s]+'
            math_matches = re.findall(math_pattern, remaining)
            expression_parts.extend(math_matches)
            
            if expression_parts:
                expression = "".join(expression_parts).strip()
                expression = re.sub(r'\s+', '', expression)
                return expression if expression else None
        
        # 如果没有函数调用，使用原来的简单模式
        # 匹配数字、运算符、括号和函数名
        pattern = r'[0-9\+\-\*\/\(\)\.\s]+|sqrt|pow|sin|cos|tan|log|log10|exp|abs|pi|e'
        matches = re.findall(pattern, query, re.IGNORECASE)
        
        if matches:
            expression = "".join(matches).strip()
            # 清理多余的空白
            expression = re.sub(r'\s+', '', expression)
            return expression if expression else None
        
        return None
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        """执行安全的数学计算
        
        Args:
            expression: 数学表达式
            
        Returns:
            计算结果字典，包含 success, result, error 字段
        """
        try:
            # 编译表达式以检查安全性
            code = compile(expression, "<string>", "eval")
            
            # 检查代码中使用的名称是否都在允许列表中
            for name in code.co_names:
                if name not in self.allowed_functions:
                    return {
                        "success": False,
                        "result": None,
                        "error": f"不支持的函数或变量: {name}",
                        "expression": expression
                    }
            
            # 执行计算
            result = eval(code, {"__builtins__": {}}, self.allowed_functions)
            
            return {
                "success": True,
                "result": result,
                "error": None,
                "expression": expression
            }
            
        except SyntaxError as e:
            return {
                "success": False,
                "result": None,
                "error": f"表达式语法错误: {str(e)}",
                "expression": expression
            }
        except ZeroDivisionError:
            return {
                "success": False,
                "result": None,
                "error": "除零错误",
                "expression": expression
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"计算出错: {str(e)}",
                "expression": expression
            }
    
    def execute(self, query: str) -> Dict[str, Any]:
        """执行计算请求
        
        Args:
            query: 用户查询
            
        Returns:
            工具执行结果
        """
        # 提取表达式
        expression = self.extract_expression(query)
        
        if not expression:
            return {
                "success": False,
                "result": None,
                "error": "无法从查询中提取数学表达式",
                "query": query
            }
        
        # 执行计算
        result = self.calculate(expression)
        
        if result["success"]:
            self.logger.info(f"计算成功: {expression} = {result['result']}")
        else:
            self.logger.warning(f"计算失败: {result['error']}")
        
        return result

