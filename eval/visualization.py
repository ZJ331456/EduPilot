#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验结果可视化分析 - 顶级论文标准版
生成高质量、学术级别的可视化图表
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import matplotlib
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import platform
import matplotlib.font_manager as fm

# 根据操作系统选择合适的字体
if platform.system() == 'Windows':
    # Windows系统字体配置
    chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']
    english_fonts = ['Arial', 'DejaVu Sans', 'Liberation Sans']
elif platform.system() == 'Darwin':  # macOS
    chinese_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Arial Unicode MS']
    english_fonts = ['Arial', 'Helvetica', 'DejaVu Sans']
else:  # Linux
    chinese_fonts = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'DejaVu Sans']
    english_fonts = ['DejaVu Sans', 'Liberation Sans', 'Arial']

# 查找可用的字体
available_fonts = []
for font in chinese_fonts + english_fonts:
    try:
        fm.findfont(font)
        available_fonts.append(font)
    except:
        continue

if available_fonts:
    matplotlib.rcParams['font.sans-serif'] = available_fonts
    print(f"✅ 使用字体: {available_fonts[0]}")
else:
    # 如果没有找到合适字体，使用默认字体
    matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
    print("⚠️ 未找到合适的中文字体，使用默认字体")

matplotlib.rcParams['axes.unicode_minus'] = False

# 设置学术级图表样式
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# 定义学术级配色方案
ACADEMIC_COLORS = {
    'primary': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3A1772'],
    'secondary': ['#6B8E23', '#CD853F', '#8B4513', '#708090', '#2F4F4F'],
    'accent': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
    'neutral': ['#F8F9FA', '#E9ECEF', '#DEE2E6', '#CED4DA', '#ADB5BD']
}

# 定义学术级图表参数
ACADEMIC_STYLE = {
    'figure.dpi': 300,
    'figure.figsize': (12, 8),
    'axes.linewidth': 1.5,
    'axes.edgecolor': '#2C3E50',
    'axes.labelcolor': '#2C3E50',
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'font.size': 12,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.8
}

