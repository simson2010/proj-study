---
name: chatglm-image
description: 使用 ChatGLM/智谱AI 的图像生成能力（文生图/图生图）来产出高质量图片。适用于需要把自然语言需求转为可用提示词、参数，并输出可直接调用接口的请求示例与落地流程。
---

# ChatGLM 图像生成

## 使用说明

- **环境变量设置**：首先确保已设置 API Token 环境变量 `CHATGLM_API_TOKEN` 或 `GLM_API_TOKEN`，如果没有设置，需要提示用户设置并给出设置方法。
- **提示词优化**：将用户需求改写为清晰、具体的提示词，包含主体、场景、构图、风格等关键要素。
- **参数配置**：使用 cogView-4 模型，支持参数包括：
  - `prompt`：图片生成提示词（必需）
  - `output_dir`：输出文件夹路径（默认 "output"）
  - `size`：图片尺寸（默认 "1024x1024"），可选 "1024x1024"、"512x512" 等
  - `quality`：图片质量（默认 "standard"）
- **调用方式**：使用命令行方式调用 `generate_image.py` 脚本，格式为：
  ```bash
  python generate_image.py <prompt> [output_dir] [size] [quality]
  ```
- **输出结果**：生成的图片将保存到指定文件夹，文件名包含时间戳和提示词。
- **错误处理**：如果 API Token 未设置或调用失败，给出明确的错误提示和解决方案。

## 输出规范

- 默认输出以下小节（保持简洁）：
  - **需求复述**
  - **正向提示词（中文/英文各一版，优先英文以提高可控性）**
  - **负向提示词**
  - **推荐参数**
  - **调用示例（伪代码或 curl）**
  - **迭代建议（3 条以内）**
- 若用户要求限制字数：遵守用户限制；否则正文尽量控制在 999 个字符以内（标点也计入）。

## 提示词模板

**正向提示词（英文模板）**

- `Subject, action/pose, environment, composition (close-up/wide shot/centered), lighting, color palette, style, material, ultra-detailed, high quality`

**负向提示词（英文模板）**

- `lowres, blurry, watermark, text, logo, jpeg artifacts, bad anatomy, extra fingers, deformed hands, duplicate, cropped, worst quality`

## 示例

### 示例 1：基本使用

生成一张可爱的小猫咪图片：

```bash
python generate_image.py "一只可爱的小猫咪，坐在阳光明媚的窗台上，背景是蓝天白云"
```

输出：图片将保存到默认的 `output` 文件夹中，文件名格式为 `{timestamp}_{prompt}.png`

### 示例 2：指定输出目录和尺寸

生成竖版海报图片并保存到指定目录：

```bash
python generate_image.py "赛博朋克风格的城市夜景，霓虹灯闪烁，雨夜街道" output 1024x1024 standard
```

参数说明：
- `prompt`：图片生成提示词（必需）
- `output`：输出文件夹路径（可选，默认 "output"）
- `1024x1024`：图片尺寸（可选，默认 "1024x1024"）
- `standard`：图片质量（可选，默认 "standard"）

### 示例 3：完整调用示例

```bash
# 设置环境变量（首次使用需要）
export CHATGLM_API_TOKEN='your_token_here'

# 生成图片
python generate_image.py "极简风格的香水产品图，白色背景，柔和灯光" ./images 1024x1024 standard
```

**注意事项**：
- 确保已安装 `requests` 库：`pip install requests`
- API Token 可以从 https://open.bigmodel.cn 获取
- 如果未设置环境变量，脚本会提示设置方法


