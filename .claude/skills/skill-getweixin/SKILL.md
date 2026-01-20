---
name: GetWeixin
description: 访问微信公众号文章（mp.weixin.qq.com），获取完整HTML并提取文章内容。使用特定的User-Agent以确保能获取到完整页面。
---

# GetWeixin - 微信公众号文章内容提取

## 使用说明

- **功能**：访问微信公众号文章链接，获取完整HTML内容，然后提取文章的标题、发布时间、作者、正文内容等关键信息。
- **User-Agent设置**：使用 Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0 作为请求头，以确保能获取到完整的页面内容。
- **依赖库**：需要安装 requests 和 BeautifulSoup4 库。
- **调用方式**：使用命令行方式调用 `get_weixin.py` 脚本，格式为：
  ```bash
  python get_weixin.py <url>
  ```

## 输出规范

默认输出以下信息（保持简洁）：
- **文章标题**
- **发布时间**
- **作者**
- **公众号名称**
- **文章正文**（纯文本，去除HTML标签和换行符）

## 使用示例

### 示例 1：基本使用
```bash
python get_weixin.py "https://mp.weixin.qq.com/s/xxxxxx"
```

输出：
```
标题：微信公众号文章标题
发布时间：2024-01-21
作者：作者名称
公众号：公众号名称
正文：文章的完整内容...
```

### 示例 2：保存到文件
```bash
python get_weixin.py "https://mp.weixin.qq.com/s/xxxxxx" > article.txt
```

### 示例 3：安装依赖库
```bash
pip install requests beautifulsoup4
```

## 注意事项
- 确保网络连接正常
- 微信公众号文章链接必须是有效的 mp.weixin.qq.com 链接
- 有些文章可能需要登录才能访问，此时脚本可能会失败
- 脚本会自动处理常见的微信公众号文章格式，但不保证能处理所有特殊格式
