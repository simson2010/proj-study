# Chat GLM 生成图像API开发文档

## 使用说明 
按文档内容开发使用ChatGLM LLM API的文生图模型，按用户的Promt生成指定大小的图片，并存到指定文件夹。

### 开发说明 
 
3.0
 - 按以下Shell脚本开发调用API生成图片，API Token要从环境变量获取，如果没有，需要提示用户设置环境变量，并给出设置环境变量的方式。
 - 该生图模型使用 cogview-4 
 - 从响应的JSON中获取图片URL，下载到本地并存储到指定文件夹中

3.1 请求
```sh 
curl --request POST \
  --url https://open.bigmodel.cn/api/paas/v4/images/generations \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '
{
  "model": "cogView-4",
  "prompt": "一只可爱的小猫咪，坐在阳光明媚的窗台上，背景是蓝天白云.",
  "size": "1024x1024",
  "quality": "standard"
}
'
```

3.2 响应
```JSON
{
  "created": 123,
  "data": [
    {
      "url": "<string>"
    }
  ],
  "content_filter": [
    {
      "role": "assistant",
      "level": 1
    }
  ]
}
```