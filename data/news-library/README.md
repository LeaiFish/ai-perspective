# 按首次收录日查新闻

从 2026 年 11 月 11 日起，每条新闻按 `first_seen_at` 换算成北京时间，写入 `年份/YYYY-MM-DD.jsonl`。每天一个文件，每行一条，保留新闻 ID、标题、已有中文标题、来源、原文链接、原文发布时间和专题。原文发布时间可能为空。采集窗口和原文发表日均可与收录日不同。

云端每轮更新滚动库后，追加尚未归档的 ID。达到 35 天、旧条目退出滚动库或同一 ID 再次出现时，历史日文件继续保留。每条记录可以命中多个专题，按收录时的[专题配置](../../config/topics.json)匹配；未命中也保留。11 月 11–18 日的首批数据由该期间已提交的 59 份采集快照核对，计 8,831 个不同 ID，截至 18 日北京时间 11:26。当天此后的新增继续写入同一文件。

在仓库根目录用 Python 3 离线查询：

```bash
python3 scripts/news_library.py find --date 2026-11-11
python3 scripts/news_library.py find --topic 'Personal Agent' --start 2026-11-11 --end 2026-11-18
python3 scripts/news_library.py find --topic product-entry --count
python3 scripts/news_library.py find --topic 未分类 --date 2026-11-11 --count
python3 scripts/news_library.py find --list-topics
```

输出依次为北京时间收录日、标题、来源和原文链接。GitHub 上可直接按[年份](2026/)打开某天的文件。同步到本机后可搜索整个历史区间；漏过数天也可通过快进仓库一次补回。
