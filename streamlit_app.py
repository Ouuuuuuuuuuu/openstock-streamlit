import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json

# 页面配置
st.set_page_config(
    page_title="OpenStock - 开源股票追踪",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stock-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .price-up {
        color: #00c851;
        font-weight: bold;
    }
    .price-down {
        color: #ff4444;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']

# API 配置
FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# 缓存函数
@st.cache_data(ttl=60)
def get_stock_quote(symbol):
    """获取股票实时报价"""
    if not FINNHUB_API_KEY:
        return None
    try:
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {"symbol": symbol, "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"获取报价失败: {e}")
        return None

@st.cache_data(ttl=300)
def search_stocks(query):
    """搜索股票"""
    if not FINNHUB_API_KEY or not query:
        return []
    try:
        url = f"{FINNHUB_BASE_URL}/search"
        params = {"q": query, "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('result', [])[:10]
        return []
    except Exception as e:
        return []

@st.cache_data(ttl=600)
def get_company_profile(symbol):
    """获取公司信息"""
    if not FINNHUB_API_KEY:
        return None
    try:
        url = f"{FINNHUB_BASE_URL}/stock/profile2"
        params = {"symbol": symbol, "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def get_market_news(category="general"):
    """获取市场新闻"""
    if not FINNHUB_API_KEY:
        return []
    try:
        url = f"{FINNHUB_BASE_URL}/news"
        params = {
            "category": category,
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()[:10]
        return []
    except Exception as e:
        return []

@st.cache_data(ttl=60)
def get_market_indices():
    """获取主要市场指数"""
    indices = {
        '^GSPC': '标普500',
        '^DJI': '道琼斯',
        '^IXIC': '纳斯达克'
    }
    results = {}
    for symbol, name in indices.items():
        quote = get_stock_quote(symbol)
        if quote:
            results[name] = quote
    return results

# 侧边栏
with st.sidebar:
    st.markdown("### 🔍 搜索股票")
    search_query = st.text_input("输入股票代码或名称", placeholder="例如: AAPL")
    
    if search_query:
        search_results = search_stocks(search_query)
        if search_results:
            st.markdown("#### 搜索结果")
            for stock in search_results:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{stock['symbol']}** - {stock.get('description', 'N/A')}")
                with col2:
                    if st.button("+ 关注", key=f"add_{stock['symbol']}"):
                        if stock['symbol'] not in st.session_state.watchlist:
                            st.session_state.watchlist.append(stock['symbol'])
                            st.success(f"已添加 {stock['symbol']}")
                            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 我的关注列表")
    
    for symbol in st.session_state.watchlist[:]:
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(symbol, key=f"view_{symbol}"):
                st.session_state.selected_stock = symbol
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"remove_{symbol}"):
                st.session_state.watchlist.remove(symbol)
                st.rerun()

# 主内容区
st.markdown('<p class="main-header">📈 OpenStock 开源股票追踪</p>', unsafe_allow_html=True)

# 检查 API Key
if not FINNHUB_API_KEY:
    st.warning("⚠️ 请在 Streamlit Secrets 中设置 FINNHUB_API_KEY")
    with st.expander("如何配置 API Key"):
        st.markdown("""
        1. 点击右上角 ⚙️ Settings
        2. 选择 Secrets
        3. 添加以下内容:
        ```toml
        FINNHUB_API_KEY = "your_api_key_here"
        ```
        """)

# 市场概览
st.markdown("### 📊 市场概览")
indices = get_market_indices()
if indices:
    cols = st.columns(len(indices))
    for i, (name, data) in enumerate(indices.items()):
        with cols[i]:
            current = data.get('c', 0)
            change = data.get('d', 0)
            change_pct = data.get('dp', 0)
            
            color = "🟢" if change >= 0 else "🔴"
            st.metric(
                label=f"{color} {name}",
                value=f"{current:,.2f}",
                delta=f"{change:+.2f} ({change_pct:+.2f}%)"
            )

# 选中的股票详情
selected_symbol = st.session_state.get('selected_stock', st.session_state.watchlist[0] if st.session_state.watchlist else 'AAPL')

if selected_symbol:
    st.markdown(f"---")
    st.markdown(f"### 📌 {selected_symbol}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 股票报价
        quote = get_stock_quote(selected_symbol)
        if quote:
            current_price = quote.get('c', 0)
            change = quote.get('d', 0)
            change_pct = quote.get('dp', 0)
            high = quote.get('h', 0)
            low = quote.get('l', 0)
            open_price = quote.get('o', 0)
            prev_close = quote.get('pc', 0)
            
            price_color = "price-up" if change >= 0 else "price-down"
            arrow = "▲" if change >= 0 else "▼"
            
            st.markdown(f"""
            <div style="font-size: 3rem; font-weight: bold;">
                ${current_price:.2f} 
                <span class="{price_color}">{arrow} {abs(change):.2f} ({change_pct:.2f}%)</span>
            </div>
            """, unsafe_allow_html=True)
            
            # 详细数据
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
            with metrics_col1:
                st.metric("开盘", f"${open_price:.2f}")
            with metrics_col2:
                st.metric("最高", f"${high:.2f}")
            with metrics_col3:
                st.metric("最低", f"${low:.2f}")
            with metrics_col4:
                st.metric("昨收", f"${prev_close:.2f}")
    
    with col2:
        # 公司信息
        profile = get_company_profile(selected_symbol)
        if profile:
            st.markdown("#### 公司信息")
            st.write(f"**公司名称:** {profile.get('name', 'N/A')}")
            st.write(f"**行业:** {profile.get('finnhubIndustry', 'N/A')}")
            st.write(f"**市值:** ${profile.get('marketCapitalization', 0):,.0f}M")
            st.write(f"**员工:** {profile.get('employeeTotal', 'N/A')}")
            if profile.get('weburl'):
                st.write(f"**官网:** [{profile['weburl']}]({profile['weburl']})")
        else:
            st.info("暂无公司详细信息")

# 关注列表表格
st.markdown("---")
st.markdown("### 📋 关注列表概览")

if st.session_state.watchlist:
    watchlist_data = []
    for symbol in st.session_state.watchlist:
        quote = get_stock_quote(symbol)
        if quote:
            watchlist_data.append({
                '代码': symbol,
                '现价': f"${quote.get('c', 0):.2f}",
                '涨跌': f"{quote.get('d', 0):+.2f}",
                '涨跌幅%': f"{quote.get('dp', 0):+.2f}%",
                '最高': f"${quote.get('h', 0):.2f}",
                '最低': f"${quote.get('l', 0):.2f}"
            })
    
    if watchlist_data:
        df = pd.DataFrame(watchlist_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

# 市场新闻
st.markdown("---")
st.markdown("### 📰 市场新闻")

news = get_market_news()
if news:
    for item in news[:5]:
        with st.expander(f"📰 {item.get('headline', '无标题')}"):
            st.write(item.get('summary', '暂无摘要'))
            if item.get('url'):
                st.write(f"[阅读原文]({item['url']})")
            st.caption(f"来源: {item.get('source', '未知')} | {datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')}")
else:
    st.info("暂无新闻数据")

# 页脚
st.markdown("---")
st.caption("🚀 OpenStock - 开源股票追踪 | 数据由 Finnhub 提供 | Built with Streamlit")
