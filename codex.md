你是资深 Python 后端/DevOps 工程师。请帮我从零创建一个“公开电视直播源聚合器”项目，目标是生成可供 APTV / IPTV 播放器订阅的 playlist.m3u 和 epg.xml。

项目名称：
open-tv-aggregator

核心目标：
1. 聚合合法、公开、可访问的电视直播源。
2. 支持 YouTube Live、官方 HLS/m3u8、iptv-org、Free-TV/IPTV 等公开源。
3. 自动检测频道可用性。
4. 自动生成 APTV 可直接订阅的 M3U。
5. 自动生成基础 EPG XMLTV。
6. 支持 GitHub Actions 定时更新。
7. 支持 Docker 本地运行。
8. 不采集、不破解、不绕过 DRM、不提供盗版源。

技术要求：
- 使用 Python 3.12。
- 尽量少依赖，优先标准库。
- 允许使用 requests、PyYAML。
- YouTube Live 解析使用 yt-dlp 命令行，不直接依赖其 Python API。
- 项目结构清晰，方便后期扩展。
- 输出文件放在 dist/ 目录。
- 配置文件放在 config/ 目录。
- 源码放在 src/ 目录。
- 所有脚本必须可直接运行。
- README 要写清楚如何本地运行、Docker 运行、GitHub Actions 部署、APTV 导入。

频道范围：
优先支持以下分类：
- Taiwan：台湾公开频道、官方 YouTube Live、TaiwanPlus、公视等
- News：Bloomberg、DW、France 24、NHK World、CNA、Arirang 等
- Tech：NASA TV、ESA、科技类公开直播
- Asia：日本、韩国、香港、新加坡等公开直播
- Global：国际公开 HLS 频道

请不要写死一堆失效源。请设计成配置驱动。

配置文件示例：
config/channels.yml

每个频道字段包括：
- id
- name
- group
- country
- logo
- source_type: hls | youtube | m3u
- url
- epg_id
- enabled

示例：
- id: taiwanplus
  name: TaiwanPlus
  group: Taiwan
  country: TW
  logo: https://example.com/logo.png
  source_type: hls
  url: https://example.com/live.m3u8
  epg_id: taiwanplus.tw
  enabled: true

- id: tvbs-news-youtube
  name: TVBS News Live
  group: Taiwan
  country: TW
  logo: https://example.com/tvbs.png
  source_type: youtube
  url: https://www.youtube.com/@TVBSNEWS01/live
  epg_id: tvbs-news.tw
  enabled: true

功能模块要求：
1. config_loader.py
   - 读取 YAML 配置
   - 校验字段
   - 过滤 enabled=false 的频道

2. resolver.py
   - 根据 source_type 解析真实播放地址
   - hls：直接返回原始 URL
   - youtube：调用 yt-dlp -g 获取真实 HLS 地址
   - m3u：预留接口，后期可解析远程 m3u
   - 解析失败时记录错误，不中断整个任务

3. validator.py
   - 对解析出的播放地址做可用性检测
   - 使用 HTTP HEAD，失败时尝试 GET Range
   - 超时时间可配置
   - 返回 online/offline 状态

4. playlist.py
   - 生成标准 M3U
   - 支持 tvg-id、tvg-name、tvg-logo、group-title
   - 输出 dist/playlist.m3u

5. epg.py
   - 生成基础 XMLTV
   - 如果没有真实节目单，就生成占位节目，例如 “Live Programming”
   - 输出 dist/epg.xml

6. report.py
   - 生成 dist/report.json
   - 包含频道总数、成功数、失败数、失败原因、更新时间

7. main.py
   - 串联完整流程：
     读取配置 → 解析源 → 校验 → 生成 M3U → 生成 EPG → 生成报告

8. cli.py
   - 支持命令：
     python -m src.cli build
     python -m src.cli validate
     python -m src.cli list

GitHub Actions：
创建 .github/workflows/update.yml
要求：
- 每 6 小时运行一次
- 支持手动 workflow_dispatch
- 安装 Python 3.12
- 安装 yt-dlp
- 运行构建脚本
- 将 dist/ 输出提交回仓库
- 生成 GitHub Pages 可访问路径说明

Docker：
创建 Dockerfile 和 docker-compose.yml
要求：
- 基于 python:3.12-slim
- 安装 yt-dlp
- 默认执行 python -m src.cli build
- dist 挂载为 volume

README 要包含：
1. 项目介绍
2. 合法性说明
3. 本地运行方式
4. Docker 运行方式
5. GitHub Actions 自动更新方式
6. GitHub Pages 发布方式
7. APTV 导入方式：
   - playlist.m3u 地址
   - epg.xml 地址
8. 如何新增频道
9. 常见问题：
   - YouTube 地址为什么会失效
   - 为什么部分台湾商业频道没有稳定源
   - 为什么不支持 DRM 平台
   - 为什么某些源在中国大陆无法播放

请直接生成完整项目代码，包括：
- requirements.txt
- README.md
- Dockerfile
- docker-compose.yml
- .gitignore
- config/channels.yml
- src/ 下所有 Python 文件
- .github/workflows/update.yml

代码质量要求：
- 函数有类型标注
- 有基础异常处理
- 日志清晰
- 不要把失败频道写入 playlist.m3u，除非配置 allow_offline=true
- report.json 中保留失败详情
- 所有输出文件必须 UTF-8
- M3U 兼容 APTV

请一次性完成整个项目，不要只给片段。