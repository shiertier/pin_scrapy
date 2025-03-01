import httpx
import time
import urllib.parse
from ..utils import logger
from typing import List, Dict, Any

class SearchPics:
    """图片搜索操作类(同步版本)"""

    def __init__(self, client):
        """
        初始化图片搜索操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    def get_pics_urls(self, pin_id: str, page_size: int = 25) -> List[str]:
        pics_data = self.get_pics_data(pin_id, page_size)
        return [pic['url'] for pic in pics_data]

    def get_pics_data(self, pin_id: str, page_size: int = 25) -> List[Dict[str, Any]]:
        pics_data_origin = self.get_pics_data_origin(pin_id, page_size)
        pics_data = []
        for pic in pics_data_origin:
            pics_data.append({
                'id': pic['id'],
                'url': pic.get('images', {}).get('orig', {}).get('url', ''),
                'width': pic.get('images', {}).get('orig', {}).get('width', 0),
                'height': pic.get('images', {}).get('orig', {}).get('height', 0),
                'created_at': int(time.mktime(time.strptime(pic.get('created_at', ''), '%a, %d %b %Y %H:%M:%S %z'))) if pic.get('created_at') else 0,
                'dominant_color': pic.get('dominant_color', ''),
                'count': {
                    'save': pic.get('aggregate_metadata', {}).get('aggregated_stats', {}).get('saves', 0),
                    'repin': pic.get('repin_count', 0),
                },
                'text': {
                    'title': pic.get('title', ''),
                    'auto_alt_text': pic.get('auto_alt_text', ''),
                }
            })
        return pics_data

    def get_pics_data_origin(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索图片

        参数:
            query: 搜索关键词
        返回:
            图片列表
        """
        bookmark = None
        images = []

        while True:
            # 显示进度
            i_len = len(images)
            logger.debug(f"获取搜索结果 [ {i_len} / ? ]")

            try:
                batch, bookmark = self._fetch_batch(query, bookmark)
                images.extend(batch)

                # 如果没有下一页，退出循环
                if bookmark == "-end-" or bookmark == '%22-end-%22':
                    break
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        i_len = len(images)
        logger.success(f"找到 {i_len} 张图片{'s' if i_len > 1 else ''}")
        return images

    def _build_options(self, query: str, bookmark: str = None) -> Dict[str, Any]:
        """构建请求参数"""
        options = {
            'applied_unified_filters': 'null',
            'appliedProductFilters': "---",
            # 'article': 'null',
            'auto_correction_disabled': 'false',
            'corpus': 'null',
            'customized_rerank_type': 'null',
            'domains': 'null',
            'dynamicPageSizeExpGroup': 'null',
            'filters': 'null',
            'journey_depth': 'null',
            'page_size': 25,
            'price_max': 'null',
            'price_min': 'null',
            'query_pin_sigs': 'null',
            'query': query,
            'redux_normalize_feed': 'true',
            'request_params': 'null',
            'rs': "content_type_filter",
            'scope': "pins",
            'selected_one_bar_modules': 'null',
            'seoDrawerEnabled': 'false',
            'source_id': 'null',
            'source_module_id': 'null',
            'source_url': f"/search/pins/?q={urllib.parse.quote(query)}&rs=typed",
            'top_pin_id': 'null',
            'top_pin_ids': 'null'
        }

        if bookmark:
            options['bookmarks'] = [bookmark]

        return options

    def _fetch_batch(self, query: str, bookmark: str = None) -> tuple:
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
                r = self.client.session.get(
                    'https://www.pinterest.com/resource/BaseSearchResource/get/',
                    params=post_d,
                    timeout=60
                )
                data = r.json()
                # 修正数据提取路径
                batch = data['resource_response']['data']['results']
                bookmark = data['resource_response'].get('bookmark', '-end-')  # 使用get避免KeyError

                # 如果没有bookmark，说明是最后一页
                if not bookmark:
                    bookmark = '-end-'

                return batch, bookmark

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                time.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"搜索图片失败: query={query}")