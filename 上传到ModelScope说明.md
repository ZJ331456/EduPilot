# 将 metadata 数据上传到 ModelScope 数据集

本指南将帮助您将 `metadata` 文件夹中的数据上传到 ModelScope（魔搭社区）的数据集。

## 📋 前置准备

### 1. 安装依赖

```bash
pip install modelscope tqdm
```

### 2. 获取 ModelScope Token

1. 登录 [ModelScope 官网](https://www.modelscope.cn/)
2. 进入个人中心 → 访问令牌
3. 创建新的访问令牌并复制保存

### 3. 创建数据集

在 ModelScope 网站上创建数据集：
1. 登录后进入"我的数据集"
2. 点击"创建数据集"
3. 填写数据集信息（名称、描述等）
4. 记录数据集名称（如 `edu-data`）

## 🚀 使用方法

### 方法一：使用 Git 方式上传（推荐）

Git 方式适合大量文件和大文件上传，支持断点续传。

#### 步骤 1: 扫描文件并生成上传脚本

```bash
python upload_to_modelscope.py \
  --token ms-f149c52c-ae24-4c84-a26e-75a1e5f9e3a8 \
  --dataset edu-data \
  --namespace zerochoe \
  --prepare-git
```

参数说明：
- `--token`: 您的 ModelScope token
- `--dataset`: 数据集名称（在网站上创建的数据集名称）
- `--namespace`: 您的用户名
- `--prepare-git`: 仅生成上传脚本，不实际上传

#### 步骤 2: 执行上传脚本

**Linux/Mac:**
```bash
bash upload_script.sh
```

**Windows:**
```cmd
upload_script.bat
```

脚本会自动：
1. 克隆数据集仓库（如果尚未克隆）
2. 安装并配置 Git LFS（用于大文件）
3. 复制所有文件到仓库
4. 提交并推送到 ModelScope

### 方法二：选择性上传特定文件夹

如果只想上传部分数据，可以使用 `--include-dirs` 参数：

```bash
# 只上传 ChineseBooK 和 shu 文件夹
python upload_to_modelscope.py \
  --token ms-f149c52c-ae24-4c84-a26e-75a1e5f9e3a8 \
  --dataset edu-data \
  --namespace zerochoe \
  --include-dirs ChineseBooK shu \
  --prepare-git
```

### 方法三：排除特定文件夹

```bash
# 排除 ChinaTextbook 文件夹（因为 PDF 文件较大）
python upload_to_modelscope.py \
  --token ms-f149c52c-ae24-4c84-a26e-75a1e5f9e3a8 \
  --dataset edu-data \
  --namespace zerochoe \
  --exclude-dirs ChinaTextbook \
  --prepare-git
```

### 方法四：只上传特定文件类型

```bash
# 只上传 .txt 文件
python upload_to_modelscope.py \
  --token ms-f149c52c-ae24-4c84-a26e-75a1e5f9e3a8 \
  --dataset edu-data \
  --namespace zerochoe \
  --file-types .txt \
  --prepare-git
```

## 📊 脚本功能说明

### 1. 文件扫描

脚本会自动扫描 `metadata` 文件夹，统计：
- 总文件数和总大小
- 按类别分类的文件数量
- 文件类型分布

### 2. 大文件处理

对于超过 50MB 的文件（可通过 `--max-size-mb` 调整），脚本会自动使用 Git LFS 处理。

### 3. 进度保存

上传进度会保存在 `.upload_progress.json` 文件中，支持断点续传。

### 4. 元数据生成

脚本会生成 `dataset_metadata.json` 文件，包含：
- 数据集基本信息
- 文件列表和统计信息
- 类别和文件类型分布

## 🔧 高级配置

### 自定义最大文件大小阈值

```bash
python upload_to_modelscope.py \
  --max-size-mb 100 \
  --prepare-git
```

### 查看所有参数

```bash
python upload_to_modelscope.py --help
```

## ⚠️ 注意事项

1. **大文件处理**: PDF 文件通常较大，建议使用 Git LFS。确保已安装 Git LFS：
   ```bash
   # Windows: 下载安装 https://git-lfs.github.com/
   # Linux: sudo apt-get install git-lfs
   # Mac: brew install git-lfs
   ```

2. **网络稳定性**: 上传大量文件时，建议在网络稳定的环境下进行。

3. **存储空间**: 确保 ModelScope 账户有足够的存储空间。

4. **文件编码**: 确保文本文件使用 UTF-8 编码。

5. **权限问题**: 确保您有该数据集的写入权限。

## 📝 示例工作流

### 完整上传流程

```bash
# 1. 扫描所有文件并查看统计
python upload_to_modelscope.py \
  --token YOUR_TOKEN \
  --dataset edu-data \
  --namespace YOUR_USERNAME

# 2. 生成 Git 上传脚本（只上传文本文件）
python upload_to_modelscope.py \
  --token YOUR_TOKEN \
  --dataset edu-data \
  --namespace YOUR_USERNAME \
  --file-types .txt \
  --prepare-git

# 3. 执行上传脚本
bash upload_script.sh  # Linux/Mac
# 或
upload_script.bat      # Windows

# 4. 验证上传
# 在 ModelScope 网站上查看数据集，确认文件已成功上传
```

### 分批次上传

如果数据量很大，可以分批次上传：

```bash
# 第一批：只上传 ChineseBooK
python upload_to_modelscope.py \
  --token YOUR_TOKEN \
  --dataset edu-data \
  --namespace YOUR_USERNAME \
  --include-dirs ChineseBooK \
  --prepare-git

# 执行上传后，再上传第二批
python upload_to_modelscope.py \
  --token YOUR_TOKEN \
  --dataset edu-data \
  --namespace YOUR_USERNAME \
  --include-dirs shu \
  --prepare-git
```

## 🐛 常见问题

### Q1: Git LFS 上传失败

**解决方案**:
1. 确保已安装 Git LFS
2. 检查网络连接
3. 尝试单独上传大文件

### Q2: 权限错误

**解决方案**:
1. 检查 token 是否有效
2. 确认您有数据集的写入权限
3. 重新生成 token

### Q3: 文件编码问题

**解决方案**:
脚本会自动处理 UTF-8 编码的文件。如果遇到编码错误，请先转换文件编码。

### Q4: 上传中断

**解决方案**:
脚本支持断点续传。重新运行脚本时会自动跳过已上传的文件。

## 📚 相关资源

- [ModelScope 官方文档](https://modelscope.cn/docs)
- [Git LFS 文档](https://git-lfs.github.com/)
- [ModelScope 数据集创建指南](https://modelscope.cn/docs)

## 💡 提示

- 首次上传建议先测试一个小文件夹，确认流程无误后再上传全部数据
- 上传前可以先查看生成的 `dataset_metadata.json` 了解数据集结构
- 对于超大数据集，考虑使用 ModelScope 的批量上传工具

