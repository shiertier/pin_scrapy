import httpx
import time
import urllib.parse
import asyncio
from ..utils import logger
from typing import List, Dict, Any

class AccountBoards:
    """账号画板操作类"""

    def __init__(self, client):
        """
        初始化账号画板操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get_all(self, username: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有画板

        参数:
            username: 用户名
        返回:
            画板列表
        """
        bookmark = None
        boards = []

        while bookmark != '-end-':
            options = self._build_options(username, bookmark)

            # 显示进度
            b_len = len(boards) - 1 if len(boards) > 0 else 0
            logger.debug(f"获取所有板块 [ {b_len} / ? ]")

            try:
                batch, bookmark = await self._fetch_batch(options, username)
                boards.extend(batch)
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        b_len = len(boards)
        logger.success(f"找到 {b_len} 个板块{'s' if b_len > 1 else ''}")
        return boards

    def _build_options(self, username: str, bookmark: str = None) -> Dict[str, Any]:
        """构建请求参数"""
        options = {
            'isPrefetch': 'false',
            'privacy_filter': 'all',
            'sort': 'alphabetical',
            'field_set_key': 'profile_grid_item',
            'username': username,
            'page_size': 25,
            'group_by': 'visibility',
            'include_archived': 'true',
            'redux_normalize_feed': 'true',
        }

        if bookmark:
            options.update({'bookmarks': [bookmark]})

        return options

    async def _fetch_batch(self, options: Dict[str, Any], username: str) -> tuple:
        """获取一批数据"""
        post_d = urllib.parse.urlencode({
            'source_url': username,
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        for t in (15, 30, 40, 50, 60):
            try:
                r = await self.client.client.get(
                    'https://www.pinterest.com/resource/BoardsResource/get/',
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
                    raise Exception(f"获取此用户名失败: {username}")
