from ..utils import logger
from typing import Dict, Any
import json
from bs4 import BeautifulSoup
import time

class PicData:
    """图片数据操作类(同步版本)"""

    def __init__(self, client):
        """
        初始化图片数据操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    def get_origin(self, pin_id: str) -> Dict[str, Any]:
        """
        获取图片详细数据

        参数:
            pin_id: 图片ID
        返回:
            图片详细数据
        """
        try:
            r = self.client.session.get(
                f"https://www.pinterest.com/pin/{pin_id}/",
                timeout=60
            )

            # 解析HTML获取数据
            soup = BeautifulSoup(r.text, "html.parser")

            # 查找包含数据的script标签
            for script in soup.find_all("script"):
                if script.get("data-relay-response") == "true":
                    data = json.loads(script.string)
                    pin_data = data["response"]["data"]["v3GetPinQuery"]["data"]
                    return pin_data

            raise Exception("Pin data not found")

        except Exception as e:
            logger.error(f"获取图片数据失败: {e}")
            raise Exception(f"获取图片数据失败: pin_id={pin_id}")

    def get(self, pin_id: str) -> Dict[str, Any]:
        """
        获取图片详细数据
        """
        p = self.get_origin(pin_id)
        data = {
            'id': p['entityId'],
            'url': p.get('imageSpec_orig', {}).get('url', ''),
            'width': p.get('imageSpec_orig', {}).get('width', 0),
            'height': p.get('imageSpec_orig', {}).get('height', 0),
            'link': p.get('link', ''),
            'created_at': int(time.mktime(time.strptime(p.get('createdAt', ''), '%a, %d %b %Y %H:%M:%S %z'))) if p.get('createdAt') else 0,
            'join': p.get('pinJoin', {}).get('visualAnnotation', ''),
            'dominant_color': p.get('dominantColor', ''),
            'count': {
                'reaction': p.get('totalReactionCount', 0),
                'save': p.get('aggregatedPinData', {}).get('aggregatedStats', {}).get('saves', 0),
                'share': p.get('shareCount', 0),
                'favorite': p.get('favoriteUserCount', 0),
                'repin': p.get('repinCount', 0),
            },
            'text': {
                'alttext': p.get('altText', ''),
                'autoalttext': p.get('autoAltText', ''),
                'description': p.get('description', ''),
                'closeup_description': p.get('closeupDescription', ''),
                'title': p.get('title', ''),
                'grid_title': p.get('gridTitle', ''),
            },
            'category': p.get('category', []),
        }
        return data