# 知识图谱更新器，用于将三元组添加到用户画像知识图谱中

from typing import List, Dict, Any, Set, Optional
import json
import os
from datetime import datetime
import networkx as nx
from collections import defaultdict
from pathlib import Path


class GraphUpdater:
    """知识图谱更新器类"""
    
    def __init__(self, graph_store_path: str = None):
        """
        初始化用户画像图谱更新器
        
        Args:
            graph_store_path: 图谱存储路径，默认为data/graph_store/user_profile_graph.json
        """
        # 使用相对路径指向项目根目录
        project_root = Path(__file__).parent.parent.parent
        if graph_store_path is None:
            graph_store_path = project_root / "data" / "graph_store" / "user_profile_graph.json"
        else:
            graph_store_path = Path(graph_store_path)
        
        self.graph_store_path = graph_store_path
        self.graph = nx.MultiDiGraph()  # 使用有向多重图支持多种关系
        self.entity_attributes = {}  # 存储实体的属性信息
        self.relation_history = defaultdict(list)  # 存储关系的历史记录
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.graph_store_path), exist_ok=True)
        
        # 加载现有图谱
        self._load_graph()
    
    def add_triple(self, subject: str, predicate: str, obj: str, 
                   confidence: float = 1.0, timestamp: str = None) -> bool:
        """
        添加三元组到知识图谱
        
        Args:
            subject: 主语（实体）
            predicate: 谓语（关系）
            obj: 宾语（实体）
            confidence: 置信度
            timestamp: 时间戳
            
        Returns:
            是否成功添加
        """
        try:
            # 验证输入参数
            if not self._validate_triple_input(subject, predicate, obj):
                return False
                
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            # 1. 检查并添加实体
            self._ensure_entity_exists(subject)
            self._ensure_entity_exists(obj)
            
            # 2. 检查关系是否存在
            edge_key = self._get_edge_key(subject, obj, predicate)
            
            if self.graph.has_edge(subject, obj, key=edge_key):
                # 关系存在，覆盖更新
                self._update_existing_relation(subject, obj, predicate, confidence, timestamp)
            else:
                # 关系不存在，添加新关系
                self._add_new_relation(subject, obj, predicate, confidence, timestamp)
            
            # 3. 保存图谱
            self._save_graph()
            
            return True
            
        except Exception as e:
            print(f"添加三元组失败: {str(e)}")
            return False
    
    def add_triples_batch(self, triples: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量添加三元组
        
        Args:
            triples: 三元组列表，每个元素包含subject, predicate, object, confidence, timestamp
            
        Returns:
            统计信息：{'success': 成功数量, 'failed': 失败数量}
        """
        success_count = 0
        failed_count = 0
        
        for triple in triples:
            try:
                subject = triple.get('subject', '')
                predicate = triple.get('predicate', '')
                obj = triple.get('object', '')
                confidence = triple.get('confidence', 1.0)
                timestamp = triple.get('timestamp')
                
                if self.add_triple(subject, predicate, obj, confidence, timestamp):
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"处理三元组失败: {triple}, 错误: {str(e)}")
                failed_count += 1
        
        return {'success': success_count, 'failed': failed_count}
    
    def _validate_triple_input(self, subject: str, predicate: str, obj: str) -> bool:
        """
        验证三元组输入的有效性
        
        Args:
            subject: 主语
            predicate: 谓语
            obj: 宾语
            
        Returns:
            是否有效
        """
        # 检查是否为空或None
        if not subject or not predicate or not obj:
            return False
        
        # 检查是否为字符串类型
        if not isinstance(subject, str) or not isinstance(predicate, str) or not isinstance(obj, str):
            return False
        
        # 检查去除空白后是否为空
        if not subject.strip() or not predicate.strip() or not obj.strip():
            return False
        
        return True
    
    def _ensure_entity_exists(self, entity: str) -> None:
        """
        确保实体存在于图谱中
        
        Args:
            entity: 实体名称
        """
        if not self.graph.has_node(entity):
            # 添加新实体
            self.graph.add_node(entity)
            self.entity_attributes[entity] = {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'relation_count': 0
            }
        else:
            # 更新现有实体的时间戳
            if entity in self.entity_attributes:
                self.entity_attributes[entity]['updated_at'] = datetime.now().isoformat()
    
    def _get_edge_key(self, subject: str, obj: str, predicate: str) -> str:
        """
        生成边的唯一键
        
        Args:
            subject: 主语
            obj: 宾语
            predicate: 关系
            
        Returns:
            边的唯一键
        """
        return f"{predicate}"
    
    def _update_existing_relation(self, subject: str, obj: str, predicate: str, 
                                confidence: float, timestamp: str) -> None:
        """
        更新现有关系
        
        Args:
            subject: 主语
            obj: 宾语
            predicate: 关系
            confidence: 置信度
            timestamp: 时间戳
        """
        edge_key = self._get_edge_key(subject, obj, predicate)
        
        # 获取现有关系数据
        old_data = self.graph.edges[subject, obj, edge_key]
        
        # 保存历史记录
        history_key = f"{subject}-{predicate}-{obj}"
        self.relation_history[history_key].append({
            'old_confidence': old_data.get('confidence', 0.0),
            'old_timestamp': old_data.get('timestamp', ''),
            'updated_at': timestamp
        })
        
        # 更新关系属性
        self.graph.edges[subject, obj, edge_key].update({
            'predicate': predicate,
            'confidence': confidence,
            'timestamp': timestamp,
            'updated_at': timestamp,
            'update_count': old_data.get('update_count', 0) + 1
        })
    
    def _add_new_relation(self, subject: str, obj: str, predicate: str, 
                         confidence: float, timestamp: str) -> None:
        """
        添加新关系
        
        Args:
            subject: 主语
            obj: 宾语
            predicate: 关系
            confidence: 置信度
            timestamp: 时间戳
        """
        edge_key = self._get_edge_key(subject, obj, predicate)
        
        # 添加新边
        self.graph.add_edge(subject, obj, key=edge_key, 
                           predicate=predicate,
                           confidence=confidence,
                           timestamp=timestamp,
                           created_at=timestamp,
                           updated_at=timestamp,
                           update_count=0)
        
        # 更新实体的关系计数
        if subject in self.entity_attributes:
            self.entity_attributes[subject]['relation_count'] += 1
        if obj in self.entity_attributes:
            self.entity_attributes[obj]['relation_count'] += 1
    
    def get_entity_relations(self, entity: str) -> List[Dict[str, Any]]:
        """
        获取实体的所有关系
        
        Args:
            entity: 实体名称
            
        Returns:
            关系列表
        """
        relations = []
        
        # 获取出边（作为主语的关系）
        for target in self.graph.successors(entity):
            for edge_key, edge_data in self.graph[entity][target].items():
                relations.append({
                    'subject': entity,
                    'predicate': edge_data.get('predicate', ''),
                    'object': target,
                    'confidence': edge_data.get('confidence', 0.0),
                    'timestamp': edge_data.get('timestamp', ''),
                    'direction': 'outgoing'
                })
        
        # 获取入边（作为宾语的关系）
        for source in self.graph.predecessors(entity):
            for edge_key, edge_data in self.graph[source][entity].items():
                relations.append({
                    'subject': source,
                    'predicate': edge_data.get('predicate', ''),
                    'object': entity,
                    'confidence': edge_data.get('confidence', 0.0),
                    'timestamp': edge_data.get('timestamp', ''),
                    'direction': 'incoming'
                })
        
        return relations
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        获取图谱统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'entity_count': self.graph.number_of_nodes(),
            'relation_count': self.graph.number_of_edges(),
            'entities': list(self.graph.nodes()),
            'relation_types': list(set([data.get('predicate', '') 
                                      for _, _, data in self.graph.edges(data=True)])),
            'last_updated': datetime.now().isoformat()
        }
    
    def _load_graph(self) -> None:
        """
        从文件加载图谱数据（支持RDF格式）
        """
        try:
            if os.path.exists(self.graph_store_path):
                with open(self.graph_store_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查是否为RDF格式
                if 'triples' in data and '@type' in data:
                    # RDF格式加载
                    self._load_rdf_format(data)
                elif 'graph' in data:
                    # 旧格式兼容性加载
                    self._load_legacy_format(data)
                else:
                    # 初始化空图谱
                    self._initialize_empty_graph()
                
        except Exception as e:
            print(f"加载图谱失败: {str(e)}")
            # 初始化空图谱
            self._initialize_empty_graph()
    
    def _load_rdf_format(self, data: Dict[str, Any]) -> None:
        """
        加载RDF格式的图谱数据
        
        Args:
            data: RDF格式的数据
        """
        # 重建图谱
        self.graph = nx.MultiDiGraph()
        
        # 加载实体
        entities_data = data.get('entities', [])
        for entity_data in entities_data:
            entity_id = entity_data.get('@id', entity_data.get('name', ''))
            if entity_id:
                self.graph.add_node(entity_id)
                self.entity_attributes[entity_id] = entity_data.get('attributes', {})
        
        # 加载三元组
        triples_data = data.get('triples', [])
        for triple_data in triples_data:
            subject = triple_data.get('subject', {}).get('@id', '')
            predicate = triple_data.get('predicate', {}).get('name', '')
            obj = triple_data.get('object', {}).get('@id', '')
            
            if subject and predicate and obj:
                edge_key = self._get_edge_key(subject, obj, predicate)
                
                # 确保节点存在
                if not self.graph.has_node(subject):
                    self.graph.add_node(subject)
                if not self.graph.has_node(obj):
                    self.graph.add_node(obj)
                
                # 添加边
                self.graph.add_edge(subject, obj, key=edge_key,
                                   predicate=predicate,
                                   confidence=triple_data.get('confidence', 1.0),
                                   timestamp=triple_data.get('timestamp', ''),
                                   created_at=triple_data.get('created_at', ''),
                                   updated_at=triple_data.get('updated_at', ''),
                                   update_count=triple_data.get('update_count', 0))
        
        # 加载关系历史
        self.relation_history = defaultdict(list, data.get('relation_history', {}))
    
    def _load_legacy_format(self, data: Dict[str, Any]) -> None:
        """
        加载旧格式的图谱数据（兼容性）
        
        Args:
            data: 旧格式的数据
        """
        # 重建图谱
        graph_data = data.get('graph', {})
        if graph_data:
            self.graph = nx.node_link_graph(graph_data, 
                                           directed=True, 
                                           multigraph=True)
        
        # 加载实体属性
        self.entity_attributes = data.get('entity_attributes', {})
        
        # 加载关系历史
        self.relation_history = defaultdict(list, data.get('relation_history', {}))
    
    def _initialize_empty_graph(self) -> None:
        """
        初始化空图谱
        """
        self.graph = nx.MultiDiGraph()
        self.entity_attributes = {}
        self.relation_history = defaultdict(list)
    
    def _save_graph(self) -> None:
        """
        保存图谱数据到文件（RDF格式）
        """
        try:
            # 准备RDF格式的三元组数据
            rdf_triples = []
            for subject, obj, edge_key, edge_data in self.graph.edges(keys=True, data=True):
                rdf_triple = {
                    "@type": "Triple",
                    "subject": {
                        "@type": "Entity",
                        "@id": subject,
                        "name": subject
                    },
                    "predicate": {
                        "@type": "Relation",
                        "@id": edge_data.get('predicate', edge_key),
                        "name": edge_data.get('predicate', edge_key)
                    },
                    "object": {
                        "@type": "Entity",
                        "@id": obj,
                        "name": obj
                    },
                    "confidence": edge_data.get('confidence', 1.0),
                    "timestamp": edge_data.get('timestamp', ''),
                    "created_at": edge_data.get('created_at', ''),
                    "updated_at": edge_data.get('updated_at', ''),
                    "update_count": edge_data.get('update_count', 0)
                }
                rdf_triples.append(rdf_triple)
            
            # 准备实体数据
            entities = []
            for entity in self.graph.nodes():
                entity_data = {
                    "@type": "Entity",
                    "@id": entity,
                    "name": entity,
                    "attributes": self.entity_attributes.get(entity, {})
                }
                entities.append(entity_data)
            
            # 准备保存数据（RDF-JSON格式）
            save_data = {
                "@context": {
                    "@vocab": "http://user-profile-kg.org/",
                    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                    "xsd": "http://www.w3.org/2001/XMLSchema#"
                },
                "@type": "Graph",
                "@id": "user-profile-knowledge-graph",
                "triples": rdf_triples,
                "entities": entities,
                "statistics": {
                    "entity_count": len(entities),
                    "triple_count": len(rdf_triples),
                    "relation_types": list(set([triple["predicate"]["name"] for triple in rdf_triples]))
                },
                "relation_history": dict(self.relation_history),
                "metadata": {
                    "format": "RDF-JSON",
                    "last_saved": datetime.now().isoformat(),
                    "version": "1.0",
                    "description": "用户画像知识图谱 - RDF格式存储"
                }
            }
            
            # 保存到文件
            with open(self.graph_store_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存图谱失败: {str(e)}")
    
    def clear_graph(self) -> None:
        """
        清空图谱
        """
        self.graph.clear()
        self.entity_attributes.clear()
        self.relation_history.clear()
        self._save_graph()
    
    def export_graph(self, export_path: str, format_type: str = 'rdf-json') -> bool:
        """
        导出图谱数据
        
        Args:
            export_path: 导出路径
            format_type: 导出格式 ('rdf-json', 'json', 'gexf', 'graphml', 'turtle')
            
        Returns:
            是否成功导出
        """
        try:
            if format_type == 'rdf-json':
                # 使用当前的RDF-JSON格式保存
                self._save_graph_to_path(export_path)
            elif format_type == 'json':
                # 传统JSON格式
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'graph': nx.node_link_data(self.graph),
                        'statistics': self.get_graph_statistics()
                    }, f, ensure_ascii=False, indent=2)
            elif format_type == 'turtle':
                # Turtle格式导出
                self._export_turtle(export_path)
            elif format_type == 'gexf':
                nx.write_gexf(self.graph, export_path)
            elif format_type == 'graphml':
                nx.write_graphml(self.graph, export_path)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            return True
            
        except Exception as e:
            print(f"导出图谱失败: {str(e)}")
            return False
    
    def _save_graph_to_path(self, file_path: str) -> None:
        """
        将图谱保存到指定路径（RDF格式）
        
        Args:
            file_path: 保存路径
        """
        # 准备RDF格式的三元组数据
        rdf_triples = []
        for subject, obj, edge_key, edge_data in self.graph.edges(keys=True, data=True):
            rdf_triple = {
                "@type": "Triple",
                "subject": {
                    "@type": "Entity",
                    "@id": subject,
                    "name": subject
                },
                "predicate": {
                    "@type": "Relation",
                    "@id": edge_data.get('predicate', edge_key),
                    "name": edge_data.get('predicate', edge_key)
                },
                "object": {
                    "@type": "Entity",
                    "@id": obj,
                    "name": obj
                },
                "confidence": edge_data.get('confidence', 1.0),
                "timestamp": edge_data.get('timestamp', ''),
                "created_at": edge_data.get('created_at', ''),
                "updated_at": edge_data.get('updated_at', ''),
                "update_count": edge_data.get('update_count', 0)
            }
            rdf_triples.append(rdf_triple)
        
        # 准备实体数据
        entities = []
        for entity in self.graph.nodes():
            entity_data = {
                "@type": "Entity",
                "@id": entity,
                "name": entity,
                "attributes": self.entity_attributes.get(entity, {})
            }
            entities.append(entity_data)
        
        # 准备保存数据（RDF-JSON格式）
        save_data = {
            "@context": {
                "@vocab": "http://user-profile-kg.org/",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            },
            "@type": "Graph",
            "@id": "user-profile-knowledge-graph",
            "triples": rdf_triples,
            "entities": entities,
            "statistics": {
                "entity_count": len(entities),
                "triple_count": len(rdf_triples),
                "relation_types": list(set([triple["predicate"]["name"] for triple in rdf_triples]))
            },
            "relation_history": dict(self.relation_history),
            "metadata": {
                "format": "RDF-JSON",
                "last_saved": datetime.now().isoformat(),
                "version": "1.0",
                "description": "用户画像知识图谱 - RDF格式存储"
            }
        }
        
        # 保存到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    def _export_turtle(self, export_path: str) -> None:
        """
        导出为Turtle格式
        
        Args:
            export_path: 导出路径
        """
        turtle_content = []
        turtle_content.append("@prefix : <http://user-profile-kg.org/> .")
        turtle_content.append("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
        turtle_content.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
        turtle_content.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
        turtle_content.append("")
        
        # 添加三元组
        for subject, obj, edge_key, edge_data in self.graph.edges(keys=True, data=True):
            predicate = edge_data.get('predicate', edge_key)
            confidence = edge_data.get('confidence', 1.0)
            
            # 转换为安全的URI格式
            safe_subject = subject.replace(' ', '_').replace(':', '_')
            safe_object = obj.replace(' ', '_').replace(':', '_')
            safe_predicate = predicate.replace(' ', '_').replace(':', '_')
            
            turtle_content.append(f":{safe_subject} :{safe_predicate} :{safe_object} .")
            turtle_content.append(f":{safe_subject} :confidence \"{confidence}\"^^xsd:float .")
        
        # 保存到文件
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(turtle_content))