class AcademicExperimentVisualizer:
    """学术级实验结果可视化器"""
    
    def __init__(self, results_file: str = None):
        self.results_file = results_file
        self.results = None
        self.df = None
        
        # 应用学术级样式
        plt.rcParams.update(ACADEMIC_STYLE)
        
        if results_file:
            self.load_results(results_file)
    
    def _get_system_labels(self):
        """获取系统标签的英文映射"""
        if self.df is None:
            return []
        
        systems = self.df['system'].unique()
        system_labels = []
        
        for sys in systems:
            # 将中文系统名称映射为英文
            if '基础' in sys:
                system_labels.append('Basic Config')
            elif '标准' in sys:
                system_labels.append('Standard Config')
            elif '增强' in sys:
                system_labels.append('Enhanced Config')
            elif '专家' in sys:
                system_labels.append('Expert Config')
            else:
                system_labels.append(sys)
        
        return system_labels
    
    def load_results(self, results_file: str):
        """加载实验结果"""
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                self.results = json.load(f)
            
            # 转换为DataFrame
            self._convert_to_dataframe()
            print(f"✅ 成功加载结果文件: {results_file}")
            
        except Exception as e:
            print(f"❌ 加载结果文件失败: {e}")
    
    def _convert_to_dataframe(self):
        """将结果转换为DataFrame"""
        data = []
        for system_name, results in self.results.items():
            if system_name != "statistics" and isinstance(results, list):
                for result in results:
                    if result.get("success", False):
                        row = {
                            "system": system_name,
                            "query_id": result.get("query_id", ""),
                            "user_id": result.get("user_id", ""),
                            "response_time": result.get("response_time", 0),
                            "accuracy": result.get("quality_scores", {}).get("accuracy", 0),
                            "completeness": result.get("quality_scores", {}).get("completeness", 0),
                            "explanation_quality": result.get("quality_scores", {}).get("explanation_quality", 0),
                            "learning_value": result.get("quality_scores", {}).get("learning_value", 0),
                        }
                        data.append(row)
        
        self.df = pd.DataFrame(data)
        
        # 计算综合评分
        self.df['composite_score'] = (
            self.df['accuracy'] * 0.3 +
            self.df['completeness'] * 0.25 +
            self.df['explanation_quality'] * 0.25 +
            self.df['learning_value'] * 0.2
        )
    
    def _create_academic_figure(self, figsize=(12, 8), title="", subtitle=""):
        """创建学术级图表"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # 设置标题和副标题
        if title:
            ax.set_title(title, fontsize=18, fontweight='bold', pad=20, color='#2C3E50')
        if subtitle:
            fig.suptitle(subtitle, fontsize=14, color='#7F8C8D', y=0.95)
        
        # 设置背景色
        ax.set_facecolor('#FAFAFA')
        fig.patch.set_facecolor('white')
        
        return fig, ax
    
    def plot_quality_comparison(self, save_path: str = None):
        """绘制质量对比图 - 学术级版本"""
        if self.df is None:
            print("请先加载结果数据")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Multi-Agent System Quality Comparison Analysis', fontsize=20, fontweight='bold', y=0.98)
        fig.patch.set_facecolor('white')
        
        metrics = [
            ('accuracy', 'Accuracy Score', '准确性评分'),
            ('completeness', 'Completeness Score', '完整性评分'),
            ('explanation_quality', 'Explanation Quality', '解释质量评分'),
            ('learning_value', 'Learning Value', '学习价值评分')
        ]
        
        for idx, (metric, eng_name, ch_name) in enumerate(metrics):
            ax = axes[idx//2, idx%2]
            ax.set_facecolor('#FAFAFA')
            
            # 创建箱线图
            box_plot = ax.boxplot([self.df[self.df['system'] == sys][metric].values 
                                  for sys in self.df['system'].unique()],
                                 patch_artist=True,
                                 medianprops=dict(color='#2C3E50', linewidth=2),
                                 flierprops=dict(marker='o', markerfacecolor='#E74C3C', markersize=4))
            
            # 设置箱体颜色
            colors = ACADEMIC_COLORS['primary']
            for patch, color in zip(box_plot['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            # 设置标签和标题
            ax.set_title(f'{eng_name}', fontsize=14, fontweight='bold', pad=15)
            ax.set_ylabel('Score', fontsize=12)
            
            # 使用英文标签，避免字体问题
            system_labels = self._get_system_labels()
            ax.set_xticklabels(system_labels, rotation=45, ha='right', fontsize=11)
            ax.grid(True, alpha=0.2, linewidth=0.5)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"📊 质量对比图已保存到: {save_path}")
        
        plt.show()
    
    def plot_composite_score_comparison(self, save_path: str = None):
        """绘制综合评分对比图 - 学术级版本"""
        if self.df is None:
            print("请先加载结果数据")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
        fig.suptitle('Composite Score Analysis and Ranking', fontsize=18, fontweight='bold', y=0.95)
        fig.patch.set_facecolor('white')
        
        # 左侧：箱线图
        ax1.set_facecolor('#FAFAFA')
        box_plot = ax1.boxplot([self.df[self.df['system'] == sys]['composite_score'].values 
                               for sys in self.df['system'].unique()],
                              patch_artist=True,
                              medianprops=dict(color='#2C3E50', linewidth=2),
                              flierprops=dict(marker='o', markerfacecolor='#E74C3C', markersize=4))
        
        colors = ACADEMIC_COLORS['primary']
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax1.set_title('Composite Score Distribution', fontsize=14, fontweight='bold', pad=15)
        ax1.set_ylabel('Composite Score', fontsize=12)
        ax1.set_xticklabels(self._get_system_labels(), rotation=45, ha='right')
        ax1.grid(True, alpha=0.3, linewidth=0.8)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        # 右侧：排名条形图
        ax2.set_facecolor('#FAFAFA')
        mean_scores = self.df.groupby('system')['composite_score'].mean().sort_values(ascending=False)
        
        # 创建渐变色彩
        colors = plt.cm.viridis(np.linspace(0, 1, len(mean_scores)))
        
        bars = ax2.bar(range(len(mean_scores)), mean_scores.values, 
                       color=colors, alpha=0.8, edgecolor='#2C3E50', linewidth=1)
        
        ax2.set_title('Average Composite Score Ranking', fontsize=14, fontweight='bold', pad=15)
        ax2.set_ylabel('Average Score', fontsize=12)
        ax2.set_xticks(range(len(mean_scores)))
        ax2.set_xticklabels(mean_scores.index, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3, linewidth=0.8, axis='y')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        # 添加数值标签和排名
        for i, (bar, score) in enumerate(zip(bars, mean_scores.values)):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{score:.3f}\n(#{i+1})', ha='center', va='bottom', 
                    fontweight='bold', fontsize=11)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"📊 综合评分对比图已保存到: {save_path}")
        
        plt.show()
    
    def plot_response_time_analysis(self, save_path: str = None):
        """绘制响应时间分析图 - 学术级版本"""
        if self.df is None:
            print("请先加载结果数据")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
        fig.suptitle('Response Time Performance Analysis', fontsize=18, fontweight='bold', y=0.95)
        fig.patch.set_facecolor('white')
        
        # 左侧：响应时间分布
        ax1.set_facecolor('#FAFAFA')
        box_plot = ax1.boxplot([self.df[self.df['system'] == sys]['response_time'].values 
                               for sys in self.df['system'].unique()],
                              patch_artist=True,
                              medianprops=dict(color='#2C3E50', linewidth=2),
                              flierprops=dict(marker='o', markerfacecolor='#E74C3C', markersize=4))
        
        colors = ACADEMIC_COLORS['accent']
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax1.set_title('Response Time Distribution', fontsize=14, fontweight='bold', pad=15)
        ax1.set_ylabel('Response Time (seconds)', fontsize=12)
        
        # 使用英文标签，避免字体问题
        system_labels = self._get_system_labels()
        ax1.set_xticklabels(system_labels, rotation=45, ha='right', fontsize=11)
        ax1.grid(True, alpha=0.2, linewidth=0.5)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        # 右侧：性能排名
        ax2.set_facecolor('#FAFAFA')
        mean_times = self.df.groupby('system')['response_time'].mean().sort_values()
        
        # 使用顶级期刊标准颜色
        colors = ACADEMIC_COLORS['primary']
        bars = ax2.bar(range(len(mean_times)), mean_times.values, 
                       color=colors[:len(mean_times)], alpha=0.8, edgecolor='#2C3E50', linewidth=1)
        
        ax2.set_title('Average Response Time Ranking', fontsize=14, fontweight='bold', pad=15)
        ax2.set_ylabel('Average Time (seconds)', fontsize=12)
        ax2.set_xticks(range(len(mean_times)))
        
        # 使用英文标签，避免字体问题
        ax2.set_xticklabels(system_labels, rotation=45, ha='right', fontsize=11)
        ax2.grid(True, alpha=0.2, linewidth=0.5, axis='y')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        # 添加数值标签和性能等级，避免重叠
        for i, (bar, time_val) in enumerate(zip(bars, mean_times.values)):
            height = bar.get_height()
            performance = "Fast" if i == 0 else "Medium" if i == 1 else "Slow"
            
            # 调整标签位置，避免重叠
            label_y = height + max(0.001, height * 0.05)  # 动态调整标签高度
            ax2.text(bar.get_x() + bar.get_width()/2., label_y,
                    f'{time_val:.3f}s\n({performance})', ha='center', va='bottom', 
                    fontweight='bold', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"📊 响应时间分析图已保存到: {save_path}")
        
        plt.show()
    
    def plot_radar_chart(self, save_path: str = None):
        """绘制雷达图对比 - 学术级版本"""
        if self.df is None:
            print("请先加载结果数据")
            return
        
        # 计算各系统的平均评分
        metrics = ['accuracy', 'completeness', 'explanation_quality', 'learning_value']
        metric_labels = ['Accuracy', 'Completeness', 'Explanation\nQuality', 'Learning\nValue']
        systems = self.df['system'].unique()
        
        # 准备数据
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]  # 闭合图形
        
        fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))
        fig.patch.set_facecolor('white')
        
        colors = ACADEMIC_COLORS['primary']
        
        for i, system in enumerate(systems):
            values = []
            for metric in metrics:
                mean_value = self.df[self.df['system'] == system][metric].mean()
                values.append(mean_value)
            
            values += values[:1]  # 闭合图形
            
            # 绘制雷达图
            ax.plot(angles, values, 'o-', linewidth=3, label=system, color=colors[i], markersize=8)
            ax.fill(angles, values, alpha=0.2, color=colors[i])
        
        # 设置标签和样式
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, fontsize=12, fontweight='bold')
        ax.set_ylim(0, 5)
        
        # 设置网格样式
        ax.grid(True, alpha=0.3, linewidth=0.8)
        ax.set_facecolor('#FAFAFA')
        
        # 设置标题和图例
        ax.set_title('Multi-Agent System Capability Radar Chart', size=18, y=1.08, 
                    fontweight='bold', color='#2C3E50')
        
        # 使用英文标签创建图例
        system_labels = self._get_system_labels()
        legend_labels = []
        for i, system in enumerate(systems):
            if i < len(system_labels):
                legend_labels.append(system_labels[i])
            else:
                legend_labels.append(f'System {i+1}')
        
        ax.legend(legend_labels, loc='upper right', bbox_to_anchor=(1.4, 1.0), 
                 fontsize=12, frameon=True, fancybox=True, shadow=True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"📊 雷达图已保存到: {save_path}")
        
        plt.show()
    
    def plot_heatmap(self, save_path: str = None):
        """绘制热力图 - 学术级版本"""
        if self.df is None:
            print("请先加载结果数据")
            return
        
        # 计算相关性矩阵
        correlation_matrix = self.df[['accuracy', 'completeness', 'explanation_quality', 
                                    'learning_value', 'composite_score', 'response_time']].corr()
        
        # 创建自定义色彩映射
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
        n_bins = 100
        cmap = LinearSegmentedColormap.from_list("custom_diverging", colors, N=n_bins)
        
        fig, ax = plt.subplots(figsize=(12, 10))
        fig.patch.set_facecolor('white')
        
        # 创建热力图
        sns.heatmap(correlation_matrix, 
                   annot=True, 
                   cmap=cmap, 
                   center=0,
                   square=True, 
                   linewidths=1.5, 
                   cbar_kws={"shrink": .8, "aspect": 30},
                   annot_kws={"size": 11, "fontweight": "bold"},
                   fmt='.3f')
        
        # 设置标题和标签
        ax.set_title('Metrics Correlation Heatmap', fontsize=18, fontweight='bold', pad=20, color='#2C3E50')
        
        # 美化标签
        label_mapping = {
            'accuracy': 'Accuracy',
            'completeness': 'Completeness', 
            'explanation_quality': 'Explanation\nQuality',
            'learning_value': 'Learning\nValue',
            'composite_score': 'Composite\nScore',
            'response_time': 'Response\nTime'
        }
        
        ax.set_xticklabels([label_mapping.get(label.get_text(), label.get_text()) 
                           for label in ax.get_xticklabels()], 
                          rotation=45, ha='right', fontsize=11)
        ax.set_yticklabels([label_mapping.get(label.get_text(), label.get_text()) 
                           for label in ax.get_yticklabels()], 
                          rotation=0, fontsize=11)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"📊 热力图已保存到: {save_path}")
        
        plt.show()
    
    def plot_performance_trends(self, save_path: str = None):
        """绘制性能趋势图 - 新增功能"""
        if self.df is None:
            print("请先加载结果数据")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
        fig.suptitle('Performance Trends and Efficiency Analysis', fontsize=18, fontweight='bold', y=0.95)
        fig.patch.set_facecolor('white')
        
        # 左侧：效率散点图（质量 vs 时间）
        ax1.set_facecolor('#FAFAFA')
        
        for i, system in enumerate(self.df['system'].unique()):
            system_data = self.df[self.df['system'] == system]
            ax1.scatter(system_data['response_time'], system_data['composite_score'],
                       c=ACADEMIC_COLORS['primary'][i], alpha=0.7, s=60, 
                       label=self._get_system_labels()[i] if i < len(self._get_system_labels()) else system, 
                       edgecolors='#2C3E50', linewidth=1)
        
        ax1.set_xlabel('Response Time (seconds)', fontsize=12)
        ax1.set_ylabel('Composite Score', fontsize=12)
        ax1.set_title('Efficiency Analysis: Quality vs Speed', fontsize=14, fontweight='bold', pad=15)
        ax1.legend(fontsize=11, frameon=True, fancybox=True, shadow=True)
        ax1.grid(True, alpha=0.3, linewidth=0.8)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        # 右侧：性能分布直方图
        ax2.set_facecolor('#FAFAFA')
        
        for i, system in enumerate(self.df['system'].unique()):
            system_data = self.df[self.df['system'] == system]
            ax2.hist(system_data['composite_score'], bins=15, alpha=0.6, 
                    color=ACADEMIC_COLORS['primary'][i], 
                    label=self._get_system_labels()[i] if i < len(self._get_system_labels()) else system, 
                    edgecolor='#2C3E50', linewidth=1)
        
        ax2.set_xlabel('Composite Score', fontsize=12)
        ax2.set_ylabel('Frequency', fontsize=12)
        ax2.set_title('Performance Distribution', fontsize=14, fontweight='bold', pad=15)
        ax2.legend(fontsize=11, frameon=True, fancybox=True, shadow=True)
        ax2.grid(True, alpha=0.3, linewidth=0.8)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"📊 性能趋势图已保存到: {save_path}")
        
        plt.show()
    
    def generate_summary_report(self):
        """生成学术级摘要报告"""
        if self.df is None:
            print("请先加载结果数据")
            return
        
        print("="*100)
        print("📊 ACADEMIC EXPERIMENT SUMMARY REPORT")
        print("="*100)
        
        # 系统性能排名
        print("\n🏆 SYSTEM PERFORMANCE RANKING:")
        system_performance = self.df.groupby('system').agg({
            'composite_score': ['mean', 'std'],
            'response_time': ['mean', 'std']
        }).round(3)
        
        # 计算排名
        mean_scores = self.df.groupby('system')['composite_score'].mean()
        rankings = mean_scores.rank(ascending=False)
        
        for system in mean_scores.index:
            rank = int(rankings[system])
            mean_score = system_performance.loc[system, ('composite_score', 'mean')]
            std_score = system_performance.loc[system, ('composite_score', 'std')]
            mean_time = system_performance.loc[system, ('response_time', 'mean')]
            std_time = system_performance.loc[system, ('response_time', 'std')]
            
            print(f"  {rank}. {system}:")
            print(f"     Composite Score: {mean_score:.3f} ± {std_score:.3f}")
            print(f"     Response Time: {mean_time:.3f} ± {std_time:.3f}s")
        
        # 各指标最佳系统
        print("\n⭐ TOP PERFORMERS BY METRIC:")
        metrics = ['accuracy', 'completeness', 'explanation_quality', 'learning_value']
        metric_names = ['Accuracy', 'Completeness', 'Explanation Quality', 'Learning Value']
        
        for metric, name in zip(metrics, metric_names):
            best_system = self.df.groupby('system')[metric].mean().idxmax()
            best_score = self.df.groupby('system')[metric].mean().max()
            print(f"  {name}: {best_system} ({best_score:.3f})")
        
        # 统计显著性分析
        print("\n🔍 STATISTICAL SIGNIFICANCE ANALYSIS:")
        if 'statistics' in self.results:
            stats = self.results['statistics']
            comparisons = stats.get('comparisons', {})
            
            for comparison, result in comparisons.items():
                effect_size = result.get('effect_size', '')
                if effect_size in ['medium', 'large']:
                    print(f"  {comparison}: {effect_size.upper()} effect size")
                    print(f"     Cohen's d: {result.get('cohens_d', 0):.3f}")
                    print(f"     p-value: {result.get('p_value', 0):.3f}")
        
        # 实验规模信息
        print("\n📈 EXPERIMENT SCALE:")
        print(f"  Total Queries: {len(self.df)}")
        print(f"  Systems Tested: {len(self.df['system'].unique())}")
        print(f"  Metrics Evaluated: 4 (Accuracy, Completeness, Explanation Quality, Learning Value)")
        
        print("\n" + "="*100)
    
    def create_all_visualizations(self, output_dir: str = "results"):
        """创建所有学术级可视化图表"""
        if self.df is None:
            print("请先加载结果数据")
            return
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print("🎨 开始生成学术级可视化图表...")
        
        # 生成各种图表
        self.plot_quality_comparison(save_path=output_path / "01_quality_comparison.png")
        self.plot_composite_score_comparison(save_path=output_path / "02_composite_score.png")
        self.plot_response_time_analysis(save_path=output_path / "03_response_time.png")
        self.plot_radar_chart(save_path=output_path / "04_radar_chart.png")
        self.plot_heatmap(save_path=output_path / "05_correlation_heatmap.png")
        self.plot_performance_trends(save_path=output_path / "06_performance_trends.png")
        
        print(f"✅ 所有学术级图表已保存到: {output_path}")
        
        # 生成摘要报告
        self.generate_summary_report()
        
        # 生成LaTeX表格
        self._generate_latex_tables(output_path)
    
    def _generate_latex_tables(self, output_path: Path):
        """生成LaTeX格式的表格"""
        if self.df is None:
            return
        
        # 性能汇总表
        performance_summary = self.df.groupby('system').agg({
            'composite_score': ['mean', 'std'],
            'response_time': ['mean', 'std'],
            'accuracy': 'mean',
            'completeness': 'mean',
            'explanation_quality': 'mean',
            'learning_value': 'mean'
        }).round(3)
        
        latex_table = r"""
