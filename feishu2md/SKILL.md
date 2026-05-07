---
name: feishu2md
description: 飞书文档导出工具，支持将飞书/larksuite 文档、文件夹或知识库下载为 Markdown 文件。当用户需要下载飞书文档、导出飞书文档为 Markdown、批量下载飞书文件夹内容、或导出飞书知识库时使用此 skill。触发词包括："下载飞书文档"、"导出为 Markdown"、"飞书文档转 Markdown"、"批量下载飞书文件夹"、"导出知识库"等。
---

# feishu2md - 飞书文档导出 Skill

将飞书文档、文件夹或知识库下载为 Markdown 文件的工具。

## 工具位置

可执行文件位于：`scripts/feishu2md.exe`

## 使用场景

此 skill 应在以下情况下使用：
- 用户提供了飞书文档链接，要求下载或导出
- 用户要求将飞书文档转换为 Markdown 格式
- 用户需要批量下载飞书文件夹中的多个文档
- 用户需要导出整个飞书知识库

## 使用方法

### 1. 下载单个文档

使用以下命令下载单个飞书文档：

```bash
& "C:\Users\Administrator\.workbuddy\skills\feishu2md\scripts\feishu2md.exe" dl "<飞书文档URL>"
```

示例：
```bash
& "C:\Users\Administrator\.workbuddy\skills\feishu2md\scripts\feishu2md.exe" dl "https://domain.feishu.cn/docx/docxtoken"
```

### 2. 批量下载文件夹

使用 `--batch` 参数批量下载文件夹内的所有文档：

```bash
& "C:\Users\Administrator\.workbuddy\skills\feishu2md\scripts\feishu2md.exe" dl --batch -o <输出目录> "<文件夹URL>"
```

示例：
```bash
& "C:\Users\Administrator\.workbuddy\skills\feishu2md\scripts\feishu2md.exe" dl --batch -o output_directory "https://domain.feishu.cn/drive/folder/foldertoken"
```

### 3. 导出知识库

使用 `--wiki` 参数导出整个知识库：

```bash
& "C:\Users\Administrator\.workbuddy\skills\feishu2md\scripts\feishu2md.exe" dl --wiki -o <输出目录> "<知识库设置URL>"
```

示例：
```bash
& "C:\Users\Administrator\.workbuddy\skills\feishu2md\scripts\feishu2md.exe" dl --wiki -o output_directory "https://domain.feishu.cn/wiki/settings/123456789101112"
```

## 获取飞书文档链接

指导用户按以下步骤获取文档链接：
1. 打开飞书文档
2. 点击"分享"按钮
3. 开启"链接分享"
4. 选择"互联网上获得链接的人可阅读"
5. 复制链接

## 配置说明

工具已配置完成，无需额外配置。如需查看配置状态，可运行：

```bash
& "C:\Users\Administrator\.workbuddy\skills\feishu2md\scripts\feishu2md.exe" config
```

## 注意事项

- 确保提供的 URL 是有效的飞书分享链接
- 批量下载时，建议指定输出目录 `-o` 参数
- 导出知识库需要使用知识库设置页面的 URL，而非普通的访问 URL
- 工具会自动将文档转换为 Markdown 格式，并保留图片等资源

## 命令参数说明

- `dl` 或 `download`: 下载命令
- `--output` 或 `-o`: 指定输出目录（默认为当前目录）
- `--batch`: 批量下载文件夹下所有文档
- `--wiki`: 下载整个知识库
- `--dump`: 转储 API 的 JSON 响应（调试用）
