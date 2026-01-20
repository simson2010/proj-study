#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GetWeixin - 微信公众号文章内容提取工具
使用特定的 User-Agent 访问微信公众号文章，获取完整 HTML 并提取内容
"""

import requests
from bs4 import BeautifulSoup
import argparse
import sys


def get_weixin_article(url):
    """
    访问微信公众号文章并提取内容
    """
    # 定义请求头，使用指定的 User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    try:
        # 发送请求
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"请求失败，状态码：{response.status_code}")
            return None

        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取文章信息
        article = {}

        # 标题
        title_tag = soup.find('h1', class_='rich_media_title')
        if title_tag:
            article['title'] = title_tag.get_text(strip=True)
        else:
            article['title'] = '未找到标题'

        # 发布时间
        time_tag = soup.find('em', id='publish_time')
        if time_tag:
            article['publish_time'] = time_tag.get_text(strip=True)
        else:
            article['publish_time'] = '未找到发布时间'

        # 作者
        author_tag = soup.find('a', id='js_name')
        if author_tag:
            article['author'] = author_tag.get_text(strip=True)
        else:
            # 备用方法：查找作者信息
            author_tag = soup.find('span', class_='rich_media_meta rich_media_meta_text')
            if author_tag:
                article['author'] = author_tag.get_text(strip=True)
            else:
                article['author'] = '未找到作者'

        # 公众号名称
        wxname_tag = soup.find('a', class_='profile_nickname')
        if wxname_tag:
            article['wxname'] = wxname_tag.get_text(strip=True)
        else:
            article['wxname'] = '未找到公众号名称'

        # 正文内容
        content_tag = soup.find('div', class_='rich_media_content')
        if content_tag:
            # 提取纯文本内容，去除 HTML 标签
            content = content_tag.get_text(strip=True)
            # 处理换行和多余空格
            article['content'] = ' '.join(content.split())
        else:
            article['content'] = '未找到正文内容'

        return article

    except Exception as e:
        print(f"获取文章内容失败：{str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(description='微信公众号文章内容提取工具')
    parser.add_argument('url', help='微信公众号文章链接')

    args = parser.parse_args()

    # 获取文章内容
    article = get_weixin_article(args.url)

    if article:
        # 输出结果
        print(f"标题：{article['title']}")
        print(f"发布时间：{article['publish_time']}")
        print(f"作者：{article['author']}")
        print(f"公众号：{article['wxname']}")
        print(f"正文：{article['content']}")


if __name__ == '__main__':
    main()
