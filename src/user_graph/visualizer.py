# 原文件 b4 - 将实时更新的图谱生成实时更新的可视化图谱

from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime
import hashlib


class GraphVisualizer:
    """实时可视化知识图谱的类"""
    
    def __init__(self, cache_path: str):
        """
        初始化图谱可视化器
        
        Args:
            cache_path: 可视化缓存路径
        """
        self.cache_path = cache_path
        self.last_hash = None
        self.last_update_time = None
        
        # 确保缓存目录存在
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    def generate_visualization(self, graph_data: Dict[str, Any]) -> str:
        """
        生成图谱的可视化数据
        
        Args:
            graph_data: 图谱数据
            
        Returns:
            可视化数据的文件路径
        """
        # 检查数据是否有变化，实现增量更新
        current_hash = self._calculate_data_hash(graph_data)
        
        if self.last_hash == current_hash and os.path.exists(self.cache_path):
            # 数据未变化，直接返回缓存路径
            return self.cache_path
        
        # 创建网络图数据
        viz_data = self._create_network_data(graph_data)
        
        # 更新缓存
        self._update_cache(viz_data)
        
        # 更新状态
        self.last_hash = current_hash
        self.last_update_time = datetime.now()
        
        return self.cache_path
    
    def _create_network_data(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建网络图数据格式"""
        nodes = []
        edges = []
        
        # 处理实体节点
        entities = graph_data.get('entities', [])
        for entity in entities:
            node = {
                'id': entity.get('@id', ''),
                'label': entity.get('name', ''),
                'type': 'entity',
                'size': self._calculate_node_size(entity),
                'color': self._get_node_color(entity),
                'attributes': entity.get('attributes', {})
            }
            nodes.append(node)
        
        # 处理关系边
        triples = graph_data.get('triples', [])
        for i, triple in enumerate(triples):
            edge = {
                'id': f"edge_{i}",
                'source': triple.get('subject', {}).get('@id', ''),
                'target': triple.get('object', {}).get('@id', ''),
                'label': triple.get('predicate', {}).get('name', ''),
                'type': 'relation',
                'weight': triple.get('confidence', 0.5),
                'timestamp': triple.get('timestamp', ''),
                'attributes': {
                    'confidence': triple.get('confidence', 0.5),
                    'created_at': triple.get('created_at', ''),
                    'updated_at': triple.get('updated_at', ''),
                    'update_count': triple.get('update_count', 0)
                }
            }
            edges.append(edge)
        
        # 构建完整的可视化数据
        viz_data = {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'node_count': len(nodes),
                'edge_count': len(edges),
                'statistics': graph_data.get('statistics', {}),
                'format': 'network_graph'
            },
            'layout': {
                'algorithm': 'force_directed',
                'options': {
                    'iterations': 100,
                    'node_repulsion': 50,
                    'edge_attraction': 10
                }
            }
        }
        
        return viz_data
    
    def _update_cache(self, viz_data: Dict[str, Any]) -> None:
        """更新可视化缓存"""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(viz_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"更新可视化缓存失败: {str(e)}")
    
    def _calculate_data_hash(self, graph_data: Dict[str, Any]) -> str:
        """计算图谱数据的哈希值，用于检测变化"""
        # 提取关键数据用于哈希计算
        key_data = {
            'triples': graph_data.get('triples', []),
            'entities': graph_data.get('entities', []),
            'statistics': graph_data.get('statistics', {})
        }
        
        data_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    def _calculate_node_size(self, entity: Dict[str, Any]) -> int:
        """根据实体的关系数量计算节点大小"""
        relation_count = entity.get('attributes', {}).get('relation_count', 1)
        # 基础大小 + 关系数量的对数缩放
        base_size = 10
        scale_factor = 5
        return base_size + int(scale_factor * (relation_count ** 0.5))
    
    def _get_node_color(self, entity: Dict[str, Any]) -> str:
        """根据实体类型或属性确定节点颜色"""
        entity_id = entity.get('@id', '')
        
        # 根据实体ID或名称确定颜色
        if entity_id == '用户':
            return '#FF6B6B'  # 红色 - 中心用户
        elif any(keyword in entity_id for keyword in ['地点', '区域', '北京', '朝阳区']):
            return '#4ECDC4'  # 青色 - 地理位置
        elif any(keyword in entity_id for keyword in ['职业', '程序员', '工作']):
            return '#45B7D1'  # 蓝色 - 职业相关
        elif any(keyword in entity_id for keyword in ['兴趣', '爱好', '编程', '阅读']):
            return '#96CEB4'  # 绿色 - 兴趣爱好
        elif any(keyword in entity_id for keyword in ['年龄', '岁']):
            return '#FFEAA7'  # 黄色 - 个人信息
        else:
            return '#DDA0DD'  # 紫色 - 其他
    
    def get_real_time_stats(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取实时统计信息"""
        return {
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'cache_status': 'valid' if os.path.exists(self.cache_path) else 'invalid',
            'data_hash': self.last_hash,
            'node_count': len(graph_data.get('entities', [])),
            'edge_count': len(graph_data.get('triples', [])),
            'relation_types': graph_data.get('statistics', {}).get('relation_types', [])
        }
    
    def export_to_format(self, graph_data: Dict[str, Any], format_type: str = 'json') -> str:
        """导出为不同格式的可视化数据"""
        viz_data = self._create_network_data(graph_data)
        
        if format_type == 'json':
            return json.dumps(viz_data, ensure_ascii=False, indent=2)
        elif format_type == 'cytoscape':
            return self._convert_to_cytoscape(viz_data)
        elif format_type == 'd3':
            return self._convert_to_d3(viz_data)
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def _convert_to_cytoscape(self, viz_data: Dict[str, Any]) -> str:
        """转换为Cytoscape.js格式"""
        elements = []
        
        # 添加节点
        for node in viz_data['nodes']:
            elements.append({
                'data': {
                    'id': node['id'],
                    'label': node['label'],
                    'size': node['size'],
                    'color': node['color']
                }
            })
        
        # 添加边
        for edge in viz_data['edges']:
            elements.append({
                'data': {
                    'id': edge['id'],
                    'source': edge['source'],
                    'target': edge['target'],
                    'label': edge['label'],
                    'weight': edge['weight']
                }
            })
        
        return json.dumps({'elements': elements}, ensure_ascii=False, indent=2)
    
    def _convert_to_d3(self, viz_data: Dict[str, Any]) -> str:
        """转换为D3.js格式"""
        d3_data = {
            'nodes': viz_data['nodes'],
            'links': [{
                'source': edge['source'],
                'target': edge['target'],
                'label': edge['label'],
                'value': edge['weight']
            } for edge in viz_data['edges']]
        }
        
        return json.dumps(d3_data, ensure_ascii=False, indent=2)