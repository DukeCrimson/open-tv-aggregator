# open-tv-aggregator

公开电视直播源聚合器，用于生成 APTV / IPTV 播放器可订阅的 `playlist.m3u` 和基础 XMLTV `epg.xml`。

本项目只聚合合法、公开、可访问的官方直播源。它不采集付费平台、不破解、不绕过 DRM、不提供盗版源。YouTube Live 会通过 `yt-dlp` 命令行解析临时播放地址；官方 HLS/m3u8 可直接配置。

## 功能

- 配置驱动：频道写在 `config/channels.yml`
- 支持 `hls`、`youtube`，并预留 `m3u` 扩展接口
- 支持为个别 HLS 源配置 `user_agent`、`referrer`
- 自动解析 YouTube Live 临时 HLS 地址
- 自动检测频道可用性
- 仅把在线频道写入 `dist/playlist.m3u`
- 生成占位 XMLTV：`dist/epg.xml`
- 生成构建报告：`dist/report.json`
- 支持 Docker 和 GitHub Actions 定时更新

## 本地运行

需要 Python 3.12。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.cli build
```

输出文件：

- `dist/playlist.m3u`
- `dist/epg.xml`
- `dist/report.json`

常用命令：

```bash
python -m src.cli list
python -m src.cli list --include-disabled
python -m src.cli validate
python -m src.cli build --timeout 20
```

## Docker 运行

```bash
docker compose up --build
```

`dist/` 会挂载到本地目录，方便直接拿到生成文件。

也可以直接使用 Docker：

```bash
docker build -t open-tv-aggregator .
docker run --rm -v "$PWD/dist:/app/dist" -v "$PWD/config:/app/config:ro" open-tv-aggregator
```

## GitHub Actions 自动更新

工作流文件位于 `.github/workflows/update.yml`：

- 每 6 小时运行一次
- 支持手动 `workflow_dispatch`
- 使用 Python 3.12
- 安装 `yt-dlp`
- 执行 `python -m src.cli build`
- 将 `dist/playlist.m3u`、`dist/epg.xml`、`dist/report.json` 提交回仓库

仓库需要允许 GitHub Actions 写入：

1. 进入仓库 `Settings`
2. 打开 `Actions` -> `General`
3. 在 `Workflow permissions` 选择 `Read and write permissions`

## GitHub Pages 发布

推荐使用 GitHub Pages 直接发布主分支：

1. 进入仓库 `Settings` -> `Pages`
2. `Build and deployment` 选择 `Deploy from a branch`
3. Branch 选择 `main`，目录选择 `/root`

发布后文件地址通常是：

```text
https://<your-user>.github.io/open-tv-aggregator/dist/playlist.m3u
https://<your-user>.github.io/open-tv-aggregator/dist/epg.xml
```

如果仓库名不是 `open-tv-aggregator`，把 URL 中的路径替换成你的仓库名。

## APTV 导入

在 APTV 中新增 IPTV 订阅：

- Playlist URL：`https://<your-user>.github.io/open-tv-aggregator/dist/playlist.m3u`
- EPG URL：`https://<your-user>.github.io/open-tv-aggregator/dist/epg.xml`

也可以在本地测试时直接导入生成后的 `dist/playlist.m3u`。

## 新增频道

编辑 `config/channels.yml`：

```yaml
- id: taiwanplus
  name: TaiwanPlus
  group: Taiwan
  country: TW
  logo: https://example.com/logo.png
  source_type: hls
  url: https://example.com/live.m3u8
  epg_id: taiwanplus.tw
  enabled: true
```

字段说明：

- `id`：项目内唯一 ID
- `name`：播放器显示名称
- `group`：频道分组，例如 `Taiwan`、`News`、`Tech`
- `country`：国家或地区代码
- `logo`：台标 URL，可为空字符串
- `source_type`：`hls`、`youtube` 或 `m3u`
- `url`：HLS 地址或 YouTube Live 页面
- `epg_id`：XMLTV 中的频道 ID，应与 `tvg-id` 对应
- `enabled`：是否启用
- `allow_offline`：可选。设为 `true` 时，即使检测离线也会写入 playlist
- `user_agent`：可选。部分公开 HLS 源要求特定 User-Agent
- `referrer`：可选。部分公开 HLS 源要求 Referer

默认配置优先启用公开 HLS 源。YouTube Live 示例默认禁用，因为无 Cookie 的 CI 环境可能触发 YouTube 反机器人校验。

YouTube 示例：

```yaml
- id: dw-news
  name: DW News
  group: News
  country: DE
  logo: ""
  source_type: youtube
  url: https://www.youtube.com/@dwnews/live
  epg_id: dw-news.de
  enabled: true
```

## 合法性边界

建议只添加以下类型的源：

- 电视台官网公开提供的 HLS/m3u8
- 电视台官方 YouTube Live
- 政府、公共媒体、教育机构公开直播
- 明确允许公开访问和转发的公共 IPTV 源

不要添加：

- 需要付费订阅、登录或地区破解的地址
- DRM 平台地址
- 来历不明的盗链
- 需要绕过 token、签名、加密或风控的地址

## 常见问题

### YouTube 地址为什么会失效？

`yt-dlp -g` 解析出来的是临时播放地址，通常带有签名和过期时间，所以不能长期写死。项目每次构建都会重新解析 YouTube Live。

### 为什么部分台湾商业频道没有稳定源？

很多商业频道的稳定播出权在有线电视、OTT 或授权平台中，公开 YouTube Live 可能只在新闻事件或特定时段开放。项目会把解析或检测失败写入 `dist/report.json`。

### 为什么不支持 DRM 平台？

DRM 的目的就是限制未授权播放。绕过 DRM 通常违反平台条款和法律，本项目不会支持。

### 为什么某些源在中国大陆无法播放？

常见原因包括 CDN 区域策略、网络互联质量、DNS 污染、平台访问限制，以及 YouTube 等服务本身不可达。构建环境能访问不代表播放器所在网络也能访问。

## 开发结构

```text
config/channels.yml          频道配置
src/config_loader.py         配置读取与校验
src/resolver.py              播放地址解析
src/validator.py             可用性检测
src/playlist.py              M3U 生成
src/epg.py                   XMLTV 生成
src/report.py                JSON 报告
src/main.py                  构建流程编排
src/cli.py                   CLI
dist/                        生成输出
```
