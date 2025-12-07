# JD_COOKIE 管理系统

本项目是一个基于 Flask 的 JD_COOKIE 管理系统，支持 JD_COOKIE 的查询与更新，适合内部使用。前端页面美观，支持 Docker 部署。

![](figs/1.png)

![](figs/2.png)

## 功能简介

- 查询 JD_COOKIE 状态（按 pt_pin 查询）
- 更新并启用 JD_COOKIE
- 限制同一 IP 每日访问次数
- 支持 Docker 一键部署

## 目录结构

```
.
├── app.py                  # Flask 主程序
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml.example # Compose 示例配置
├── static/
│   ├── index.html
│   └── jdupdate.html       # 前端页面
├── .dockerignore
└── .gitignore
```

## 快速开始

### 1. 本地运行

1. 安装依赖

    ```sh
    pip install -r requirements.txt
    ```

2. 设置环境变量

    ```sh
    export QL_HOST=http://your-qinglong-host:5789
    export CLIENT_ID=your_client_id
    export CLIENT_SECRET=your_client_secret

    # 可选配置
    export MAX_DAILY_ACCESS=7
    export BACKGROUND_IMAGE_URL=https://t.alcy.cc/ycy
    ```

3. 运行应用

    ```sh
    python app.py
    ```

### 2. Docker Compose 部署（推荐）

1. 复制并修改配置文件

    ```sh
    cp docker-compose.yaml.example docker-compose.yaml
    ```

2. 编辑 `docker-compose.yaml`，填入你的青龙面板配置信息


3. 构建镜像

    ```sh
    docker build -t jdupdate .
    ```

4. 启动服务

    ```sh
    docker-compose up -d
    ```

4. 查看日志

    ```sh
    docker-compose logs -f
    ```

## 环境变量说明

### 必需环境变量
- `QL_HOST`：青龙面板地址（如 `http://192.168.192.37:5789`）
- `CLIENT_ID`：青龙开放 API 的 Client ID
- `CLIENT_SECRET`：青龙开放 API 的 Client Secret

### 可选环境变量
- `MAX_DAILY_ACCESS`：每个 IP 每日最大访问次数（默认值：`7`）
- `BACKGROUND_IMAGE_URL`：页面背景图片 URL（默认值：`https://t.alcy.cc/ycy`）
  - 可以使用任何图片 URL
  - 推荐使用随机图片 API 或自定义图片链接

## 前端页面

访问 `http://localhost:8080` 即可使用管理界面，支持 JD_COOKIE 查询与更新。

## 功能特性

### IP 访问限制
- 默认每个 IP 每日最多可访问 7 次（可通过 `MAX_DAILY_ACCESS` 环境变量修改）
- 访问计数自动在每日重置
- 超过限制后会显示剩余重置时间

### 自定义背景
- 支持通过 `BACKGROUND_IMAGE_URL` 环境变量自定义页面背景图
- 默认使用随机图片 API
- 可以使用任何公开的图片 URL

### API 接口
- `GET /api/config` - 获取前端配置信息
- `GET /api/envs` - 获取青龙面板环境变量列表
- `GET /api/jdcookie/query?ptpin=<value>` - 查询指定 pt_pin 的 JD_COOKIE
- `POST /api/jdcookie/update` - 更新并启用 JD_COOKIE

## 注意事项

- 本项目仅供内部学习与交流使用，请勿用于非法用途
- IP 访问限制基于内存存储，应用重启后计数会重置
- 默认限制同一 IP 每日最多 7 次操作，可通过环境变量修改
- 建议在生产环境中使用 HTTPS 协议确保数据传输安全

## 问题反馈及功能开发

[![QQ群](https://img.shields.io/badge/QQ群-965312424-green)](https://qm.qq.com/cgi-bin/qm/qr?k=en97YqjfYaLpebd9Nn8gbSvxVrGdIXy2&jump_from=webapi&authKey=41BmkEjbGeJ81jJNdv7Bf5EDlmW8EHZeH7/nktkXYdLGpZ3ISOS7Ur4MKWXC7xIx)

## License

MIT