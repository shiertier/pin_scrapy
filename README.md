# Pinterest Scrapy

这是一个Pinterest Scrapy实现，目前仅支持同步操作（异步版本正在开发中）。

## 功能特点

该客户端提供以下主要功能：

### 1. 画板(Board)相关操作

- `account_boards`: 获取用户的画板
- `search_boards`: 搜索画板
- `board`: 获取画板内容
- `board_related`: 获取相关画板

### 2. 图片(Pin)相关操作

- `search_pics`: 搜索图片
- `pic_related`: 获取相关图片
- `pic_data`: 获取单个图片的详细信息

## 快速开始

```python
from pin.client import PinterestClient

# 创建客户端实例
client = PinterestClient()

# 搜索图片
pics = client.search_pics.get_pics_data("猫咪")
for pic in pics:
    print(pic['url'])

# 获取用户画板
boards = client.account_boards.get_data("username")
for board in boards:
    print(board['name'])

# 获取单个图片详情
pic_info = client.pic_data.get("pin_id")
```

## 数据返回格式

对于同类型的操作，返回格式保持一致：

### 画板数据格式
```python
{
    'id': '画板ID',
    'name': '画板名称',
    'url': '画板URL',
    'follower_count': '关注者数量',
    'pin_count': '图片数量'
}
```

### 图片数据格式
```python
{
    'id': '图片ID',
    'title': '标题',
    'repin_count': '转发数',
    'save_count': '保存数',
    'url': '图片URL',
    'width': '宽度',
    'height': '高度',
    'created_at': '创建时间',
    'dominant_color': '主色调'
}
```

## 注意事项

1. 目前仅支持同步操作，异步版本正在开发中
2. 建议使用自己的 Cookie 以获得更好的访问体验
3. 可以通过设置代理来解决访问限制问题

## Cookie 设置

可以通过以下三种方式设置 Cookie：

1. Cookie 文件
```python
client = PinterestClient(cookie_file='path/to/cookie.txt')
```

2. Cookie 字符串
```python
client = PinterestClient(cookie_str='your_cookie_string')
```

3. 默认 Cookie
```python
client = PinterestClient()
```