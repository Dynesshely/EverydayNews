from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import List, Optional
import os
import requests
import pandas as pd
import json

# 枚举类型定义
class HotTagType(str, Enum):
    """热搜标签类型"""
    NEW = "1"      # 新
    HOT = "3"      # 热
    NORMAL = "0"   # 普通

@dataclass
class HotItem:
    """热搜条目数据类"""
    title: str           # word字段
    order: Optional[int] = None  # index字段
    hot_tag: Optional[str] = None  # hotTag字段
    url: Optional[str] = None
    is_top: bool = False  # isTop字段
    img: Optional[str] = None  # 注意：新JSON中没有img字段
    desc: Optional[str] = None  # 注意：新JSON中没有desc字段
    new_hot_name: Optional[str] = None  # newHotName字段
    
    @property
    def tag_type(self) -> HotTagType:
        """获取标签类型枚举"""
        if self.hot_tag == HotTagType.NEW:
            return HotTagType.NEW
        elif self.hot_tag == HotTagType.HOT:
            return HotTagType.HOT
        else:
            return HotTagType.NORMAL
    
    @property
    def is_new(self) -> bool:
        """是否是新的热搜"""
        return self.hot_tag == HotTagType.NEW
    
    @property
    def is_hot(self) -> bool:
        """是否是热的热搜"""
        return self.hot_tag == HotTagType.HOT
    
    @classmethod
    def from_json(cls, json_data: dict) -> 'HotItem':
        """从JSON数据创建HotItem实例"""
        return cls(
            title=json_data.get('word', ''),
            order=json_data.get('index'),
            hot_tag=json_data.get('hotTag'),
            url=json_data.get('url'),
            is_top=json_data.get('isTop', False),
            new_hot_name=json_data.get('newHotName')
            # 注意：新JSON中没有img和desc字段
        )

@dataclass
class HotSearchBoard:
    """热搜榜单数据类"""
    items: List[HotItem] = field(default_factory=list)
    board_title: str = "热搜榜"
    log_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        """初始化后处理"""
        # 按order排序
        self.items.sort(key=lambda x: x.order if x.order is not None else float('inf'))
    
    def add_item(self, item: HotItem):
        """添加热搜条目"""
        self.items.append(item)
        # 重新排序
        self.items.sort(key=lambda x: x.order if x.order is not None else float('inf'))
    
    def get_top_items(self, count: int = 10) -> List[HotItem]:
        """获取前N条热搜"""
        return self.items[:count]
    
    def get_items_by_tag(self, tag: HotTagType) -> List[HotItem]:
        """按标签类型获取热搜"""
        return [item for item in self.items if item.hot_tag == tag.value]
    
    def get_item_by_title(self, title: str) -> Optional[HotItem]:
        """根据标题查找热搜"""
        for item in self.items:
            if item.title == title:
                return item
        return None
    
    @classmethod
    def from_api_response(cls, json_data: dict) -> 'HotSearchBoard':
        """从API响应创建HotSearchBoard实例"""
        items = []
        
        # 解析新的JSON结构
        cards = json_data.get('data', {}).get('cards', [])
        
        for card in cards:
            if card.get('component') == 'tabTextList':
                content_blocks = card.get('content', [])
                for block in content_blocks:
                    content_items = block.get('content', [])
                    for item_data in content_items:
                        items.append(HotItem.from_json(item_data))
        
        # 获取board标题
        board_title = json_data.get('data', {}).get('currentBoard', {}).get('text', '热搜榜')
        
        # 获取log_id
        log_id = json_data.get('data', {}).get('logid')
        
        return cls(
            items=items,
            board_title=board_title,
            log_id=log_id
        )
    
    def to_dataframe(self) -> pd.DataFrame:
        """转换为DataFrame"""
        data = []
        for item in self.items:
            data.append({
                '热搜排名': item.order or 0,
                '热搜标题': item.title,
                '标签': item.new_hot_name or '',
                '是否置顶': '是' if item.is_top else '否',
                '链接地址': item.url or '',
                '热度类型': item.tag_type.name
            })
        
        return pd.DataFrame(data)
    
    def save_to_files(self, base_path: str = '../../News/CN/'):
        """保存到CSV和HTML文件"""
        # 获取北京时间
        beijing_time = self.timestamp + timedelta(hours=8)
        year = beijing_time.strftime('%Y')
        month_day = beijing_time.strftime('%m%d')
        minute = beijing_time.hour * 60 + beijing_time.minute
        
        # 创建目录路径
        path = os.path.join(base_path, year, month_day)
        os.makedirs(path, exist_ok=True)
        
        # 转换为DataFrame
        df = self.to_dataframe()
        
        # 保存文件
        csv_filename = f'百度{self.board_title}.{minute}.csv'
        html_filename = f'百度{self.board_title}.{minute}.html'
        
        csv_path = os.path.join(path, csv_filename)
        html_path = os.path.join(path, html_filename)
        
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        df.to_html(html_path, index=False, classes='table table-striped')
        
        print(f"数据已保存到:")
        print(f"CSV文件: {csv_path}")
        print(f"HTML文件: {html_path}")
        
        return csv_path, html_path