\begin{table}[htbp]
\centering
\caption{Multi-Agent System Performance Summary}
\label{tab:performance_summary}
\begin{tabular}{lcccccc}
\toprule
System & Composite Score & Response Time & Accuracy & Completeness & Explanation Quality & Learning Value \\
& (Mean ± Std) & (Mean ± Std) & (Mean) & (Mean) & (Mean) & (Mean) \\
\midrule
"""
        
        for system in performance_summary.index:
            composite_mean = performance_summary.loc[system, ('composite_score', 'mean')]
            composite_std = performance_summary.loc[system, ('composite_score', 'std')]
            time_mean = performance_summary.loc[system, ('response_time', 'mean')]
            time_std = performance_summary.loc[system, ('response_time', 'std')]
            accuracy = performance_summary.loc[system, ('accuracy', 'mean')]
            completeness = performance_summary.loc[system, ('completeness', 'mean')]
            explanation = performance_summary.loc[system, ('explanation_quality', 'mean')]
            learning = performance_summary.loc[system, ('learning_value', 'mean')]
            
            latex_table += f"{system} & {composite_mean:.3f} ± {composite_std:.3f} & {time_mean:.3f} ± {time_std:.3f} & {accuracy:.3f} & {completeness:.3f} & {explanation:.3f} & {learning:.3f} \\\\\n"
        
        latex_table += r"""
\bottomrule
\end{tabular}
\end{table}
"""
        
        # 保存LaTeX表格
        with open(output_path / "performance_table.tex", 'w', encoding='utf-8') as f:
            f.write(latex_table)
        
        print(f"📋 LaTeX表格已保存到: {output_path / 'performance_table.tex'}")


if __name__ == "__main__":
    # 查找最新的结果文件
    results_dir = Path(__file__).parent / "results"
    if results_dir.exists():
        json_files = list(results_dir.glob("experiment_results_*.json"))
        if json_files:
            latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
            print(f"🔍 找到最新结果文件: {latest_file.name}")
            
            # 创建学术级可视化器
            visualizer = AcademicExperimentVisualizer(str(latest_file))
            
            # 生成所有学术级可视化图表
            visualizer.create_all_visualizations()
        else:
            print("❌ 未找到实验结果文件，请先运行实验")
    else:
        print("❌ 结果目录不存在，请先运行实验")
