import httpx
import time
import urllib.parse
import asyncio
from ..utils import logger

class Board:
    """画板操作类"""

    def __init__(self, client):
        """
        初始化画板操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get(self, board_id, uname=None, board_slug=None, section_slug=None):
        """
        获取画板内容

        参数:
            board_id: 画板ID
            uname: 用户名
            board_slug: 画板slug
            section_slug: 分区slug
        """
        board = {
            'board': {
                'id': board_id,
            },
            'section': None
        }
        if uname and board_slug:
            shortform = '/'.join([uname, board_slug, section_slug]) if section_slug else '/'.join([uname, board_slug])
        else:
            shortform = None
        bookmark = None
        images = []

        while bookmark != '-end-':
            options = self._build_options(board, section_slug, bookmark)

            # 显示进度
            i_len = len(images) - 1 if len(images) > 0 else 0
            logger.debug(f"获取所有图片 [ {i_len} / ? ]")

            # 发送请求获取数据
            try:
                batch, bookmark = await self._fetch_batch(options, shortform)
                images.extend(batch)
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        i_len = len(images)
        logger.success(f"找到 {i_len} 张图片{'s' if i_len > 1 else ''}")
        return images

    def _build_options(self, board, section_slug, bookmark=None):
        """构建请求参数"""
        options = {
            'isPrefetch': 'false',
            'board_id': board['board']['id'],
            'field_set_key': 'react_grid_pin',
            'filter_section_pins': 'true',
            'layout': 'default',
            'page_size': 25,
            'redux_normalize_feed': 'true',
        }

        if section_slug:
            options.update({'section_id': board['section']['id']})
        if bookmark:
            options.update({'bookmarks': [bookmark]})

        return options

    async def _fetch_batch(self, options, shortform=None):
        """获取一批数据"""
        post_d = urllib.parse.urlencode({
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        for t in (15, 30, 40, 50, 60):
            try:
                r = await self.client.client.get(
                    'https://www.pinterest.com/resource/BoardFeedResource/get/',
                    params=post_d
                )
                data = r.json()
                batch = data['resource_response']['data']
                bookmark = data['resource']['options']['bookmarks'][0]
                return batch, bookmark

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                await asyncio.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"获取此板块/分区失败: {shortform}")