import requests
import time
import urllib.parse
from ..utils import logger
from typing import List, Dict, Any

class BoardRelated:
    """相关画板图片操作类(同步版本)"""

    def __init__(self, client):
        """
        初始化相关画板图片操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    def get_pics_urls(self, board_id: str) -> List[str]:
        pics_data = self.get_pics_data(board_id)
        return [pic['url'] for pic in pics_data]

    def get_pics_data(self, board_id: str) -> List[Dict[str, Any]]:
        pics_data_origin = self.get_pics_data_origin(board_id)
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

    def get_pics_data_origin(self, board_id: str) -> List[Dict[str, Any]]:
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
            i_len = len(images)
            logger.info(f"获取相关图片 [ {i_len} / ? ]")

            try:
                batch, bookmark = self._fetch_batch(options)
                images.extend(batch)
            except Exception as e:
                # 显示错误堆栈
                import traceback
                traceback.print_exc()
                logger.error(f"获取数据失败: {e}")
                break

        i_len = len(images)
        logger.success(f"找到 {i_len} 张相关图片{'s' if i_len > 1 else ''}")
        return images

    def _build_options(self, board_id: str, bookmark: str = None) -> Dict[str, Any]:
        """构建请求参数"""
        options = {
            "isPrefetch": 'false',
            "type": "board",
            "id": board_id,
            "page_size": 25,
        }
        if bookmark:
            options.update({'bookmarks': [bookmark]})

        return options

    def _fetch_batch(self, options: Dict[str, Any]) -> tuple:
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
                r = self.client.session.get(
                    'https://www.pinterest.com/_ngjs/resource/BoardContentRecommendationResource/get/',
                    params=post_d,
                    timeout=60
                )
                data = r.json()
                batch = data['resource_response']['data']
                bookmark = data['resource']['options']['bookmarks'][0]
                return batch, bookmark

            except (requests.Timeout, requests.ConnectionError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                time.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"获取相关图片失败: board_id={options['id']}")