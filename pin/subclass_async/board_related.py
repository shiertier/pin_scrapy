import httpx
import time
import urllib.parse
import asyncio
from ..utils import logger
from typing import List, Dict, Any

class BoardRelated:
    """相关画板图片操作类"""

    def __init__(self, client):
        """
        初始化相关画板图片操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get(self, board_id: str) -> List[Dict[str, Any]]:
        """
        获取相关画板的图片

        参数:
            board_id: 画板ID
        返回:
            图片列表
        """
        bookmark = None
        images = []

        while bookmark != '-end-':
            options = self._build_options(board_id, bookmark)

            # 显示进度
            i_len = len(images) - 1 if len(images) > 0 else 0
            logger.debug(f"获取相关图片 [ {i_len} / ? ]")

            try:
                batch, bookmark = await self._fetch_batch(options)
                images.extend(batch)
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        i_len = len(images)
        logger.success(f"找到 {i_len} 张相关图片{'s' if i_len > 1 else ''}")
        return images

    def _build_options(self, board_id: str, bookmark: str = None) -> Dict[str, Any]:
        """构建请求参数"""
        # options = {
        #     'isPrefetch': 'false',
        #     'board_id': board_id,
        #     'field_set_key': 'react_grid_pin',  # 与Board类保持一致
        #     'page_size': 25,
        #     'redux_normalize_feed': 'true',
        # }
        options = {
            "add_vase": 'true',
            'id': board_id,
            'type': 'board',
            "__track__referrer": 20,
        }
        if bookmark:
            options.update({'bookmarks': [bookmark]})

        return options

    async def _fetch_batch(self, options: Dict[str, Any]) -> tuple:
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
                    'https://www.pinterest.com/resource/BoardContentRecommendationResource/get',
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
                    raise Exception(f"获取相关图片失败: board_id={options['board_id']}")
