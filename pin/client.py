import httpx
from http.cookies import SimpleCookie
from fake_useragent import UserAgent
from .config import VER
from .utils import logger
from .subclass.board import Board
from .subclass.account_boards import AccountBoards
from .subclass.board_related import BoardRelated
from .subclass.pic_related import PicRelated
from .subclass.pic_data import PicData
from .subclass.search_boards import SearchBoards
from .subclass.search_pics import SearchPics


class PinterestClient:
    """Pinterest API客户端(同步版本)"""

    # 添加默认cookie
    DEFAULT_COOKIE = (
        'csrftoken=cc9c00da139f6a9a2a80fbeebac45ae4; '
        '_pinterest_sess=TWc9PSZQeWg4b2IvMElPZGxsUTNYMUE4dXBGbDdXUXJnWE1CY01XZVVmL21UdktMQ0Fyd2VHSFJ2dThUYXBNVXRUNk50aDlxTmNRamg1a0lCVmFYLyt0eGVoY2UzOGxZTjRDTDh3b1RNOThrUlVzbz0mak9lQ3B3MXNRbmh5UndzSlRkMVk4dzNPL1Y4PQ==; '
        '_auth=0; '
        '_routing_id="150e1f53-1c2d-4722-b357-2eb240576717"; '
        'sessionFunnelEventLogged=1'
    )

    def __init__(self, ver_i=2, proxies=None, cookie_file=None, cookie_str=None):
        """
        初始化Pinterest客户端

        参数:
            ver_i: API版本索引
            proxies: 代理设置
            cookie_file: cookie文件路径
            cookie_str: cookie字符串
        """
        self.ver_i = ver_i
        self.proxies = proxies
        self.cookie_file = cookie_file
        self.cookie_str = cookie_str
        self.ua = UserAgent()
        self.session = None
        self.pic_data = PicData(self)  # 初始化图片数据操作实例
        self.pic_related = PicRelated(self)  # 初始化相关图片操作实例
        self.board = Board(self)  # 初始化画板操作实例
        self.board_related = BoardRelated(self)  # 初始化相关画板操作实例
        self.account_boards = AccountBoards(self)  # 初始化账号画板操作实例
        self.search_boards = SearchBoards(self)  # 初始化画板搜索操作实例
        self.search_pics = SearchPics(self)  # 初始化图片搜索操作实例
        self.connect()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self.session:
            self.session.close()

    def connect(self):
        """建立连接"""
        # 处理cookie
        cookies = None

        # 优先使用cookie文件
        if self.cookie_file:
            try:
                with open(self.cookie_file) as f:
                    rawdata = f.read()
                my_cookie = SimpleCookie()
                my_cookie.load(rawdata)
                cookies = {key: morsel.value for key, morsel in my_cookie.items()}
            except Exception as e:
                logger.warning(f"读取cookie文件失败: {e}")

        # 其次使用cookie字符串
        elif self.cookie_str:
            my_cookie = SimpleCookie()
            my_cookie.load(self.cookie_str)
            cookies = {key: morsel.value for key, morsel in my_cookie.items()}

        # 最后使用默认cookie
        else:
            my_cookie = SimpleCookie()
            my_cookie.load(self.DEFAULT_COOKIE)
            cookies = {key: morsel.value for key, morsel in my_cookie.items()}

        # 设置headers
        headers = {
            'User-Agent': self.ua.chrome,
            'Accept': 'application/json, text/javascript, */*, q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.pinterest.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'X-APP-VERSION': VER[self.ver_i] if self.ver_i in (1, 2) else None,
            'X-Pinterest-AppState': 'active',
            'X-Pinterest-PWS-Handler': 'www/[username]/[slug]/[section_slug].js',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'Trailers'
        }

        # 创建会话
        self.session = httpx.Client(
            headers=headers,
            cookies=cookies,
            proxies=self.proxies if self.proxies else None,
            follow_redirects=True
        )