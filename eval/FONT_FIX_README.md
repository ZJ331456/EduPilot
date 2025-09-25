# 中文字体显示问题解决方案

## 🚨 问题描述

在生成的可视化图表中，中文字符显示为"0000"或乱码，这表明matplotlib无法正确渲染中文字符。

## 🔍 问题原因

1. **字体配置问题**：matplotlib默认字体不支持中文字符
2. **系统字体缺失**：系统中没有安装合适的中文字体
3. **字体路径问题**：matplotlib找不到字体文件

## 🛠️ 解决方案

### 方案1：自动字体检测（推荐）

我们已经实现了自动字体检测功能，系统会自动：

1. 检测操作系统类型
2. 查找可用的中文字体
3. 自动配置合适的字体
4. 如果中文失败，回退到英文标签

### 方案2：手动安装字体

#### Windows系统
```bash
# 确保以下字体已安装
- Microsoft YaHei (微软雅黑)
- SimHei (黑体)
- SimSun (宋体)
- KaiTi (楷体)
- FangSong (仿宋)
```

#### macOS系统
```bash
# 确保以下字体已安装
- PingFang SC (苹方)
- Hiragino Sans GB (冬青黑体)
- STHeiti (华文黑体)
- Arial Unicode MS
```

#### Linux系统
```bash
# 安装中文字体包
sudo apt-get install fonts-wqy-microhei fonts-wqy-zenhei  # Ubuntu/Debian
sudo yum install wqy-microhei-fonts wqy-zenhei-fonts      # CentOS/RHEL
```

### 方案3：使用英文标签

如果中文字体问题无法解决，系统会自动使用英文标签：

- `基础配置` → `Basic Config`
- `标准配置` → `Standard Config`
- `增强配置` → `Enhanced Config`
- `专家配置` → `Expert Config`

## 🧪 测试字体修复

运行以下命令测试字体配置：

```bash
python test_font_fix.py
```

这将：
1. 检测系统字体
2. 创建测试图表
3. 验证中文字符显示

## 📊 图表标签说明

### 修复前的问题
- X轴标签显示为"0000"
- 图例标签无法显示
- 中文标题可能显示异常

### 修复后的效果
- X轴标签正确显示系统名称
- 图例标签清晰可读
- 支持中英文双语显示

## 🔧 技术实现

### 字体检测逻辑
```python
def _get_system_labels(self):
    """获取系统标签的英文映射"""
    systems = self.df['system'].unique()
    system_labels = []
    
    for sys in systems:
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
```

### 字体配置
```python
# 根据操作系统选择合适的字体
if platform.system() == 'Windows':
    chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']
elif platform.system() == 'Darwin':  # macOS
    chinese_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Arial Unicode MS']
else:  # Linux
    chinese_fonts = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC']
```

## 📁 相关文件

- `visualization.py` - 主要的可视化模块（已修复）
- `test_font_fix.py` - 字体测试脚本
- `FONT_FIX_README.md` - 本说明文件

## 🎯 使用建议

1. **首次使用**：运行 `test_font_fix.py` 检查字体配置
2. **生成图表**：运行 `visualization.py` 生成修复后的图表
3. **检查结果**：查看生成的PNG文件，确认标签显示正常
4. **如果仍有问题**：检查系统字体安装情况

## 🚀 预期效果

修复后的图表应该：
- ✅ 正确显示系统名称（中文或英文）
- ✅ 图例标签清晰可读
- ✅ 支持中英文双语显示
- ✅ 符合学术论文标准
- ✅ 300 DPI高分辨率输出

## 📞 故障排除

如果问题仍然存在：

1. **检查字体安装**：确认系统中安装了中文字体
2. **重启Python环境**：重新启动Jupyter或Python解释器
3. **清除matplotlib缓存**：删除matplotlib的字体缓存文件
4. **使用英文标签**：系统会自动回退到英文标签

## 🎉 总结

通过以上修复，可视化图表现在应该能够：
- 自动检测和使用合适的中文字体
- 正确显示中文系统名称
- 在字体不可用时自动回退到英文标签
- 生成符合顶级论文要求的学术级图表
