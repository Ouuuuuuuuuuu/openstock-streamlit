import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime, timedelta

# ========== 页面配置 ==========
st.set_page_config(
    page_title="OpenStock - 开源股票追踪",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 深色主题 CSS ==========
st.markdown("""
<style>
    /* 全局深色背景 */
    .stApp {
        background: #0a0a0a;
    }
    
    /* 主标题 - 渐变效果 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00d4aa 0%, #00a8e8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    
    /* 卡片样式 - 玻璃拟态 */
    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(55, 65, 81, 0.5);
        border-radius: 12px;
        padding: 1rem;
        backdrop-filter: blur(10px);
    }
    
    /* 价格样式 */
    .price-large {
        font-size: 2.5rem;
        font-weight: 700;
        color: #f9fafb;
    }
    
    .price-up {
        color: #10b981;
        font-weight: 600;
    }
    
    .price-down {
        color: #ef4444;
        font-weight: 600;
    }
    
    /* 侧边栏 */
    .sidebar-header {
        font-size: 0.875rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 1.5rem 0 0.75rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(55, 65, 81, 0.5);
    }
    
    /* 股票标签 */
    .stock-chip {
        display: inline-flex;
        align-items: center;
        background: rgba(31, 41, 55, 0.8);
        border: 1px solid rgba(75, 85, 99, 0.5);
        border-radius: 6px;
        padding: 0.375rem 0.75rem;
        margin: 0.25rem;
        font-size: 0.875rem;
        color: #e5e7eb;
        transition: all 0.2s;
    }
    
    .stock-chip:hover {
        background: rgba(55, 65, 81, 0.8);
        border-color: rgba(107, 114, 128, 0.5);
    }
    
    /* TradingView 容器 */
    .tv-container {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(55, 65, 81, 0.5);
        background: rgba(17, 24, 39, 0.5);
    }
    
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    
    /* 分隔线 */
    hr {
        border-color: rgba(55, 65, 81, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== Session State 初始化 ==========
def init_session():
    defaults = {
        'watchlist': ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'META'],
        'alerts': [],
        'selected_symbol': 'AAPL',
        'market_tab': 'overview',
        'chart_type': 'candle',
        'sort_order': None,  # None, 'asc', 'desc'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ========== API 配置 ==========
FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# ========== 数据获取函数 ==========
@st.cache_data(ttl=60)
def get_stock_quote(symbol):
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
    if not FINNHUB_API_KEY:
        return []
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not to_date:
        to_date = datetime.now().strftime('%Y-%m-%d')
    try:
        url = f"{FINNHUB_BASE_URL}/company-news"
        params = {"symbol": symbol, "from": from_date, "to": to_date, "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        return response.json()[:10] if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=600)
def get_basic_financials(symbol):
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
    indices = {'^GSPC': '标普500', '^DJI': '道琼斯', '^IXIC': '纳斯达克'}
    results = {}
    for symbol, name in indices.items():
        quote = get_stock_quote(symbol)
        if quote:
            results[name] = quote
    return results

# ========== TradingView 组件 ==========
def format_symbol_for_tv(symbol):
    """转换股票代码为 TradingView 格式"""
    tv_symbol = symbol.upper()
    if ':' not in tv_symbol:
        nasdaq_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'NFLX', 'TSLA', 'AMD', 'INTC', 'PYPL', 'ADBE', 'CSCO', 'CMCSA', 'PEP', 'AVGO', 'QCOM', 'TXN', 'TMUS', 'AMGN', 'SBUX', 'INTU', 'BKNG', 'ISRG', 'GILD', 'MDLZ', 'VRTX', 'ADP', 'FISV', 'CSX']
        if tv_symbol in nasdaq_stocks:
            tv_symbol = f"NASDAQ:{tv_symbol}"
        else:
            tv_symbol = f"NYSE:{tv_symbol}"
    return tv_symbol

def tradingview_widget(widget_type, symbol="", height=400):
    tv_symbol = format_symbol_for_tv(symbol) if symbol else ""
    
    configs = {
        'market_overview': {
            'script': 'market-overview',
            'config': '''{
                "colorTheme": "dark",
                "dateRange": "12M",
                "locale": "en",
                "largeChartUrl": "",
                "isTransparent": true,
                "showFloatingTooltip": true,
                "tabs": [
                    {
                        "title": "Technology",
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
                        "title": "Financial",
                        "symbols": [
                            {"s": "NYSE:JPM", "d": "JPMorgan"},
                            {"s": "NYSE:BAC", "d": "Bank of America"},
                            {"s": "NYSE:WFC", "d": "Wells Fargo"},
                            {"s": "NYSE:V", "d": "Visa"},
                            {"s": "NYSE:MA", "d": "Mastercard"}
                        ]
                    },
                    {
                        "title": "Services",
                        "symbols": [
                            {"s": "NASDAQ:TSLA", "d": "Tesla"},
                            {"s": "NYSE:BABA", "d": "Alibaba"},
                            {"s": "NYSE:WMT", "d": "Walmart"},
                            {"s": "NYSE:HD", "d": "Home Depot"},
                            {"s": "NYSE:DIS", "d": "Disney"}
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
                "backgroundColor": "#0a0a0a"
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
                "locale": "en",
                "colorTheme": "dark",
                "hasTopBar": false,
                "isDataSetEnabled": false,
                "isZoomEnabled": true,
                "hasSymbolTooltip": true,
                "width": "100%",
                "height": "100%"
            }'''
        },
        'market_quotes': {
            'script': 'market-quotes',
            'config': '''{
                "title": "Stocks",
                "width": "100%",
                "locale": "en",
                "showSymbolLogo": true,
                "colorTheme": "dark",
                "isTransparent": true,
                "symbolsGroups": [
                    {
                        "name": "Technology",
                        "symbols": [
                            {"name": "NASDAQ:AAPL", "displayName": "Apple"},
                            {"name": "NASDAQ:MSFT", "displayName": "Microsoft"},
                            {"name": "NASDAQ:GOOGL", "displayName": "Alphabet"},
                            {"name": "NASDAQ:NVDA", "displayName": "NVIDIA"},
                            {"name": "NASDAQ:META", "displayName": "Meta"}
                        ]
                    },
                    {
                        "name": "Financial",
                        "symbols": [
                            {"name": "NYSE:JPM", "displayName": "JPMorgan"},
                            {"name": "NYSE:BAC", "displayName": "Bank of America"},
                            {"name": "NYSE:V", "displayName": "Visa"},
                            {"name": "NYSE:MA", "displayName": "Mastercard"}
                        ]
                    }
                ]
            }'''
        },
        'timeline': {
            'script': 'timeline',
            'config': '''{
                "displayMode": "regular",
                "feedMode": "market",
                "colorTheme": "dark",
                "isTransparent": true,
                "locale": "en",
                "market": "stock"
            }'''
        },
        'symbol_info': {
            'script': 'symbol-info',
            'config': f'{{"symbol": "{tv_symbol}", "colorTheme": "dark", "isTransparent": true, "locale": "en"}}'
        },
        'advanced_chart': {
            'script': 'advanced-chart',
            'config': f'''{{
                "autosize": true,
                "symbol": "{tv_symbol}",
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "enable_publishing": false,
                "allow_symbol_change": false,
                "calendar": false,
                "support_host": "https://www.tradingview.com"
            }}'''
        },
        'baseline': {
            'script': 'advanced-chart',
            'config': f'''{{
                "autosize": true,
                "symbol": "{tv_symbol}",
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "10",
                "locale": "en",
                "enable_publishing": false,
                "allow_symbol_change": false
            }}'''
        },
        'technical': {
            'script': 'technical-analysis',
            'config': f'''{{
                "interval": "1h",
                "width": "100%",
                "isTransparent": true,
                "height": "100%",
                "symbol": "{tv_symbol}",
                "showIntervalTabs": true,
                "locale": "en",
                "colorTheme": "dark"
            }}'''
        },
        'company_profile': {
            'script': 'company-profile',
            'config': f'''{{
                "width": "100%",
                "height": "100%",
                "symbol": "{tv_symbol}",
                "isTransparent": true,
                "locale": "en",
                "colorTheme": "dark"
            }}'''
        },
        'financials': {
            'script': 'financials',
            'config': f'''{{
                "width": "100%",
                "height": "100%",
                "symbol": "{tv_symbol}",
                "isTransparent": true,
                "locale": "en",
                "colorTheme": "dark",
                "displayMode": "regular"
            }}'''
        }
    }
    
    if widget_type not in configs:
        return
    
    widget = configs[widget_type]
    html_code = f'''
    <div class="tv-container">
    <div class="tradingview-widget-container">
    <div class="tradingview-widget-container__widget"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-{widget['script']}.js" async>
    {widget['config']}
    </script>
    </div>
    </div>
    '''
    st.components.v1.html(html_code, height=height)

def tradingview_watchlist(symbols, height=550):
    """关注列表专用 TradingView 组件"""
    symbol_list = []
    for sym in symbols:
        tv_sym = format_symbol_for_tv(sym)
        symbol_list.append(f'{{"name": "{tv_sym}", "displayName": "{sym}"}}')
    
    symbols_json = ','.join(symbol_list)
    
    html_code = f'''
    <div class="tv-container">
    <div class="tradingview-widget-container">
    <div class="tradingview-widget-container__widget"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-quotes.js" async>
    {{
        "width": "100%",
        "height": "{height}",
        "symbolsGroups": [
            {{
                "name": "My Watchlist",
                "symbols": [{symbols_json}]
            }}
        ],
        "showSymbolLogo": true,
        "isTransparent": true,
        "colorTheme": "dark",
        "locale": "en"
    }}
    </script>
    </div>
    </div>
    '''
    st.components.v1.html(html_code, height=height)

# ========== 侧边栏 ==========
with st.sidebar:
    # Logo/标题
    st.markdown('<div style="text-align: center; padding: 1rem 0;">', unsafe_allow_html=True)
    st.markdown('<span style="font-size: 1.5rem; font-weight: 800; color: #00d4aa;">📈 OpenStock</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 导航
    st.markdown('<div class="sidebar-header">Navigation</div>', unsafe_allow_html=True)
    
    nav_items = {
        'overview': '📊 Dashboard',
        'heatmap': '🔥 Heatmap', 
        'watchlist': '📋 Watchlist',
        'news': '📰 News'
    }
    
    for key, label in nav_items.items():
        if st.button(label, use_container_width=True, key=f"nav_{key}"):
            st.session_state.market_tab = key
            st.rerun()
    
    # 搜索
    st.markdown('<div class="sidebar-header">Search</div>', unsafe_allow_html=True)
    search_query = st.text_input("", placeholder="Search stocks...", label_visibility="collapsed")
    
    if search_query:
        results = search_stocks(search_query)
        if results:
            st.markdown("**Results:**")
            for stock in results[:5]:
                cols = st.columns([3, 1])
                with cols[0]:
                    desc = stock.get('description', '')[:25]
                    st.write(f"**{stock['symbol']}** - {desc}")
                with cols[1]:
                    if st.button("➕", key=f"add_{stock['symbol']}"):
                        if stock['symbol'] not in st.session_state.watchlist:
                            st.session_state.watchlist.append(stock['symbol'])
                            st.success(f"Added {stock['symbol']}")
                            st.rerun()
    
    # 关注列表
    st.markdown('<div class="sidebar-header">Watchlist</div>', unsafe_allow_html=True)
    
    # 排序按钮
    sort_cols = st.columns(3)
    with sort_cols[0]:
        if st.button("Sort", key="sort_btn"):
            order = st.session_state.sort_order
            if order is None:
                st.session_state.sort_order = 'asc'
            elif order == 'asc':
                st.session_state.sort_order = 'desc'
            else:
                st.session_state.sort_order = None
            st.rerun()
    
    current_order = st.session_state.sort_order
    sort_label = "A-Z" if current_order == 'asc' else "Z-A" if current_order == 'desc' else "Default"
    st.caption(f"Sorted: {sort_label}")
    
    # 排序后的列表
    watchlist = st.session_state.watchlist.copy()
    if current_order == 'asc':
        watchlist.sort()
    elif current_order == 'desc':
        watchlist.sort(reverse=True)
    
    for symbol in watchlist:
        quote = get_stock_quote(symbol)
        change = quote.get('dp', 0) if quote else 0
        color = "🟢" if change >= 0 else "🔴"
        price = quote.get('c', 0) if quote else 0
        
        cols = st.columns([4, 2, 1])
        with cols[0]:
            if st.button(f"{color} {symbol}", key=f"sel_{symbol}", use_container_width=True):
                st.session_state.selected_symbol = symbol
                st.session_state.market_tab = 'stock_detail'
                st.rerun()
        with cols[1]:
            st.caption(f"${price:.2f}")
        with cols[2]:
            if st.button("🗑️", key=f"del_{symbol}"):
                st.session_state.watchlist.remove(symbol)
                st.rerun()

# ========== 主内容区 ==========
st.markdown('<p class="main-title">OpenStock</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Open-source stock tracking platform — free forever</p>', unsafe_allow_html=True)

# API Key 检查
if not FINNHUB_API_KEY:
    st.warning("⚠️ Please set FINNHUB_API_KEY in Streamlit Secrets")
    with st.expander("Setup Guide"):
        st.markdown("""
        1. Get free API key at [Finnhub](https://finnhub.io)
        2. Go to Streamlit Cloud → Settings → Secrets
        3. Add: `FINNHUB_API_KEY = "your_key"`
        """)

tab = st.session_state.market_tab

# ========== Dashboard / Overview ==========
if tab == 'overview':
    # 市场指数
    st.markdown("### 📊 Market Overview")
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
    
    # 双栏布局 - Market Overview + Timeline
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📈 Markets")
        tradingview_widget('market_overview', height=500)
    
    with col2:
        st.markdown("### 📰 Market News")
        tradingview_widget('timeline', height=500)
    
    st.markdown("---")
    
    # 行情数据表格
    st.markdown("### 📋 Market Quotes")
    tradingview_widget('market_quotes', height=400)

# ========== Heatmap ==========
elif tab == 'heatmap':
    st.markdown("### 🔥 Stock Heatmap (S&P 500)")
    tradingview_widget('heatmap', height=800)

# ========== Watchlist ==========
elif tab == 'watchlist':
    st.markdown("### 📋 My Watchlist")
    
    if st.session_state.watchlist:
        # 添加股票按钮
        cols = st.columns([1, 4])
        with cols[0]:
            st.markdown(f"**{len(st.session_state.watchlist)}** stocks")
        
        st.markdown("---")
        
        # TradingView 关注列表
        tradingview_watchlist(st.session_state.watchlist, height=550)
        
        st.markdown("---")
        
        # 关注列表详情表格
        st.markdown("### 📊 Watchlist Details")
        watchlist_data = []
        for sym in st.session_state.watchlist:
            quote = get_stock_quote(sym)
            profile = get_company_profile(sym)
            financials = get_basic_financials(sym)
            
            if quote:
                row = {
                    'Symbol': sym,
                    'Name': profile.get('name', sym) if profile else sym,
                    'Price': f"${quote.get('c', 0):.2f}",
                    'Change': f"{quote.get('d', 0):+.2f}",
                    'Change %': f"{quote.get('dp', 0):+.2f}%",
                    'High': f"${quote.get('h', 0):.2f}",
                    'Low': f"${quote.get('l', 0):.2f}",
                }
                
                if financials and 'metric' in financials:
                    metrics = financials['metric']
                    pe = metrics.get('peBasicExclExtraTTM')
                    row['P/E'] = f"{pe:.2f}" if pe else "N/A"
                    
                    market_cap = metrics.get('marketCapitalization')
                    if isinstance(market_cap, (int, float)):
                        row['Market Cap'] = f"${market_cap/1000:.2f}B" if market_cap >= 1000 else f"${market_cap:.0f}M"
                    else:
                        row['Market Cap'] = "N/A"
                
                watchlist_data.append(row)
        
        if watchlist_data:
            df = pd.DataFrame(watchlist_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Your watchlist is empty. Search and add stocks from the sidebar.")

# ========== News ==========
elif tab == 'news':
    st.markdown("### 📰 Market News")
    news = get_market_news()
    
    if news:
        for item in news[:20]:
            with st.expander(f"📰 {item.get('headline', 'No Title')}"):
                st.write(item.get('summary', 'No summary available.'))
                if item.get('url'):
                    st.write(f"[Read more]({item['url']})")
                st.caption(f"📌 {item.get('source', 'Unknown')} | {datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No news available at the moment.")

# ========== Stock Detail ==========
elif tab == 'stock_detail':
    symbol = st.session_state.get('selected_symbol', 'AAPL')
    
    # 获取数据
    quote = get_stock_quote(symbol)
    profile = get_company_profile(symbol)
    financials = get_basic_financials(symbol)
    
    # 标题栏
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if profile:
            st.markdown(f"### {profile.get('name', symbol)}")
            st.caption(f"{profile.get('finnhubIndustry', 'N/A')} | {profile.get('exchange', 'N/A')}")
        else:
            st.markdown(f"### {symbol}")
    
    with col2:
        if symbol not in st.session_state.watchlist:
            if st.button("➕ Add to Watchlist", use_container_width=True):
                st.session_state.watchlist.append(symbol)
                st.success(f"Added {symbol}")
                st.rerun()
        else:
            st.button("✅ In Watchlist", disabled=True, use_container_width=True)
    
    with col3:
        if st.button("🔙 Back", use_container_width=True):
            st.session_state.market_tab = 'overview'
            st.rerun()
    
    st.markdown("---")
    
    # 价格和关键指标
    cols = st.columns([2, 1, 1, 1, 1])
    
    with cols[0]:
        if quote:
            price = quote.get('c', 0)
            change = quote.get('d', 0)
            change_pct = quote.get('dp', 0)
            color_class = "price-up" if change >= 0 else "price-down"
            arrow = "▲" if change >= 0 else "▼"
            
            st.markdown(f"""
            <div style="text-align: center;">
                <div class="price-large">${price:.2f}</div>
                <div class="{color_class}">{arrow} {abs(change):.2f} ({change_pct:+.2f}%)</div>
            </div>
            """, unsafe_allow_html=True)
    
    with cols[1]:
        if quote:
            st.metric("Open", f"${quote.get('o', 0):.2f}")
            st.metric("Prev Close", f"${quote.get('pc', 0):.2f}")
    
    with cols[2]:
        if quote:
            st.metric("High", f"${quote.get('h', 0):.2f}")
            st.metric("Low", f"${quote.get('l', 0):.2f}")
    
    with cols[3]:
        if financials and 'metric' in financials:
            metrics = financials['metric']
            pe = metrics.get('peBasicExclExtraTTM')
            market_cap = metrics.get('marketCapitalization')
            st.metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A")
            if isinstance(market_cap, (int, float)):
                cap_str = f"${market_cap/1000:.2f}B" if market_cap >= 1000 else f"${market_cap:.0f}M"
                st.metric("Market Cap", cap_str)
    
    with cols[4]:
        if profile:
            st.metric("Employees", f"{profile.get('employeeTotal', 0):,}" if profile.get('employeeTotal') else "N/A")
            st.metric("IPO Date", profile.get('ipo', 'N/A'))
    
    st.markdown("---")
    
    # 图表区域 - 左：主图，右：技术分析
    col_chart, col_tech = st.columns([3, 2])
    
    with col_chart:
        st.markdown("### 📊 Chart")
        chart_type = st.selectbox("Chart Type", ["Candlestick", "Baseline"], label_visibility="collapsed")
        
        if chart_type == "Candlestick":
            tradingview_widget('advanced_chart', symbol, height=500)
        else:
            tradingview_widget('baseline', symbol, height=500)
    
    with col_tech:
        st.markdown("### 📈 Technical Analysis")
        tradingview_widget('technical', symbol, height=250)
        
        st.markdown("### 🏢 Company Profile")
        if profile:
            st.write(f"**Industry:** {profile.get('finnhubIndustry', 'N/A')}")
            st.write(f"**Sector:** {profile.get('sector', 'N/A')}")
            st.write(f"**Country:** {profile.get('country', 'N/A')}")
            st.write(f"**Currency:** {profile.get('currency', 'N/A')}")
            if profile.get('weburl'):
                st.write(f"**Website:** [{profile['weburl']}]({profile['weburl']})")
            if profile.get('phone'):
                st.write(f"**Phone:** {profile['phone']}")
    
    st.markdown("---")
    
    # 财务数据
    st.markdown("### 💰 Financials")
    tradingview_widget('financials', symbol, height=500)
    
    st.markdown("---")
    
    # 公司新闻
    st.markdown(f"### 📰 {symbol} News")
    company_news = get_company_news(symbol)
    
    if company_news:
        for item in company_news[:10]:
            with st.expander(f"📰 {item.get('headline', 'No Title')}"):
                st.write(item.get('summary', 'No summary available.'))
                if item.get('url'):
                    st.write(f"[Read more]({item['url']})")
                st.caption(f"📌 {item.get('source', 'Unknown')} | {datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No recent news for this stock.")

# ========== 页脚 ==========
st.markdown("---")
st.caption("""
🚀 **OpenStock** — Built openly, for everyone, forever free.

Data provided by [Finnhub](https://finnhub.io) and [TradingView](https://tradingview.com).
Not financial advice. Market data may be delayed.
""")
