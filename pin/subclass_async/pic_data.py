from ..utils import logger
from typing import Dict, Any
import json
from bs4 import BeautifulSoup

class PicData:
    """图片数据操作类"""

    def __init__(self, client):
        """
        初始化图片数据操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get(self, pin_id: str) -> Dict[str, Any]:
        """
        获取图片详细数据

        参数:
            pin_id: 图片ID
        返回:
            图片详细数据
        """
        try:
            r = await self.client.client.get(
                f"https://www.pinterest.com/pin/{pin_id}/"
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