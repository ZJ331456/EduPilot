# 从用户文本中抽取三元组，用于构建用户画像知识图谱

from typing import List, Tuple, Dict, Any
import re
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chat.llm_gateway import LLMGateway


class TripleExtractor:
    """从用户文本中抽取三元组的类"""
    
    def __init__(self):
        """初始化三元组抽取器"""
        self.llm = LLMGateway()
        
        # 三元组抽取的提示词模板
        self.extraction_prompt = """
你是一个专业的用户画像分析助手。请从以下用户文本中抽取有价值的信息，用于构建用户画像。

请关注以下类型的信息：
- 用户的基本信息（姓名、年龄、职业、地点等）
- 用户的兴趣爱好和偏好
- 用户的行为习惯
- 用户的社交关系
- 用户的技能和经验
- 其他有助于了解用户特征的信息

请将抽取的信息组织成三元组形式（主语-关系-宾语），并评估每个信息的可信度。

请以JSON格式返回结果：
{{
  "triples": [
    {{
      "subject": "主语",
      "predicate": "关系",
      "object": "宾语",
      "confidence": 0.95
    }}
  ]
}}

注意：系统会自动为每个三元组添加时间戳信息。

用户文本：
{conversation}

请抽取用户画像信息：
"""
    
    def extract_triples(self, conversation: str) -> List[Dict[str, Any]]:
        """
        从用户文本中抽取三元组
        
        Args:
            conversation: 用户文本
            
        Returns:
            包含三元组和置信度的列表，每个元素格式为：
            {
                'subject': str,
                'predicate': str,
                'object': str,
                'confidence': float,
                'timestamp': str  # ISO格式时间戳
            }
        """
        try:
            # 预处理文本
            cleaned_text = self._preprocess_text(conversation)
            
            if not cleaned_text.strip():
                return []
            
            # 构建提示词
            prompt = self.extraction_prompt.format(conversation=cleaned_text)
            
            # 调用LLM进行三元组抽取
            response = self.llm.send_message(prompt, enable_search=False)
            
            # 解析LLM返回的结果
            triples = self._parse_llm_response(response)
            
            # 后处理和验证
            validated_triples = self._validate_triples(triples)
            
            return validated_triples
            
        except Exception as e:
            print(f"三元组抽取失败: {str(e)}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # 移除常见的无意义前缀（如果存在）
        prefixes_to_remove = ['用户：', '助手：', 'User:', 'Assistant:']
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """
        解析LLM返回的JSON格式结果
        
        Args:
            response: LLM返回的文本
            
        Returns:
            三元组列表
        """
        try:
            # 清理响应文本
            cleaned_response = response.strip()
            
            # 移除Markdown代码块标记
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # 移除 ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]   # 移除 ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # 移除结尾的 ```
            
            cleaned_response = cleaned_response.strip()
            
            # 尝试直接解析JSON
            if cleaned_response.startswith('{') and cleaned_response.endswith('}'):
                try:
                    data = json.loads(cleaned_response)
                    return data.get('triples', [])
                except json.JSONDecodeError:
                    pass
            
            # 尝试提取JSON部分（更宽松的匹配）
            json_patterns = [
                r'\{[\s\S]*?"triples"[\s\S]*?\[[\s\S]*?\][\s\S]*?\}',  # 完整JSON
                r'"triples"[\s]*:[\s]*\[[\s\S]*?\]',  # 只匹配triples数组
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, cleaned_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    
                    # 如果只匹配到triples数组，包装成完整JSON
                    if json_str.startswith('"triples"'):
                        json_str = '{' + json_str + '}'
                    
                    try:
                        data = json.loads(json_str)
                        triples = data.get('triples', [])
                        if triples:
                            return triples
                    except json.JSONDecodeError:
                        continue
            
            # 如果无法解析JSON，返回空列表
            return []
            
        except Exception as e:
            print(f"解析LLM响应失败: {str(e)}")
            return []
    
    def _validate_triples(self, triples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证和过滤三元组
        
        Args:
            triples: 原始三元组列表
            
        Returns:
            验证后的三元组列表
        """
        validated = []
        current_timestamp = datetime.now().isoformat()
        
        for triple in triples:
            if self._is_valid_triple(triple):
                # 确保置信度在合理范围内
                confidence = triple.get('confidence', 0.5)
                if confidence > 1.0:
                    confidence = 1.0
                elif confidence < 0.0:
                    confidence = 0.0
                
                triple['confidence'] = confidence
                # 添加时间戳
                triple['timestamp'] = current_timestamp
                validated.append(triple)
        
        return validated
    
    def _is_valid_triple(self, triple: Dict[str, Any]) -> bool:
        """
        检查三元组是否有效
        
        Args:
            triple: 三元组字典
            
        Returns:
            是否有效
        """
        # 检查必需字段
        required_fields = ['subject', 'predicate', 'object']
        for field in required_fields:
            if field not in triple or not triple[field]:
                return False
        
        subject = str(triple['subject']).strip()
        predicate = str(triple['predicate']).strip()
        obj = str(triple['object']).strip()
        
        # 检查长度
        if len(subject) < 1 or len(predicate) < 1 or len(obj) < 1:
            return False
        
        # 检查是否包含无意义的内容
        invalid_keywords = ['triples', 'json', 'subject', 'predicate', 'object', '主语', '谓语', '宾语']
        for keyword in invalid_keywords:
            if keyword.lower() in subject.lower() or keyword.lower() in obj.lower():
                return False
        
        return True
    
    def _calculate_confidence(self, triple: Tuple[str, str, str]) -> float:
        """
        计算三元组的置信度
        
        Args:
            triple: 三元组元组 (subject, predicate, object)
            
        Returns:
            置信度分数 (0.0-1.0)
        """
        subject, predicate, obj = triple
        
        # 基础置信度
        confidence = 0.5
        
        # 根据实体长度调整
        if len(subject) >= 2 and len(obj) >= 2:
            confidence += 0.2
        
        # 根据关系词调整
        common_relations = ['是', '在', '有', '属于', '喜欢', '工作于', '位于', '学习', '使用']
        if predicate in common_relations:
            confidence += 0.1
        
        # 根据实体类型调整
        if self._looks_like_person_name(subject):
            confidence += 0.1
        
        # 根据实体长度进一步调整
        if len(subject) > 10 or len(obj) > 10:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _looks_like_person_name(self, text: str) -> bool:
        """
        判断文本是否像人名
        
        Args:
            text: 文本
            
        Returns:
            是否像人名
        """
        # 简单的中文人名模式
        chinese_name_pattern = r'^[\u4e00-\u9fff]{2,4}$'
        return bool(re.match(chinese_name_pattern, text.strip()))
    
    def extract_filtered_triples(self, conversation: str, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """
        抽取三元组并根据置信度过滤
        
        Args:
            conversation: 用户文本
            min_confidence: 最小置信度阈值
            
        Returns:
            过滤后的三元组列表
        """
        triples = self.extract_triples(conversation)
        return [triple for triple in triples if triple.get('confidence', 0) >= min_confidence]
    
    def extract_batch(self, conversations: List[str]) -> List[List[Dict[str, Any]]]:
        """
        批量抽取三元组
        
        Args:
            conversations: 文本列表
            
        Returns:
            每个文本对应的三元组列表
        """
        results = []
        for conversation in conversations:
            results.append(self.extract_triples(conversation))
        return results