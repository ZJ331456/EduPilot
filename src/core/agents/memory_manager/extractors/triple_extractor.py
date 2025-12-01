#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三元组提取器 - 负责从文本中提取用户信息三元组

混合提取策略：
1. LLM智能提取（主要方法）- 理解复杂语义和上下文
2. 规则提取（补充方法）- 快速准确的模式匹配
"""

import logging
import re
import json
from typing import Dict, Any, List
from datetime import datetime

from src.infrastructure.utils import ProfileDimension
from src.infrastructure.llm import Message, MessageRole, get_llm_manager


class TripleExtractor:
    """三元组提取器
    
    职责：
    1. 基于规则的三元组提取
    2. 基于语义的三元组推断
    3. 基于上下文的关系推断
    4. 概念关系三元组提取
    5. 三元组去重和合并
    """
    
    def __init__(self, use_llm: bool = True):
        """
        Args:
            use_llm: 是否使用 LLM 提取（默认 True）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.use_llm = use_llm
        self.llm_client = None
        self.extraction_rules = self._init_extraction_rules()
        
        # 初始化 LLM 客户端（优先使用本地 Ollama，速度更快）
        if self.use_llm:
            try:
                llm_manager = get_llm_manager()
                # 优先级：Ollama (本地) > Qwen (在线API)
                self.llm_client = llm_manager.get_client("ollama") or llm_manager.get_client("qwen")
                if self.llm_client:
                    client_name = "Ollama (本地)" if llm_manager.get_client("ollama") else "Qwen (在线)"
                    self.logger.info(f"三元组提取器：启用 LLM 智能提取模式 ({client_name})")
                else:
                    self.logger.warning("LLM 客户端不可用，将使用规则提取")
            except Exception as e:
                self.logger.warning(f"初始化 LLM 客户端失败: {e}，将使用规则提取")
    
    def extract(self, text: str) -> List[Dict[str, Any]]:
        """提取三元组
        
        Args:
            text: 要分析的文本
            
        Returns:
            三元组列表
        """
        self.logger.info(f"开始提取三元组，文本: {text[:50]}...")
        triples = []
        
        # 策略1：优先使用 LLM 智能提取
        if self.llm_client:
            llm_triples = self._extract_by_llm(text)
            if llm_triples:
                self.logger.info(f"✨ LLM 提取到 {len(llm_triples)} 个三元组")
                triples.extend(llm_triples)
        
        # 策略2：规则提取作为补充（总是执行，确保基本覆盖）
        rule_based_triples = self._extract_by_rules(text)
        self.logger.info(f"📋 规则提取到 {len(rule_based_triples)} 个三元组")
        triples.extend(rule_based_triples)
        
        # 策略3：语义推断（识别学科领域、学习动机等）
        semantic_triples = self._extract_semantic_triples(text)
        if semantic_triples:
            self.logger.info(f"🧠 语义推断到 {len(semantic_triples)} 个三元组")
            triples.extend(semantic_triples)
        
        # 策略4：上下文推断（感知难度、学习深度等）
        contextual_triples = self._extract_contextual_triples(text)
        if contextual_triples:
            triples.extend(contextual_triples)
        
        # 策略5：概念关系提取
        concept_triples = self._extract_concept_relations(text)
        if concept_triples:
            triples.extend(concept_triples)
        
        # 去重和合并相似三元组
        unique_triples = self._deduplicate_triples(triples)
        self.logger.info(f"✅ 最终提取 {len(unique_triples)} 个唯一三元组")
        
        return unique_triples
    
    def _extract_by_llm(self, text: str) -> List[Dict[str, Any]]:
        """使用 LLM 智能提取三元组"""
        if not self.llm_client:
            return []
        
        try:
            # # 对于简单的闲聊，跳过 LLM 提取以避免超时
            # if len(text) < 10:
            #     self.logger.info("文本过短，跳过 LLM 提取")
            #     return []
            
            prompt = self._build_llm_prompt(text)
            messages = [Message(role=MessageRole.USER, content=prompt)]
            
            # 添加超时保护：使用较短的 max_tokens 避免长时间等待
            response = self.llm_client.chat(
                messages=messages,
                temperature=0.3,  # 较低温度保证提取准确性
                max_tokens=500    # 减少 token 数以加快响应
            )
            
            # 解析 LLM 响应
            triples = self._parse_llm_response(response)
            return triples
            
        except Exception as e:
            self.logger.warning(f"LLM 提取失败（回退到规则提取）: {e}")
            return []
    
    def _build_llm_prompt(self, text: str) -> str:
        """构建 LLM 提取的 prompt"""
        return f"""你是一个专业的用户画像分析师。请从用户的话中提取关键信息，构建知识三元组（主体-关系-客体）。

**用户的话：**
{text}

**提取规则：**
1. 提取用户的兴趣爱好（喜欢/爱/热爱什么）
2. 提取用户的厌恶（不喜欢/讨厌什么）
3. 提取用户的技能（擅长/会/精通什么）
4. 提取用户的不足（不擅长/不会/不懂什么）
5. 提取用户的目标和愿望（想要/希望/打算做什么）
6. 提取用户的观点和看法（认为/觉得/以为什么）
7. 提取用户的学习兴趣和需求
8. 提取概念之间的关系

**输出格式（JSON数组）：**
```json
[
  {{
    "subject": "主体",
    "predicate": "关系",
    "object": "客体",
    "dimension": "interests|skills|goals|preferences|personality",
    "confidence": 0.0-1.0,
    "reason": "提取理由"
  }}
]
```

**示例：**
输入："我爱吃苹果，我觉得它很健康"
输出：
```json
[
  {{"subject": "用户", "predicate": "喜欢", "object": "吃苹果", "dimension": "interests", "confidence": 0.9, "reason": "明确表达喜好"}},
  {{"subject": "用户", "predicate": "认为", "object": "苹果很健康", "dimension": "preferences", "confidence": 0.85, "reason": "表达个人观点"}}
]
```

请直接输出JSON数组，不要其他解释。如果没有可提取的信息，返回空数组 []。"""
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """解析 LLM 的响应"""
        try:
            # 提取 JSON 内容（可能包含在 markdown 代码块中）
            json_str = response.strip()
            
            # 去除 markdown 代码块标记
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            # 解析 JSON
            parsed_triples = json.loads(json_str)
            
            if not isinstance(parsed_triples, list):
                self.logger.warning("LLM 返回的不是数组格式")
                return []
            
            # 格式化三元组，添加时间戳和来源
            formatted_triples = []
            for triple in parsed_triples:
                if not all(k in triple for k in ['subject', 'predicate', 'object']):
                    continue
                
                formatted_triple = {
                    'subject': triple['subject'],
                    'predicate': triple['predicate'],
                    'object': triple['object'],
                    'dimension': triple.get('dimension', 'interests'),
                    'confidence': triple.get('confidence', 0.8),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'llm_extraction',
                    'reason': triple.get('reason', '')
                }
                formatted_triples.append(formatted_triple)
                self.logger.info(
                    f"✨ LLM提取: {formatted_triple['subject']} - "
                    f"{formatted_triple['predicate']} - {formatted_triple['object']} "
                    f"(置信度: {formatted_triple['confidence']:.2f})"
                )
            
            return formatted_triples
            
        except json.JSONDecodeError as e:
            self.logger.error(f"解析 LLM 响应 JSON 失败: {e}\n响应内容: {response}")
            return []
        except Exception as e:
            self.logger.error(f"处理 LLM 响应失败: {e}")
            return []
    
    def _init_extraction_rules(self) -> List[Dict[str, Any]]:
        """初始化抽取规则"""
        return [
            {
                "pattern": r"我叫(.+?)(?:，|。|$)",
                "subject": "用户",
                "predicate": "姓名",
                "dimension": ProfileDimension.BASIC_INFO,
                "confidence": 0.9
            },
            {
                "pattern": r"我(?:喜欢|爱|热爱|很爱|超爱)(.+?)(?:，|。|？|$)",
                "subject": "用户",
                "predicate": "喜欢",
                "dimension": ProfileDimension.INTERESTS,
                "confidence": 0.85
            },
            {
                "pattern": r"我(?:不喜欢|讨厌|不爱)(.+?)(?:，|。|？|$)",
                "subject": "用户",
                "predicate": "不喜欢",
                "dimension": ProfileDimension.INTERESTS,
                "confidence": 0.85
            },
            {
                "pattern": r"我对(.+?)(?:感兴趣|很感兴趣|有兴趣)",
                "subject": "用户",
                "predicate": "感兴趣",
                "dimension": ProfileDimension.INTERESTS,
                "confidence": 0.85
            },
            {
                "pattern": r"我(?:擅长|会|精通|善于)(.+?)(?:，|。|？|$)",
                "subject": "用户",
                "predicate": "擅长",
                "dimension": ProfileDimension.SKILLS,
                "confidence": 0.8
            },
            {
                "pattern": r"我(?:不擅长|不会|不懂)(.+?)(?:，|。|？|$)",
                "subject": "用户",
                "predicate": "不擅长",
                "dimension": ProfileDimension.SKILLS,
                "confidence": 0.8
            },
            {
                "pattern": r"我(?:想要|想|希望|期望|打算)(.+?)(?:，|。|？|$)",
                "subject": "用户",
                "predicate": "目标",
                "dimension": ProfileDimension.GOALS,
                "confidence": 0.8
            },
            {
                "pattern": r"我(?:认为|觉得|感觉|以为)(.+?)(?:是|很|非常)(.+?)(?:，|。|？|$)",
                "subject": "用户观点",
                "predicate": "认为",
                "dimension": ProfileDimension.PREFERENCES,
                "confidence": 0.75
            },
            {
                "pattern": r"我想(?:学习|了解|知道)(.+?)(?:，|。|？|$)",
                "subject": "用户",
                "predicate": "学习目标",
                "dimension": ProfileDimension.GOALS,
                "confidence": 0.75
            },
            {
                "pattern": r"(?:什么是|介绍|解释)(.+?)(?:？|$)",
                "subject": "用户",
                "predicate": "学习兴趣",
                "dimension": ProfileDimension.INTERESTS,
                "confidence": 0.6
            },
            {
                "pattern": r"(.+?)(?:的历史|的文化|的特点|的意义)",
                "subject": "用户",
                "predicate": "关注领域",
                "dimension": ProfileDimension.INTERESTS,
                "confidence": 0.65
            },
            {
                "pattern": r"如何(?:学习|理解|掌握)(.+?)(?:？|$)",
                "subject": "用户",
                "predicate": "学习需求",
                "dimension": ProfileDimension.GOALS,
                "confidence": 0.7
            },
        ]
    
    def _extract_by_rules(self, text: str) -> List[Dict[str, Any]]:
        """基于规则的三元组提取"""
        triples = []
        
        for rule in self.extraction_rules:
            matches = re.findall(rule['pattern'], text)
            for match in matches:
                # 处理元组匹配结果（多组捕获）
                if isinstance(match, tuple):
                    obj = ' '.join([m.strip() for m in match if m.strip()])
                else:
                    obj = match.strip()
                
                if obj:  # 只添加非空结果
                    triple = {
                        'subject': rule['subject'],
                        'predicate': rule['predicate'],
                        'object': obj,
                        'dimension': rule['dimension'].value,
                        'confidence': rule['confidence'],
                        'timestamp': datetime.now().isoformat(),
                        'source': 'rule_based'
                    }
                    triples.append(triple)
                    self.logger.info(f"提取三元组: {rule['subject']} - {rule['predicate']} - {obj}")
        
        return triples
    
    def _extract_semantic_triples(self, text: str) -> List[Dict[str, Any]]:
        """基于语义的三元组提取"""
        triples = []
        
        # 学科领域识别
        academic_domains = self._identify_academic_domains(text)
        for domain in academic_domains:
            triples.append({
                "subject": "用户",
                "predicate": "关注学科",
                "object": domain,
                "dimension": ProfileDimension.INTERESTS.value,
                "confidence": 0.7,
                "source": "semantic_inference",
                "timestamp": datetime.now().isoformat()
            })
        
        # 学习动机识别
        learning_motivations = self._identify_learning_motivations(text)
        for motivation in learning_motivations:
            triples.append({
                "subject": "用户",
                "predicate": "学习动机",
                "object": motivation,
                "dimension": ProfileDimension.GOALS.value,
                "confidence": 0.6,
                "source": "semantic_inference",
                "timestamp": datetime.now().isoformat()
            })
        
        return triples
    
    def _extract_contextual_triples(self, text: str) -> List[Dict[str, Any]]:
        """基于上下文的关系推断"""
        triples = []
        
        # 困难度感知
        difficulty_level = self._assess_perceived_difficulty(text)
        if difficulty_level:
            triples.append({
                "subject": "用户",
                "predicate": "感知难度",
                "object": difficulty_level,
                "dimension": ProfileDimension.PREFERENCES.value,
                "confidence": 0.65,
                "source": "contextual_inference",
                "timestamp": datetime.now().isoformat()
            })
        
        # 学习深度偏好
        depth_preference = self._assess_learning_depth_preference(text)
        if depth_preference:
            triples.append({
                "subject": "用户",
                "predicate": "学习深度偏好",
                "object": depth_preference,
                "dimension": ProfileDimension.PREFERENCES.value,
                "confidence": 0.6,
                "source": "contextual_inference",
                "timestamp": datetime.now().isoformat()
            })
        
        return triples
    
    def _extract_concept_relations(self, text: str) -> List[Dict[str, Any]]:
        """提取概念间的关系"""
        triples = []
        
        # 比较关系
        comparison_patterns = [
            r"(.+?)和(.+?)(?:有什么区别|的区别)",
            r"(.+?)与(.+?)(?:的关系|的联系)"
        ]
        
        for pattern in comparison_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                concept_a = match.group(1).strip()
                concept_b = match.group(2).strip()
                if concept_a and concept_b:
                    triples.append({
                        "subject": concept_a,
                        "predicate": "比较关系",
                        "object": concept_b,
                        "dimension": ProfileDimension.INTERESTS.value,
                        "confidence": 0.8,
                        "source": "concept_relation_extraction",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return triples
    
    def _identify_academic_domains(self, text: str) -> List[str]:
        """识别学术领域"""
        domain_keywords = {
            "历史": ["历史", "古代", "朝代", "文化", "传统", "史记", "遗事"],
            "文学": ["文学", "诗歌", "小说", "散文", "作家", "作品"],
            "科学": ["科学", "实验", "理论", "研究", "技术"],
            "艺术": ["艺术", "绘画", "音乐", "美术", "设计"],
            "哲学": ["哲学", "思想", "理论", "观点", "思考"]
        }
        
        identified_domains = []
        text_lower = text.lower()
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_domains.append(domain)
        
        return identified_domains
    
    def _identify_learning_motivations(self, text: str) -> List[str]:
        """识别学习动机"""
        motivation_patterns = {
            "好奇心驱动": ["好奇", "想知道", "有趣", "探索"],
            "实用目的": ["有用", "实用", "应用", "工作"],
            "学术兴趣": ["深入", "研究", "学术", "理论"],
            "个人成长": ["提升", "成长", "发展", "进步"]
        }
        
        identified_motivations = []
        text_lower = text.lower()
        
        for motivation, patterns in motivation_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                identified_motivations.append(motivation)
        
        return identified_motivations
    
    def _assess_perceived_difficulty(self, text: str) -> str:
        """评估感知难度"""
        difficulty_indicators = {
            "简单": ["简单", "容易", "基础", "入门"],
            "中等": ["一般", "普通", "适中"],
            "困难": ["难", "复杂", "困惑", "不懂"]
        }
        
        text_lower = text.lower()
        for level, indicators in difficulty_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                return level
        
        return ""
    
    def _assess_learning_depth_preference(self, text: str) -> str:
        """评估学习深度偏好"""
        if any(word in text for word in ["详细", "深入", "全面", "系统"]):
            return "深度学习"
        elif any(word in text for word in ["简单", "概括", "大概", "简介"]):
            return "概括了解"
        
        return ""
    
    def _deduplicate_triples(self, triples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重和合并相似三元组"""
        unique_triples = {}
        
        for triple in triples:
            key = f"{triple['subject']}_{triple['predicate']}_{triple['object']}"
            
            if key in unique_triples:
                if triple['confidence'] > unique_triples[key]['confidence']:
                    unique_triples[key] = triple
            else:
                unique_triples[key] = triple
        
        return list(unique_triples.values())

