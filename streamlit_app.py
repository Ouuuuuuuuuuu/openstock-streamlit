import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import html

# ========== 页面配置 ==========
st.set_page_config(
    page_title="OpenStock 📈 - 开源股票追踪",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS 样式 ==========
st.markdown("""
<style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    }
    
    /* 主标题 */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00d4aa 0%, #00a8e8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #8b949e;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* 价格样式 */
    .price-container {
        text-align: center;
        padding: 1.5rem;
        background: rgba(22, 27, 34, 0.8);
        border-radius: 16px;
        border: 1px solid rgba(48, 54, 61, 0.8);
    }
    
    .price-large {
        font-size: 3rem;
        font-weight: 700;
        color: #f0f6fc;
    }
    
    .price-up {
        color: #3fb950;
        font-weight: 600;
    }
    
    .price-down {
        color: #f85149;
        font-weight: 600;
    }
    
    /* 卡片样式 */
    .stock-card {
        background: rgba(22, 27, 34, 0.6);
        border: 1px solid rgba(48, 54, 61, 0.6);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .stock-card:hover {
        border-color: rgba(48, 54, 61, 1);
        transform: translateY(-2px);
    }
    
    /* 指标卡片 */
    .metric-box {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.1) 0%, rgba(0, 168, 232, 0.1) 100%);
        border: 1px solid rgba(0, 212, 170, 0.2);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    
    /* 侧边栏样式 */
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #f0f6fc;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(48, 54, 61, 0.5);
    }
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    
    /* 表格样式 */
    .dataframe {
        font-size: 0.9rem !important;
    }
    
    /* 新闻卡片 */
    .news-card {
        background: rgba(22, 27, 34, 0.6);
        border-left: 3px solid #00d4aa;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* TradingView 容器 */
    .tradingview-container {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(48, 54, 61, 0.6);
    }
</style>
""", unsafe_allow_html=True)

# ========== 初始化 Session State ==========
def init_session():
    defaults = {
        'watchlist': ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA'],
        'alerts': [],
        'selected_symbol': 'AAPL',
        'search_results': [],
        'market_tab': 'overview',
        'chart_type': 'candle'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ========== API 配置 ==========
FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# ========== 缓存函数 ==========
@st.cache_data(ttl=60)
def get_stock_quote(symbol):
    """获取股票实时报价"""
    if not FINNHUB_API_KEY:
        return None
    try:
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {"symbol": symbol, "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
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
            return response.json().get('result', [])[:10]
        return []
    except:
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
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=300)
def get_market_news(category="general"):
    """获取市场新闻"""
    if not FINNHUB_API_KEY:
        return []
    try:
        url = f"{FINNHUB_BASE_URL}/news"
        params = {"category": category, "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        return response.json()[:15] if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=300)
def get_company_news(symbol, from_date=None, to_date=None):
    """获取公司新闻"""
    if not FINNHUB_API_KEY:
        return []
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not to_date:
        to_date = datetime.now().strftime('%Y-%m-%d')
    try:
        url = f"{FINNHUB_BASE_URL}/company-news"
        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date,
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        return response.json()[:10] if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=600)
def get_basic_financials(symbol):
    """获取基本财务数据"""
    if not FINNHUB_API_KEY:
        return None
    try:
        url = f"{FINNHUB_BASE_URL}/stock/metric"
        params = {"symbol": symbol, "metric": "all", "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=60)
def get_market_indices():
    """获取主要市场指数"""
    indices = {
        '^GSPC': '标普500',
        '^DJI': '道琼斯',
        '^IXIC': '纳斯达克',
        '^RUT': '罗素2000'
    }
    results = {}
    for symbol, name in indices.items():
        quote = get_stock_quote(symbol)
        if quote:
            results[name] = quote
    return results

@st.cache_data(ttl=3600)
def get_stock_peers(symbol):
    """获取同行业股票"""
    if not FINNHUB_API_KEY:
        return []
    try:
        url = f"{FINNHUB_BASE_URL}/stock/peers"
        params = {"symbol": symbol, "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        return response.json()[:5] if response.status_code == 200 else []
    except:
        return []

# ========== TradingView 组件 ==========
def tradingview_widget(widget_type, symbol="", height=400):
    """嵌入 TradingView 组件"""
    
    tv_symbol = symbol.upper()
    if ':' not in tv_symbol:
        # 自动添加交易所前缀
        if tv_symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'NFLX', 'TSLA']:
            tv_symbol = f"NASDAQ:{tv_symbol}"
        else:
            tv_symbol = f"NYSE:{tv_symbol}"
    
    widgets = {
        'overview': {
            'script': 'market-overview',
            'config': '''{
                "colorTheme": "dark",
                "dateRange": "12M",
                "locale": "zh_CN",
                "largeChartUrl": "",
                "isTransparent": true,
                "showFloatingTooltip": true,
                "tabs": [
                    {
                        "title": "科技",
                        "symbols": [
                            {"s": "NASDAQ:AAPL", "d": "Apple"},
                            {"s": "NASDAQ:MSFT", "d": "Microsoft"},
                            {"s": "NASDAQ:GOOGL", "d": "Alphabet"},
                            {"s": "NASDAQ:NVDA", "d": "NVIDIA"},
                            {"s": "NASDAQ:META", "d": "Meta"},
                            {"s": "NASDAQ:AMZN", "d": "Amazon"}
                        ]
                    },
                    {
                        "title": "金融",
                        "symbols": [
                            {"s": "NYSE:JPM", "d": "JPMorgan"},
                            {"s": "NYSE:BAC", "d": "Bank of America"},
                            {"s": "NYSE:V", "d": "Visa"},
                            {"s": "NYSE:MA", "d": "Mastercard"}
                        ]
                    },
                    {
                        "title": "中概股",
                        "symbols": [
                            {"s": "NYSE:BABA", "d": "Alibaba"},
                            {"s": "NASDAQ:PDD", "d": "PDD"},
                            {"s": "NASDAQ:JD", "d": "JD"},
                            {"s": "NYSE:NIO", "d": "NIO"},
                            {"s": "NASDAQ:BILI", "d": "Bilibili"}
                        ]
                    }
                ],
                "plotLineColorGrowing": "#0FEDBE",
                "plotLineColorFalling": "#F85149",
                "gridLineColor": "rgba(240, 243, 250, 0)",
                "scaleFontColor": "#DBDBDB",
                "belowLineFillColorGrowing": "rgba(41, 98, 255, 0.12)",
                "belowLineFillColorFalling": "rgba(41, 98, 255, 0.12)",
                "symbolActiveColor": "rgba(15, 237, 190, 0.05)",
                "backgroundColor": "#0d1117"
            }'''
        },
        'heatmap': {
            'script': 'stock-heatmap',
            'config': '''{
                "dataSource": "SPX500",
                "blockSize": "market_cap_basic",
                "blockColor": "change",
                "grouping": "sector",
                "isTransparent": true,
                "locale": "zh_CN",
                "colorTheme": "dark",
                "hasTopBar": false,
                "isDataSetEnabled": false,
                "isZoomEnabled": true,
                "hasSymbolTooltip": true
            }'''
        },
        'symbol_info': {
            'script': 'symbol-info',
            'config': f'''{"symbol": "{tv_symbol}", "colorTheme": "dark", "isTransparent": true, "locale": "zh_CN"}'''
        },
        'advanced_chart': {
            'script': 'advanced-chart',
            'config': f'''{"autosize": true, "symbol": "{tv_symbol}", "interval": "D", "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "zh_CN", "enable_publishing": false, "allow_symbol_change": false, "calendar": false, "support_host": "https://www.tradingview.com"}'''
        },
        'technical': {
            'script': 'technical-analysis',
            'config': f'''{"interval": "1h", "width": "100%", "isTransparent": true, "height": "{height}", "symbol": "{tv_symbol}", "showIntervalTabs": true, "locale": "zh_CN", "colorTheme": "dark"}'''
        },
        'company_profile': {
            'script': 'company-profile',
            'config': f'''{"width": "100%", "height": "{height}", "symbol": "{tv_symbol}", "isTransparent": true, "locale": "zh_CN", "colorTheme": "dark"}'''
        },
        'financials': {
            'script': 'financials',
            'config': f'''{"width": "100%", "height": "{height}", "symbol": "{tv_symbol}", "isTransparent": true, "locale": "zh_CN", "colorTheme": "dark", "displayMode": "regular"}'''
        },
        'timeline': {
            'script': 'timeline',
            'config': '''{
                "feedMode": "market",
                "market": "stock",
                "isTransparent": true,
                "displayMode": "regular",
                "width": "100%",
                "height": "400",
                "locale": "zh_CN",
                "colorTheme": "dark"
            }'''
        }
    }
    
    if widget_type not in widgets:
        return
    
    widget = widgets[widget_type]
    
    html_code = f'''
    <div class="tradingview-container">
    <div class="tradingview-widget-container">
    <div class="tradingview-widget-container__widget"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-{widget['script']}.js" async>
    {widget['config']}
    </script>
    </div>
    </div>
    '''
    
    st.components.v1.html(html_code, height=height)

# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown('<p class="sidebar-header">🔍 股票搜索</p>', unsafe_allow_html=True)
    
    search_query = st.text_input("", placeholder="输入代码或名称...", key="search_input")
    
    if search_query:
        results = search_stocks(search_query)
        if results:
            st.markdown("**搜索结果：**")
            for stock in results:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{stock['symbol']}**  
{stock.get('description', '')[:20]}...")
                with col2:
                    if st.button("➕", key=f"add_{stock['symbol']}"):
                        if stock['symbol'] not in st.session_state.watchlist:
                            st.session_state.watchlist.append(stock['symbol'])
                            st.success(f"已添加 {stock['symbol']}")
                            st.rerun()
    
    st.markdown("---")
    st.markdown('<p class="sidebar-header">📋 我的关注</p>', unsafe_allow_html=True)
    
    for symbol in st.session_state.watchlist[:]:
        quote = get_stock_quote(symbol)
        change = quote.get('dp', 0) if quote else 0
        color = "🟢" if change >= 0 else "🔴"
        
        cols = st.columns([4, 1, 1])
        with cols[0]:
            if st.button(f"{color} {symbol}", key=f"select_{symbol}"):
                st.session_state.selected_symbol = symbol
                st.rerun()
        with cols[1]:
            if quote:
                st.caption(f"{quote.get('c', 0):.2f}")
        with cols[2]:
            if st.button("🗑️", key=f"del_{symbol}"):
                st.session_state.watchlist.remove(symbol)
                st.rerun()
    
    st.markdown("---")
    st.markdown('<p class="sidebar-header">⚡ 快速导航</p>', unsafe_allow_html=True)
    
    if st.button("📊 市场概览", use_container_width=True):
        st.session_state.market_tab = 'overview'
        st.rerun()
    if st.button("🔥 热力图", use_container_width=True):
        st.session_state.market_tab = 'heatmap'
        st.rerun()
    if st.button("📰 市场新闻", use_container_width=True):
        st.session_state.market_tab = 'news'
        st.rerun()

# ========== 主内容 ==========
st.markdown('<p class="main-title">📈 OpenStock</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">开源股票追踪平台 | 实时数据 · 专业图表 · 智能分析</p>', unsafe_allow_html=True)

# API Key 检查
if not FINNHUB_API_KEY:
    st.warning("⚠️ 请在 Streamlit Secrets 中设置 FINNHUB_API_KEY")
    with st.expander("🔧 配置指南"):
        st.markdown("""
        **设置步骤：**
        1. 访问 [Finnhub](https://finnhub.io) 注册免费账号
        2. 获取 API Key
        3. 在 Streamlit Cloud → Settings → Secrets 中添加：
        ```toml
        FINNHUB_API_KEY = "your_api_key_here"
        ```
        """)

# 市场标签页
tab = st.session_state.get('market_tab', 'overview')

if tab == 'overview':
    # 市场概览
    st.markdown("### 📊 全球市场指数")
    indices = get_market_indices()
    
    if indices:
        cols = st.columns(len(indices))
        for i, (name, data) in enumerate(indices.items()):
            with cols[i]:
                current = data.get('c', 0)
                change = data.get('d', 0)
                change_pct = data.get('dp', 0)
                
                delta_color = "normal" if change >= 0 else "inverse"
                st.metric(
                    label=f"**{name}**",
                    value=f"{current:,.2f}",
                    delta=f"{change:+.2f} ({change_pct:+.2f}%)",
                    delta_color=delta_color
                )
    
    st.markdown("---")
    
    # TradingView 市场概览
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown("### 📈 行业走势")
        tradingview_widget('overview', height=500)
    with col2:
        st.markdown("### 📰 市场动态")
        tradingview_widget('timeline', height=500)

elif tab == 'heatmap':
    st.markdown("### 🔥 标普500 热力图")
    tradingview_widget('heatmap', height=800)

elif tab == 'news':
    st.markdown("### 📰 市场新闻")
    news = get_market_news()
    
    if news:
        for item in news[:20]:
            with st.expander(f"📰 {item.get('headline', '无标题')}"):
                st.write(item.get('summary', '暂无摘要'))
                col1, col2 = st.columns([1, 2])
                with col1:
                    if item.get('url'):
                        st.write(f"[阅读全文]({item['url']})")
                with col2:
                    st.caption(f"📌 {item.get('source', '未知')} | {datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("暂无新闻数据")

# ========== 股票详情页 ==========
symbol = st.session_state.get('selected_symbol', 'AAPL')

if symbol:
    st.markdown("---")
    st.markdown(f"## 📌 {symbol} 详细分析")
    
    # 获取数据
    quote = get_stock_quote(symbol)
    profile = get_company_profile(symbol)
    financials = get_basic_financials(symbol)
    
    # 顶部信息栏
    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
    
    with col1:
        if profile:
            st.markdown(f"### {profile.get('name', symbol)}")
            st.caption(f"{profile.get('finnhubIndustry', 'N/A')} | {profile.get('exchange', 'N/A')}")
    
    with col2:
        if quote:
            price = quote.get('c', 0)
            change = quote.get('d', 0)
            change_pct = quote.get('dp', 0)
            color_class = "price-up" if change >= 0 else "price-down"
            arrow = "▲" if change >= 0 else "▼"
            
            st.markdown(f"""
            <div class="price-container">
                <div class="price-large">${price:.2f}</div>
                <div class="{color_class}">{arrow} {abs(change):.2f} ({change_pct:+.2f}%)</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if quote:
            st.metric("最高", f"${quote.get('h', 0):.2f}")
            st.metric("最低", f"${quote.get('l', 0):.2f}")
    
    with col4:
        if quote:
            st.metric("开盘", f"${quote.get('o', 0):.2f}")
            st.metric("昨收", f"${quote.get('pc', 0):.2f}")
    
    with col5:
        if financials and 'metric' in financials:
            metrics = financials['metric']
            pe = metrics.get('peBasicExclExtraTTM', 'N/A')
            market_cap = metrics.get('marketCapitalization', 'N/A')
            if isinstance(market_cap, (int, float)):
                market_cap = f"${market_cap:,.0f}M"
            st.metric("市盈率", pe if pe else "N/A")
            st.metric("市值", market_cap)
    
    # 操作按钮
    cols = st.columns([1, 1, 1, 4])
    with cols[0]:
        if symbol not in st.session_state.watchlist:
            if st.button("➕ 加入关注", use_container_width=True):
                st.session_state.watchlist.append(symbol)
                st.success(f"已添加 {symbol} 到关注列表")
                st.rerun()
        else:
            st.button("✅ 已关注", disabled=True, use_container_width=True)
    
    with cols[1]:
        st.selectbox("图表类型", ["K线图", "基线图"], key="chart_type_select")
    
    # TradingView 图表
    st.markdown("---")
    
    col_chart, col_info = st.columns([3, 2])
    
    with col_chart:
        st.markdown("### 📊 技术分析")
        tradingview_widget('advanced_chart', symbol, height=500)
    
    with col_info:
        st.markdown("### 📋 技术指标")
        tradingview_widget('technical', symbol, height=250)
        
        st.markdown("### 🏢 公司简介")
        if profile:
            st.write(f"**行业:** {profile.get('finnhubIndustry', 'N/A')}")
            st.write(f"**国家:** {profile.get('country', 'N/A')}")
            st.write(f"**货币:** {profile.get('currency', 'N/A')}")
            st.write(f"**IPO日期:** {profile.get('ipo', 'N/A')}")
            st.write(f"**员工:** {profile.get('employeeTotal', 'N/A'):,}" if profile.get('employeeTotal') else "**员工:** N/A")
            if profile.get('weburl'):
                st.write(f"**官网:** [{profile['weburl']}]({profile['weburl']})")
            if profile.get('phone'):
                st.write(f"**电话:** {profile['phone']}")
    
    # 财务数据
    st.markdown("---")
    st.markdown("### 💰 财务数据")
    tradingview_widget('financials', symbol, height=500)
    
    # 公司新闻
    st.markdown("---")
    st.markdown(f"### 📰 {symbol} 相关新闻")
    company_news = get_company_news(symbol)
    
    if company_news:
        for item in company_news[:10]:
            with st.expander(f"📰 {item.get('headline', '无标题')}"):
                st.write(item.get('summary', '暂无摘要'))
                if item.get('url'):
                    st.write(f"[阅读全文]({item['url']})")
                st.caption(f"📌 {item.get('source', '未知')} | {datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("暂无相关新闻")

# ========== 关注列表表格 ==========
st.markdown("---")
st.markdown("### 📋 关注列表概览")

if st.session_state.watchlist:
    watchlist_data = []
    for sym in st.session_state.watchlist:
        quote = get_stock_quote(sym)
        profile = get_company_profile(sym)
        financials = get_basic_financials(sym)
        
        if quote:
            row = {
                '代码': sym,
                '名称': profile.get('name', sym) if profile else sym,
                '现价': f"${quote.get('c', 0):.2f}",
                '涨跌': f"{quote.get('d', 0):+.2f}",
                '涨跌幅%': f"{quote.get('dp', 0):+.2f}%",
                '最高': f"${quote.get('h', 0):.2f}",
                '最低': f"${quote.get('l', 0):.2f}",
            }
            
            if financials and 'metric' in financials:
                metrics = financials['metric']
                pe = metrics.get('peBasicExclExtraTTM')
                row['市盈率'] = f"{pe:.2f}" if pe else "N/A"
                
                market_cap = metrics.get('marketCapitalization')
                if isinstance(market_cap, (int, float)):
                    row['市值'] = f"${market_cap/1000:.2f}B" if market_cap >= 1000 else f"${market_cap:.0f}M"
                else:
                    row['市值'] = "N/A"
            
            watchlist_data.append(row)
    
    if watchlist_data:
        df = pd.DataFrame(watchlist_data)
        
        # 使用 st.dataframe 并设置样式
        def color_change(val):
            if isinstance(val, str):
                if '+' in val:
                    return 'color: #3fb950'
                elif '-' in val and val != '-':
                    return 'color: #f85149'
            return ''
        
        styled_df = df.style.map(color_change, subset=['涨跌', '涨跌幅%'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ========== 页脚 ==========
st.markdown("---")
st.caption("""
🚀 **OpenStock** - 开源股票追踪平台 | Built with Streamlit + TradingView + Finnhub

数据仅供参考，不构成投资建议。投资有风险，入市需谨慎。
""")
