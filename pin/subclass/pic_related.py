import requests
import time
from ..utils import logger
from typing import List, Dict, Any
import urllib.parse

class PicRelated:
    """相关图片操作类(同步版本)"""

    def __init__(self, client):
        """
        初始化相关图片操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    @staticmethod
    def help():
        print("""
        PicRelated 类提供以下方法:

        get_pics_urls(pin_id: str, page_size: int = 25) -> List[str]:
        获取相关图片的URL列表

        get_pics_data(pin_id: str, page_size: int = 25) -> List[Dict[str, Any]]:
        获取相关图片的数据

        get_pics_data_origin(pin_id: str, page_size: int = 25) -> List[Dict[str, Any]]:
        获取相关图片的原始数据
        """)

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

    def get_pics_data_origin(self, pin_id: str, page_size: int = 25) -> List[Dict[str, Any]]:
        """
        获取相关图片

        参数:
            pin_id: 图片ID
            page_size: 每页数量，默认25，最大50
        返回:
            相关图片列表
        """
        if not pin_id:
            raise ValueError("无效的图片ID")
        if page_size < 1:
            raise ValueError("每页数量必须大于0")
        if page_size > 50:
            raise ValueError("每页数量不能超过50")

        bookmark = None
        images = []

        while True:
            # 显示进度
            i_len = len(images)
            logger.debug(f"获取相关图片 [ {i_len} / ? ]")

            try:
                batch, bookmark = self._fetch_batch(pin_id, bookmark, page_size)
                images.extend(batch)

                # 如果没有下一页，退出循环
                if bookmark == "-end-" or bookmark == '%22-end-%22':
                    break
            except Exception as e:
                # 打印错误栈
                import traceback
                traceback.print_exc()
                logger.error(f"获取数据失败: {e}")
                break

        i_len = len(images)
        logger.success(f"找到 {i_len} 张相关图片{'s' if i_len > 1 else ''}")
        return images

    def _build_options(self, pin_id: str, bookmark: str = None, page_size: int = 25) -> Dict[str, Any]:
        """构建请求参数"""
        options = {
            "pin_id": pin_id,
            "context_pin_ids": [],
            "page_size": page_size,
            "search_query": "",
            "source": "deep_linking",
            "top_level_source": "deep_linking",
            "top_level_source_depth": 1,
            "is_pdp": "false"
        }

        if bookmark:
            options["bookmarks"] = [bookmark]

        return options

    def _fetch_batch(self, pin_id: str, bookmark: str = None, page_size: int = 25) -> tuple:
        """获取一批数据"""
        options = self._build_options(pin_id, bookmark, page_size)
        source_url = f"/pin/{pin_id}/"

        post_d = urllib.parse.urlencode({
            'source_url': source_url,
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        for t in (15, 30, 40, 50, 60):
            try:
                r = self.client.session.get(
                    'https://www.pinterest.com/resource/RelatedModulesResource/get/',
                    params=post_d,
                    timeout=60
                )
                data = r.json()
                # 提取数据
                batch = data['resource_response']['data']
                bookmark = data['resource']['options'].get('bookmarks', ['-end-'])[0]

                return batch, bookmark

            except (requests.Timeout, requests.ConnectionError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                time.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"获取相关图片失败: pin_id={pin_id}")