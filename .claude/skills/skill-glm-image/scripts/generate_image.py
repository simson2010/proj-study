#!/usr/bin/env python3
"""
使用 ChatGLM API 生成图片的脚本
根据用户提示词生成指定大小的图片并保存到指定文件夹
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse


def get_api_token() -> Optional[str]:
    """从环境变量获取 API Token"""
    token = os.getenv('CHATGLM_API_TOKEN') or os.getenv('GLM_API_TOKEN')
    return token


def print_token_setup_instructions():
    """打印设置环境变量的说明"""
    print("错误: 未找到 API Token 环境变量")
    print("\n请设置环境变量:")
    print("  Linux/macOS:")
    print("    export CHATGLM_API_TOKEN='your_token_here'")
    print("    # 或")
    print("    export GLM_API_TOKEN='your_token_here'")
    print("\n  Windows (CMD):")
    print("    set CHATGLM_API_TOKEN=your_token_here")
    print("    # 或")
    print("    set GLM_API_TOKEN=your_token_here")
    print("\n  Windows (PowerShell):")
    print("    $env:CHATGLM_API_TOKEN='your_token_here'")
    print("    # 或")
    print("    $env:GLM_API_TOKEN='your_token_here'")
    print("\n提示: 请访问 https://open.bigmodel.cn 获取您的 API Token")


def generate_image(
    prompt: str,
    output_dir: str = "output",
    size: str = "1024x1024",
    quality: str = "standard",
    model: str = "cogView-4"
) -> Optional[str]:
    """
    调用 ChatGLM API 生成图片
    
    Args:
        prompt: 图片生成提示词
        output_dir: 输出文件夹路径
        size: 图片尺寸，默认 1024x1024
        quality: 图片质量，默认 standard
        model: 模型名称，默认 cogView-4
    
    Returns:
        保存的图片文件路径，失败返回 None
    """
    # 获取 API Token
    token = get_api_token()
    if not token:
        print_token_setup_instructions()
        return None
    
    # API 端点
    url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
    
    # 请求头
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 请求体
    data = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality
    }
    
    try:
        # 发送 POST 请求
        print(f"正在生成图片: {prompt[:50]}...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        # 检查响应格式
        if 'data' not in result or not result['data']:
            print(f"错误: API 响应格式异常: {result}")
            return None
        
        # 获取图片 URL
        image_url = result['data'][0].get('url')
        if not image_url:
            print(f"错误: 响应中未找到图片 URL: {result}")
            return None
        
        print(f"图片生成成功，URL: {image_url}")
        
        # 下载图片
        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名（基于提示词和时间戳）
        import time
        timestamp = int(time.time())
        safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_prompt = safe_prompt.replace(' ', '_')
        filename = f"{timestamp}_{safe_prompt}.png"
        filepath = output_path / filename
        
        # 保存图片
        with open(filepath, 'wb') as f:
            f.write(image_response.content)
        
        print(f"图片已保存至: {filepath}")
        return str(filepath)
        
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"错误详情: {error_detail}")
            except:
                print(f"响应内容: {e.response.text}")
        return None
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python generate_image.py <prompt> [output_dir] [size] [quality]")
        print("示例: python generate_image.py '一只可爱的小猫咪' output 1024x1024 standard")
        sys.exit(1)
    
    prompt = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    size = sys.argv[3] if len(sys.argv) > 3 else "1024x1024"
    quality = sys.argv[4] if len(sys.argv) > 4 else "standard"
    
    result = generate_image(prompt, output_dir, size, quality)
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
