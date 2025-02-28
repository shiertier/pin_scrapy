import httpx
import time
import urllib.parse
import asyncio
from ..utils import logger
from typing import List, Dict, Any

class SearchBoards:
    """画板搜索操作类"""

    def __init__(self, client):
        """
        初始化画板搜索操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get_all(self, query: str) -> List[str]:
        """
        搜索画板

        参数:
            query: 搜索关键词
        返回:
            画板ID列表
        """
        bookmark = None
        board_ids = set()  # 使用set去重

        while True:
            # 显示进度
            b_len = len(board_ids)
            logger.debug(f"获取搜索结果 [ {b_len} / ? ]")

            try:
                batch, bookmark = await self._fetch_batch(query, bookmark)
                # 提取画板ID并添加到集合中
                for board in batch:
                    board_ids.add(board['id'])

                # 如果没有下一页，退出循环
                if bookmark == "-end-" or bookmark == '%22-end-%22':
                    break
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        b_len = len(board_ids)
        logger.success(f"找到 {b_len} 个画板{'s' if b_len > 1 else ''}")
        return list(board_ids)

    def _build_options(self, query: str, bookmark: str = None) -> Dict[str, Any]:
        """构建请求参数"""
        options = {
            'applied_unified_filters': None,
            'appliedProductFilters': "---",
            'article': None,
            'auto_correction_disabled': False,
            'corpus': None,
            'customized_rerank_type': None,
            'domains': None,
            'dynamicPageSizeExpGroup': "enabled_275",
            'filters': None,
            'journey_depth': None,
            'page_size': None,
            'price_max': None,
            'price_min': None,
            'query_pin_sigs': None,
            'query': query,
            'redux_normalize_feed': True,
            'request_params': None,
            'rs': "content_type_filter",
            'scope': "boards",
            'selected_one_bar_modules': None,
            'seoDrawerEnabled': False,
            'source_id': None,
            'source_module_id': None,
            'source_url': f"/search/boards/?q={urllib.parse.quote(query)}&rs=content_type_filter",
            'top_pin_id': None,
            'top_pin_ids': None
        }

        if bookmark:
            options['bookmarks'] = [bookmark]

        return options

    async def _fetch_batch(self, query: str, bookmark: str = None) -> tuple:
        """获取一批数据"""
        options = self._build_options(query, bookmark)

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
                    'https://www.pinterest.com/resource/BaseSearchResource/get/',
                    params=post_d
                )
                data = r.json()
                batch = data['resource_response']['data']['results']
                bookmark = data['resource']['options']['bookmarks'][0]
                return batch, bookmark

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                await asyncio.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"搜索画板失败: query={query}")
