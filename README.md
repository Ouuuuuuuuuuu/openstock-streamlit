# OpenStock Streamlit

开源股票追踪应用 - Streamlit 版本

## 功能特性

- 📈 实时股票价格追踪
- 🔍 股票搜索
- 📋 个人关注列表
- 📊 市场指数概览
- 📰 市场新闻
- 🏢 公司信息展示

## 部署到 Streamlit Cloud

1. Fork 此仓库到您的 GitHub
2. 访问 https://streamlit.io/cloud
3. 使用 GitHub 账号登录
4. 部署应用
5. 在 Settings > Secrets 中添加:

```toml
FINNHUB_API_KEY = "your_finnhub_api_key"
```

## 本地运行

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## API Key 获取

访问 https://finnhub.io 注册免费账号获取 API Key

## License

AGPL-3.0