class BaiduHotSearchAPI:
    """百度热搜API客户端"""
    
    BASE_URL = 'https://top.baidu.com/api/board?platform=wise&tab=realtime'
    
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Mobile Safari/537.36',
        'Host': 'top.baidu.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
    }
    
    def __init__(self, tab: str = 'realtime'):
        """
        初始化API客户端
        
        Args:
            tab: 榜单类型，可选值: realtime(热搜榜), novel(小说榜), movie(电影榜)等
        """
        self.tab = tab
    
    def fetch_hot_search(self) -> HotSearchBoard:
        """获取热搜榜单"""
        url = f'https://top.baidu.com/api/board?platform=wise&tab={self.tab}'
        
        try:
            response = requests.get(url, headers=self.DEFAULT_HEADERS, timeout=10)
            response.raise_for_status()
            
            json_data = response.json()
            
            if json_data.get('success', False):
                return HotSearchBoard.from_api_response(json_data)
            else:
                raise ValueError(f"API请求失败: {json_data.get('error', {}).get('message', '未知错误')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析失败: {e}")

# 使用示例
def main():
    """主函数示例"""
    try:
        # 创建API客户端
        api = BaiduHotSearchAPI(tab='realtime')
        
        # 获取热搜数据
        print("正在获取百度热搜榜...")
        board = api.fetch_hot_search()
        
        print(f"榜单标题: {board.board_title}")
        print(f"条目数量: {len(board.items)}")
        print(f"Log ID: {board.log_id}")
        
        # 显示前10条热搜
        print("\n=== 热搜TOP 10 ===")
        for i, item in enumerate(board.get_top_items(10), 1):
            tag_str = f"[{item.new_hot_name}]" if item.new_hot_name else ""
            top_str = "[置顶]" if item.is_top else ""
            print(f"{i:2d}. {item.order:2d}位 {tag_str}{top_str}{item.title}")
        
        # 统计不同类型的热搜
        print("\n=== 热搜类型统计 ===")
        hot_items = board.get_items_by_tag(HotTagType.HOT)
        new_items = board.get_items_by_tag(HotTagType.NEW)
        normal_items = board.get_items_by_tag(HotTagType.NORMAL)
        
        print(f"热门热搜: {len(hot_items)} 条")
        print(f"新上热搜: {len(new_items)} 条")
        print(f"普通热搜: {len(normal_items)} 条")
        
        # 查找特定热搜
        print("\n=== 查找示例 ===")
        search_title = "白银涨到可怕 有人一觉醒来赚18万"
        found_item = board.get_item_by_title(search_title)
        if found_item:
            print(f"找到热搜: {found_item.title}")
            print(f"排名: {found_item.order}位")
            print(f"标签: {found_item.new_hot_name}")
        else:
            print(f"未找到标题为 '{search_title}' 的热搜")
        
        # 保存到文件
        print("\n=== 保存数据 ===")
        board.save_to_files()
        
        # 导出为DataFrame
        print("\n=== DataFrame示例 ===")
        df = board.to_dataframe()
        print(f"DataFrame形状: {df.shape}")
        print(df.head())
        
    except Exception as e:
        print(f"程序执行出错: {e}")

if __name__ == "__main__":
    main()
