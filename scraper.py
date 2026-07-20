import json
import os
import feedparser
from datetime import datetime, timedelta, timezone

# 配置抓取数据源 (可按需添加/替换 RSS 链接)
SOURCES = [
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "AWS Machine Learning", "url": "https://aws.amazon.com/blogs/machine-learning/feed/"}
]

DATA_FILE = "data.json"

def get_cutoff_date():
    """获取 15 天前的时间节点，用于过滤历史数据"""
    return datetime.now(timezone.utc) - timedelta(days=15)

def fetch_latest_news():
    """抓取最新动态"""
    news_items = []
    cutoff = get_cutoff_date()
    
    for source in SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries:
                # 尝试解析发布时间 (转换为 UTC datetime)
                try:
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    continue # 无法解析时间的条目直接跳过
                
                # 仅保留在 15 天窗口期内的新闻
                if pub_date >= cutoff:
                    news_items.append({
                        "id": entry.link, # 使用链接作为唯一去重 ID
                        "title": entry.title,
                        "link": entry.link,
                        "source": source["name"],
                        "date": pub_date.strftime("%Y-%m-%d"),
                        "timestamp": pub_date.isoformat()
                    })
        except Exception as e:
            print(f"Error fetching {source['name']}: {e}")
            
    return news_items

def merge_and_filter(new_data):
    """合并新老数据，执行 15 天滚动窗口截断"""
    existing_data = []
    
    # 1. 加载现有 data.json (如果存在)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                pass
    
    # 2. 合并数据，使用字典根据 ID (link) 去重
    merged_dict = {item["id"]: item for item in existing_data}
    for item in new_data:
        merged_dict[item["id"]] = item
        
    # 3. 剔除超过 15 天的历史数据
    cutoff = get_cutoff_date()
    final_data = []
    for item in merged_dict.values():
        try:
            item_date = datetime.fromisoformat(item["timestamp"])
            if item_date >= cutoff:
                final_data.append(item)
        except Exception:
            pass
            
    # 4. 按时间倒序排序 (最新的在最前)
    final_data.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # 5. 覆写回 data.json
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print(f"Update completed. Saved {len(final_data)} items within the 15-day window.")

if __name__ == "__main__":
    latest_news = fetch_latest_news()
    merge_and_filter(latest_news)
