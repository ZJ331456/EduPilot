#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字体修复效果
验证中文字符是否能正确显示
"""

import matplotlib.pyplot as plt
import matplotlib
import platform
import matplotlib.font_manager as fm
import numpy as np

def test_font_configuration():
    """测试字体配置"""
    print("🔍 测试字体配置...")
    
    # 根据操作系统选择合适的字体
    if platform.system() == 'Windows':
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
            print(f"✅ 找到字体: {font}")
        except:
            print(f"❌ 未找到字体: {font}")
            continue
    
    if available_fonts:
        matplotlib.rcParams['font.sans-serif'] = available_fonts
        print(f"\n🎯 使用字体: {available_fonts[0]}")
        return True
    else:
        matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
        print("\n⚠️ 未找到合适的中文字体，使用默认字体")
        return False

def create_test_chart():
    """创建测试图表"""
    print("\n🎨 创建测试图表...")
    
    # 创建测试数据
    systems = ['基础配置', '标准配置', '增强配置', '专家配置']
    scores = [4.2, 4.5, 4.8, 4.1]
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 左侧：条形图
    bars = ax1.bar(range(len(systems)), scores, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
    ax1.set_title('系统性能测试 (System Performance Test)', fontsize=16, fontweight='bold')
    ax1.set_ylabel('评分 (Score)', fontsize=12)
    ax1.set_xticks(range(len(systems)))
    
    # 测试中文标签显示
    try:
        ax1.set_xticklabels(systems, rotation=45, ha='right')
        print("✅ 中文标签设置成功")
    except Exception as e:
        print(f"❌ 中文标签设置失败: {e}")
        # 回退到英文标签
        english_labels = ['Basic Config', 'Standard Config', 'Enhanced Config', 'Expert Config']
        ax1.set_xticklabels(english_labels, rotation=45, ha='right')
        print("🔄 使用英文标签作为回退")
    
    # 右侧：散点图
    x = np.random.normal(0, 1, 100)
    y = np.random.normal(0, 1, 100)
    ax2.scatter(x, y, alpha=0.6, color='#2E86AB')
    ax2.set_title('数据分布测试 (Data Distribution Test)', fontsize=16, fontweight='bold')
    ax2.set_xlabel('X轴 (X-axis)', fontsize=12)
    ax2.set_ylabel('Y轴 (Y-axis)', fontsize=12)
    
    plt.tight_layout()
    
    # 保存图表
    test_file = "font_test_chart.png"
    plt.savefig(test_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"💾 测试图表已保存到: {test_file}")
    
    plt.show()
    
    return test_file

def test_visualization_import():
    """测试可视化模块导入"""
    try:
        from visualization import AcademicExperimentVisualizer
        print("✅ 学术级可视化器导入成功")
        
        # 测试创建可视化器
        visualizer = AcademicExperimentVisualizer()
        print("✅ 学术级可视化器创建成功")
        
        # 测试标签映射函数
        test_systems = ['基础配置', '标准配置', '增强配置', '专家配置']
        labels = visualizer._get_system_labels()
        print(f"✅ 标签映射函数测试: {labels}")
        
        return True
    except Exception as e:
        print(f"❌ 可视化器导入失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试字体修复效果...")
    
    # 测试字体配置
    font_ok = test_font_configuration()
    
    # 创建测试图表
    if font_ok:
        test_file = create_test_chart()
        print(f"\n🎉 字体测试完成！请检查 {test_file} 文件")
    else:
        print("\n⚠️ 字体配置有问题，跳过图表创建")
    
    # 测试可视化模块
    print("\n" + "="*50)
    test_visualization_import()
    
    print("\n📋 测试完成！")
    print("如果图表中的中文标签仍然显示为'0000'，请检查系统字体安装情况")
