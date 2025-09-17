# Hikyuu框架API使用指南

**文档创建时间**: 2025年8月25日  
**分析工具**: DeepWiki MCP Server  
**框架版本**: fasiondog/hikyuu (GitHub)

## 目录

1. [框架初始化](#框架初始化)
2. [数据获取API](#数据获取api)
3. [技术指标API](#技术指标api)
4. [交易系统API](#交易系统api)
5. [投资组合管理API](#投资组合管理api)
6. [策略框架API](#策略框架api)
7. [绩效分析API](#绩效分析api)
8. [实用工具API](#实用工具api)
9. [完整示例](#完整示例)

## 框架初始化

### 基础初始化

```python
from hikyuu import *

# 简单初始化
load_hikyuu()
```

### 定制化初始化

```python
from hikyuu import *

# 定制化配置选项
options = {
    "stock_list": ["sh000001", "sz000001"],  # 指定加载的股票列表
    "ktype_list": ["day", "min"],            # 指定K线类型
    "preload_num": {                         # 预加载数量配置
        "day_max": 100000,
        "min_max": 50000
    },
    "load_history_finance": False,           # 是否加载历史财务数据
    "load_weight": False,                    # 是否加载权息数据
    "start_spot": False,                     # 是否启动实时数据
    "spot_worker_num": 1,                    # 实时数据工作线程数
}

# 使用定制化配置初始化
load_hikyuu(**options)
```

### 获取StockManager实例

```python
# 获取全局StockManager实例
sm = StockManager.instance()

# 或者直接使用全局变量sm（在load_hikyuu后自动创建）
print(len(sm))  # 显示股票数量
```

## 数据获取API

### 基于数据库结构的数据访问

```python
# 基于数据库结构的股票查询
# 参考：hku_base.stock表和hku_base.market表

# 获取所有可用市场
markets = sm.get_market_info()
print("可用市场:")
for market in markets:
    print(f"  {market.market} - {market.name}")

# 根据股票类型获取股票
# 参考：hku_base.stocktypeinfo表的类型定义
def get_stocks_by_type(stock_type):
    """根据股票类型获取股票列表
    
    Args:
        stock_type: 股票类型
            1: A股, 2: 指数, 3: B股, 4: 基金, 5: ETF, 
            6: 国债, 7: 其他债券, 8: 创业板, 9: 科创板, 11: 北交所
    """
    stocks = []
    for i in range(len(sm)):
        stock = sm[i]
        if stock.type == stock_type and stock.valid:
            stocks.append(stock)
    return stocks

# 获取A股列表
a_stocks = get_stocks_by_type(1)
print(f"A股数量: {len(a_stocks)}")

# 获取ETF列表  
etf_stocks = get_stocks_by_type(5)
print(f"ETF数量: {len(etf_stocks)}")

# 基于代码前缀规则获取股票
# 参考：hku_base.coderuletype表的前缀规则
def get_stocks_by_code_prefix(prefix):
    """根据代码前缀获取股票"""
    stocks = []
    for i in range(len(sm)):
        stock = sm[i]
        if stock.market_code.startswith(prefix) and stock.valid:
            stocks.append(stock)
    return stocks

# 获取科创板股票（688开头）
sci_tech_stocks = get_stocks_by_code_prefix("sh688")
print(f"科创板股票数量: {len(sci_tech_stocks)}")

# 获取创业板股票（300/301/302开头）
gem_stocks = (get_stocks_by_code_prefix("sz300") + 
              get_stocks_by_code_prefix("sz301") + 
              get_stocks_by_code_prefix("sz302"))
print(f"创业板股票数量: {len(gem_stocks)}")
```

### 获取股票对象

```python
# 通过市场代码获取股票
stk = sm.getStock("sh000001")  # 上证指数
stk = sm["sz000001"]           # 平安银行（简化写法）

# 检查股票有效性和详细信息
if stk.valid:
    print(f"股票名称: {stk.name}")
    print(f"市场代码: {stk.market_code}")
    print(f"股票类型: {stk.type}")
    print(f"所属市场: {stk.market}")
    
    # 获取股票的交易规则信息
    # 基于stocktypeinfo表的配置
    type_info = stk.getStockTypeInfo()
    if type_info:
        print(f"价格精度: {type_info.precision}")
        print(f"最小变动单位: {type_info.tick}")
        print(f"最小交易数量: {type_info.minTradeNumber}")
        print(f"最大交易数量: {type_info.maxTradeNumber}")
```

### 数据完整性检查

```python
def check_data_availability(stock):
    """检查股票数据的可用性和完整性"""
    
    # 检查基本信息
    if not stock.valid:
        return False, "股票无效"
    
    # 检查K线数据可用性
    kdata = stock.getKData(Query(-10))
    if len(kdata) == 0:
        return False, "无K线数据"
    
    # 检查数据更新时间
    latest_record = stock.getKRecord(-1)
    if latest_record.datetime == Datetime():
        return False, "数据未更新"
    
    # 检查数据连续性
    recent_data = stock.getKData(Query(-5))
    if len(recent_data) < 5:
        return False, "数据不足"
    
    return True, "数据完整"

# 使用示例
stk = sm["sz000001"]
is_valid, message = check_data_availability(stk)
print(f"数据检查结果: {message}")
```

### 高级股票筛选和分组

```python
# 按市场分组获取股票
def get_stocks_by_market():
    """按市场分组获取股票"""
    markets = {}
    
    for i in range(len(sm)):
        stock = sm[i]
        if stock.valid:
            market = stock.market
            if market not in markets:
                markets[market] = []
            markets[market].append(stock)
    
    return markets

# 按股票类型筛选
def get_stocks_by_type(stock_type):
    """按股票类型筛选
    
    Args:
        stock_type: 股票类型 (1-A股, 2-指数, 3-B股, 4-基金, 5-ETF等)
    """
    stocks = []
    for i in range(len(sm)):
        stock = sm[i]
        if stock.valid and stock.type == stock_type:
            stocks.append(stock)
    return stocks

# 获取活跃股票（有足够历史数据）
def get_active_stocks(min_days=100):
    """获取有足够历史数据的活跃股票"""
    active_stocks = []
    
    for i in range(len(sm)):
        stock = sm[i]
        if not stock.valid:
            continue
            
        # 检查数据量
        kdata = stock.getKData(Query(-min_days))
        if len(kdata) >= min_days * 0.8:  # 至少80%的数据
            active_stocks.append(stock)
    
    return active_stocks

# 使用示例
all_markets = get_stocks_by_market()
for market, stocks in all_markets.items():
    print(f"{market}市场: {len(stocks)}只股票")

a_stocks = get_stocks_by_type(1)  # A股
etf_stocks = get_stocks_by_type(5)  # ETF
print(f"A股数量: {len(a_stocks)}, ETF数量: {len(etf_stocks)}")

active_stocks = get_active_stocks(100)
print(f"活跃股票数量: {len(active_stocks)}")
```

### 财务数据访问

```python
# 获取股票基本信息
def get_stock_basic_info(stock):
    """获取股票基本信息"""
    info = {
        'code': stock.market_code,
        'name': stock.name,
        'market': stock.market,
        'type': stock.type,
        'valid': stock.valid,
        'start_date': stock.startDatetime,
        'last_date': stock.lastDatetime
    }
    
    # 获取股本信息（如果可用）
    try:
        info['total_count'] = stock.getCount()
        info['market_value'] = stock.getMarketValue()
    except:
        info['total_count'] = None
        info['market_value'] = None
    
    return info

# 批量获取股票信息
def batch_get_stock_info(stock_codes):
    """批量获取股票信息"""
    results = []
    
    for code in stock_codes:
        stock = sm[code]
        if stock.valid:
            info = get_stock_basic_info(stock)
            results.append(info)
    
    return results

# 使用示例
sample_codes = ['sz000001', 'sh600000', 'sz000002', 'sh000001']
stock_infos = batch_get_stock_info(sample_codes)

for info in stock_infos:
    print(f"{info['name']} ({info['code']}): {info['market']}市场")
```

### 实时数据处理

```python
# 实时数据监控
def monitor_realtime_data(stock_codes, callback=None):
    """监控实时数据更新"""
    
    stocks = [sm[code] for code in stock_codes if sm[code].valid]
    
    print(f"开始监控 {len(stocks)} 只股票的实时数据...")
    
    for stock in stocks:
        try:
            # 获取最新实时数据
            spot = stock.realtimeUpdate()
            
            if spot:
                data = {
                    'code': stock.market_code,
                    'name': stock.name,
                    'price': spot.close,
                    'volume': spot.volume,
                    'amount': spot.amount,
                    'datetime': spot.datetime
                }
                
                # 计算涨跌幅
                yesterday_close = stock.getKRecord(-2).close if len(stock.getKData(Query(-2))) >= 2 else spot.close
                if yesterday_close > 0:
                    change_pct = (spot.close - yesterday_close) / yesterday_close
                    data['change_pct'] = change_pct
                
                if callback:
                    callback(data)
                else:
                    print(f"{data['name']}: ¥{data['price']:.2f} "
                          f"({data['change_pct']:.2%}) "
                          f"成交量: {data['volume']}")
                          
        except Exception as e:
            print(f"获取 {stock.market_code} 实时数据失败: {e}")

# 自定义回调函数
def price_alert_callback(data):
    """价格预警回调"""
    if abs(data.get('change_pct', 0)) > 0.05:  # 涨跌超过5%
        print(f"⚠️  {data['name']} 异动: {data['change_pct']:.2%}")

# 使用示例
monitor_codes = ['sz000001', 'sh600000', 'sz000002']
monitor_realtime_data(monitor_codes, price_alert_callback)
```

### 交易日历和时间处理

```python
# 交易日历工具函数
def get_trading_calendar_info(start_date=None, end_date=None):
    """获取交易日历信息"""
    
    if start_date is None:
        start_date = Datetime.today() - TimeDelta(365)  # 默认一年前
    if end_date is None:
        end_date = Datetime.today()
    
    query = Query(start_date, end_date)
    trading_dates = sm.get_trading_calendar(query)
    
    info = {
        'total_days': len(trading_dates),
        'start_date': trading_dates[0] if trading_dates else None,
        'end_date': trading_dates[-1] if trading_dates else None,
        'trading_dates': trading_dates
    }
    
    return info

def is_market_open():
    """检查市场是否开盘"""
    now = Datetime.now()
    
    # 检查是否为交易日
    if not sm.is_trading_date(now):
        return False, "非交易日"
    
    # 检查交易时间（简化版本，不考虑午休）
    current_time = now.hour * 100 + now.minute
    
    # A股交易时间：9:30-11:30, 13:00-15:00
    morning_open = 930
    morning_close = 1130
    afternoon_open = 1300
    afternoon_close = 1500
    
    if morning_open <= current_time <= morning_close:
        return True, "上午交易时段"
    elif afternoon_open <= current_time <= afternoon_close:
        return True, "下午交易时段"
    else:
        return False, "非交易时间"

def get_next_trading_day(date=None):
    """获取下一个交易日"""
    if date is None:
        date = Datetime.today()
    
    return sm.get_next_trading_date(date)

# 使用示例
calendar_info = get_trading_calendar_info()
print(f"最近一年交易日数: {calendar_info['total_days']}")

is_open, status = is_market_open()
print(f"市场状态: {status}")

next_day = get_next_trading_day()
print(f"下一个交易日: {next_day}")
```

### 获取K线数据

```python
# 创建查询条件
query = Query(-100)                                    # 最近100条记录
query = Query(Datetime(20240101), Datetime(20241201)) # 指定日期范围
query = Query(-100, Query.MIN)                        # 最近100条分钟线

# 获取K线数据
kdata = stk.getKData(query)

# 访问K线数据
for k in kdata:
    print(f"日期: {k.datetime}, 开盘: {k.open}, 收盘: {k.close}")

# 获取最新K线记录
latest = stk.getKRecord(-1)  # 最新一条记录
```

### 获取实时数据

```python
# 获取最新实时数据
spot = stk.realtimeUpdate()
if spot:
    print(f"最新价格: {spot.close}")
    print(f"成交量: {spot.volume}")
```

## 技术指标API

### 基础市场数据指标

```python
# 获取OHLCV数据指标
C = CLOSE()     # 收盘价
O = OPEN()      # 开盘价
H = HIGH()      # 最高价
L = LOW()       # 最低价
V = VOL()       # 成交量
A = AMO()       # 成交金额

# 设置指标上下文
C.set_context(sm['sz000001'], Query(-100))
```

### 移动平均指标

```python
# 简单移动平均
ma5 = MA(CLOSE(), 5)    # 5日移动平均
ma10 = MA(C, 10)        # 10日移动平均

# 指数移动平均
ema12 = EMA(CLOSE(), 12)   # 12日指数移动平均
ema26 = EMA(CLOSE(), 26)   # 26日指数移动平均

# 其他移动平均
sma = SMA(CLOSE(), 10, 1)        # 修正移动平均
wma = WMA(CLOSE(), 10)           # 加权移动平均
ama = AMA(CLOSE(), 10)           # 自适应移动平均
```

### 技术分析指标

```python
# MACD指标（修正后的正确访问方式）
macd = MACD(CLOSE(), 12, 26, 9)
# 正确的MACD访问方式
if len(macd) > 0:
    dif = macd.get_result(0)         # DIF线
    dea = macd.get_result(1)         # DEA线  
    histogram = macd.get_result(2)   # 柱状图

# RSI相对强弱指数
rsi = RSI(CLOSE(), 14)

# 布林带
upper, middle, lower = BOLL(CLOSE(), 20, 2)

# ATR平均真实波幅
atr = ATR(14)

# 最高价最低价
hhv = HHV(HIGH(), 20)    # 20日内最高价
llv = LLV(LOW(), 20)     # 20日内最低价
```

### 数学和逻辑指标

```python
# 数学运算
abs_val = ABS(CLOSE() - OPEN())      # 绝对值
log_val = LOG(CLOSE())               # 对数
sqrt_val = SQRT(CLOSE())             # 平方根

# 逻辑判断
cross_up = CROSS(ma5, ma10)          # 金叉信号
cross_down = CROSS(ma10, ma5)        # 死叉信号
between = BETWEEN(RSI(14), 30, 70)   # 介于30和70之间

# 条件判断
signal = IF(RSI(14) < 30, 1, 0)      # RSI小于30时为1，否则为0
```

### 自定义指标

```python
# 通过组合创建自定义指标
def custom_signal():
    """自定义双线交叉信号"""
    ma_fast = MA(CLOSE(), 5)
    ma_slow = MA(CLOSE(), 20)
    return CROSS(ma_fast, ma_slow)

# 使用自定义指标
signal = custom_signal()
signal.set_context(sm['sz000001'], Query(-100))
```

## 交易系统API

### 创建交易账户

```python
# 创建模拟交易账户
tm = crtTM(init_cash=300000)          # 初始资金30万
tm = crtTM(
    init_cash=1000000,                # 初始资金
    cost_func=TC_FixedA(5),           # 交易成本函数
    name="我的账户"                    # 账户名称
)
```

### 创建信号指示器

```python
# 基于EMA交叉的信号指示器
sg = SG_Flex(EMA(CLOSE(), 5), slow_n=10)

# 基于布尔条件的信号指示器
condition = CROSS(MA(CLOSE(), 5), MA(CLOSE(), 20))
sg = SG_Bool(condition)

# 双线交叉信号指示器
sg = SG_Cross(MA(CLOSE(), 5), MA(CLOSE(), 20))
```

### 创建资金管理策略

```python
# 固定数量买入
mm = MM_FixedCount(1000)              # 每次买入1000股

# 固定比例资金投入
mm = MM_FixedPercent(0.1)             # 每次投入10%资金

# 固定风险资金管理
mm = MM_FixedRisk(0.02)               # 每次风险控制在2%
```

### 创建止损止盈策略

```python
# 固定比例止损
st = ST_FixedPercent(0.05)            # 5%止损

# ATR止损
st = ST_Atr(14, 3.0)                  # 基于14日ATR的3倍止损

# 固定比例止盈（修正：使用ST_而非TP_前缀）
tp = ST_FixedPercent(0.2)             # 20%止盈
```

### 创建交易系统

```python
# 创建简单交易系统
sys = SYS_Simple(
    tm=tm,                            # 交易管理器
    sg=sg,                            # 信号指示器
    mm=mm,                            # 资金管理策略
    st=st,                            # 止损策略
    tp=tp                             # 止盈策略
)

# 设置系统参数
sys.setParam("buy_delay", False)      # 是否延迟买入
sys.setParam("sell_delay", False)     # 是否延迟卖出

# 运行系统回测
sys.run(sm['sz000001'], Query(-252))  # 最近一年数据回测
```

## 投资组合管理API

### 创建投资组合

```python
# 创建系统选择器
stocks = [sm['sz000001'], sm['sh600000'], sm['sz000002']]
se = SE_Fixed(stocks, sys)            # 固定选择器

# 创建资产分配算法
af = AF_EqualWeight()                 # 等权重分配
af = AF_FixedWeight([0.4, 0.3, 0.3])  # 固定权重分配

# 创建投资组合账户
pf_tm = crtTM(init_cash=2000000)      # 200万初始资金

# 创建投资组合
pf = PF_Simple(
    tm=pf_tm,                         # 交易管理器
    se=se,                            # 系统选择器
    af=af,                            # 资产分配器
    adjust_cycle=1,                   # 调仓周期
    adjust_mode="day"                 # 调仓模式
)

# 运行投资组合回测
pf.run(Query(-500))                   # 最近500个交易日
```

### 投资组合调仓模式

```python
# 不同调仓模式
pf_daily = PF_Simple(tm=tm, se=se, af=af, adjust_mode="day", adjust_cycle=5)
pf_weekly = PF_Simple(tm=tm, se=se, af=af, adjust_mode="week", adjust_cycle=1)
pf_monthly = PF_Simple(tm=tm, se=se, af=af, adjust_mode="month", adjust_cycle=1)
```

## 策略框架API

### 创建Strategy实例

```python
# 创建策略实例
strategy = Strategy(
    code_list=['sh600000', 'sz000001'],   # 股票代码列表
    ktype_list=[Query.MIN, Query.DAY]     # K线类型列表
)
```

### 设置策略回调函数

```python
def on_change_callback(stg: Strategy, stk: Stock, spot: SpotRecord):
    """数据更新回调"""
    print(f"[数据更新]: {stk.market_code} {stk.name} 最新价格: {spot.close}")

def daily_task(stg: Strategy):
    """每日任务"""
    print(f"[每日任务] 当前时间: {stg.now()}")
    
    # 获取股票数据
    stk = sm['sz000001']
    kdata = stg.get_kdata(stk, Query(-30, Query.DAY))
    
    # 计算指标
    ma5 = MA(CLOSE(), 5)(kdata)
    ma20 = MA(CLOSE(), 20)(kdata)
    
    # 交易逻辑
    if ma5[-1] > ma20[-1] and not stg.tm.have(stk):
        stg.buy(stk, kdata[-1].close, 100)
    elif ma5[-1] < ma20[-1] and stg.tm.have(stk):
        stg.sell(stk, kdata[-1].close, 100)

def at_time_task(stg: Strategy):
    """定时任务"""
    print(f"[定时任务] 执行时间: {stg.now()}")

# 设置回调函数
strategy.on_change(on_change_callback)
strategy.run_daily(daily_task, TimeDelta(0, 0, 5))        # 每5分钟执行
strategy.run_daily_at(at_time_task, TimeDelta(0, 14, 55)) # 每日14:55执行

# 启动策略
strategy.start()
```

### 事件驱动回测

```python
# 推荐用法：on_bar 只接受一个参数 krecord，回测区间需在授权范围内
def on_bar(krecord):
    """K线数据回调函数"""
    stk = sm['sz000001']
    kdata = stk.getKData(Query(-30, Query.MIN))
    if len(kdata) < 30:
        return
    try:
        close = CLOSE()
        close.set_context(stk, Query(-30, Query.MIN))
        ma5 = MA(close, 5)
        ma10 = MA(close, 10)
        if len(ma5) > 0 and len(ma10) > 0:
            ma5_val = float(ma5[-1])
            ma10_val = float(ma10[-1])
            # 交易逻辑
            # 需获取当前持仓状态
            # tm.have(stk) 判断是否持仓
            if ma5_val > ma10_val and not tm.have(stk):
                tm.buy(stk, krecord.close, 100)
                print(f"{krecord.datetime}: 金叉买入 价格={krecord.close:.2f}")
            elif ma5_val < ma10_val and tm.have(stk):
                tm.sell(stk, krecord.close, 100)
                print(f"{krecord.datetime}: 死叉卖出 价格={krecord.close:.2f}")
    except Exception as e:
        print(f"事件驱动回测中指标计算错误: {e}")

# 执行事件驱动回测（区间需在授权范围内）
start_date = Datetime(2019, 1, 1)
end_date = Datetime(2019, 6, 30)
tm = crtTM(init_cash=300000)

backtest(on_bar, tm, start_date, end_date, Query.MIN)
```

## 绩效分析API

### TradeManager绩效分析

```python
# 获取绩效报告
performance = tm.get_performance(Datetime.now(), Query.DAY)
print(performance.report())  # 打印详细绩效报告

# 或者直接使用performance方法
tm.performance(Query(start_date, end_date, Query.DAY))

# 获取各种曲线数据
dates = sm.get_trading_calendar(Query(-252))  # 获取交易日历

# 资产净值曲线
funds_curve = tm.get_funds_curve(dates)

# 收益曲线
profit_curve = tm.get_profit_curve(dates)

# 累积收益率曲线
profit_cum_curve = tm.get_profit_cum_change_curve(dates)

# 绘制曲线
PRICELIST(funds_curve).plot()
```

### 交易记录分析

```python
# 获取所有交易记录
trade_list = tm.get_trade_list()

# 获取指定日期范围的交易记录
trade_list = tm.get_trade_list(
    Datetime(2024, 1, 1), 
    Datetime(2024, 12, 31)
)

# 获取当前持仓
positions = tm.get_position_list()

# 获取历史持仓（已平仓）
history_positions = tm.get_history_position_list()

# 转换为DataFrame进行分析
import pandas as pd
df_trades = pd.DataFrame([{
    'datetime': trade.datetime,
    'stock': trade.stock.market_code,
    'business': trade.business,
    'price': trade.realPrice,
    'number': trade.number,
    'cost': trade.cost
} for trade in trade_list])

print(df_trades.head())
```

### 导出分析结果

```python
# 导出所有数据到CSV
tm.tocsv("./trade_analysis/")

# 这将创建以下文件：
# - trade_list.csv      # 交易记录
# - position_list.csv   # 当前持仓
# - history_position_list.csv  # 历史持仓
# - funds_curve.csv     # 资产净值曲线
```

### 绩效指标获取

```python
# 获取关键绩效指标
performance = tm.get_performance(Datetime.now(), Query.DAY)

# 通过字典方式访问指标
total_return = performance['总收益率']
annual_return = performance['年化收益率'] 
max_drawdown = performance['最大回撤']
sharpe_ratio = performance['夏普比率']

# 获取所有指标名称和值
names = performance.names()
values = performance.values()

for name, value in zip(names, values):
    print(f"{name}: {value}")
```

## 实用工具API

### 日期时间处理

```python
# 创建日期时间对象
dt = Datetime(2024, 1, 1)
dt = Datetime(202401010930)  # 2024年1月1日09:30
dt = Datetime.now()          # 当前时间
dt = Datetime.today()        # 今天日期

# 时间差对象
td = TimeDelta(days=1, hours=2, minutes=30)

# 日期运算
new_dt = dt + td
```

### 数据查询

```python
# Query对象创建
q1 = Query(-100)                    # 最近100条
q2 = Query(-100, Query.MIN)         # 最近100条分钟线
q3 = Query(Datetime(2024,1,1), Datetime(2024,12,31))  # 日期范围
q4 = Query(Datetime(2024,1,1), Datetime(2024,12,31), Query.DAY)  # 指定K线类型
```

### 选股函数

```python
# 基于条件选股
def select_stocks():
    # RSI超卖选股
    rsi_condition = RSI(CLOSE(), 14) < 30
    oversold_stocks = select(rsi_condition)
    
    # 均线多头排列选股
    ma5 = MA(CLOSE(), 5)
    ma10 = MA(CLOSE(), 10) 
    ma20 = MA(CLOSE(), 20)
    bullish_condition = (ma5 > ma10) & (ma10 > ma20)
    bullish_stocks = select(bullish_condition)
    
    return oversold_stocks, bullish_stocks

oversold, bullish = select_stocks()
print(f"超卖股票数量: {len(oversold)}")
print(f"多头排列股票数量: {len(bullish)}")
```

### 数据可视化

```python
# 绘制K线图
kdata = sm['sz000001'].getKData(Query(-100))
kdata.plot()

# 绘制指标
ma5 = MA(CLOSE(), 5)
ma10 = MA(CLOSE(), 10)
ma5.set_context(sm['sz000001'], Query(-100))
ma10.set_context(sm['sz000001'], Query(-100))

ma5.plot()
ma10.plot()

# 绘制价格序列
prices = [k.close for k in kdata]
price_list = PRICELIST(prices)
price_list.plot()
```

### 高级选股策略

```python
# 基于技术指标的选股
def technical_stock_selection():
    """基于技术指标的选股策略"""
    
    # 定义选股条件
    def check_bullish_signals(stock):
        """检查看涨信号"""
        try:
            # 获取最近30天数据
            kdata = stock.getKData(Query(-30))
            if len(kdata) < 30:
                return False
                
            # 设置指标上下文
            query = Query(-30)
            
            # 均线多头排列
            ma5 = MA(CLOSE(), 5)
            ma10 = MA(CLOSE(), 10)
            ma20 = MA(CLOSE(), 20)
            
            ma5.set_context(stock, query)
            ma10.set_context(stock, query)
            ma20.set_context(stock, query)
            
            # 检查最新均线排列
            if len(ma5) > 0 and len(ma10) > 0 and len(ma20) > 0:
                latest_ma5 = ma5[-1]
                latest_ma10 = ma10[-1]
                latest_ma20 = ma20[-1]
                
                if latest_ma5 > latest_ma10 > latest_ma20:
                    # RSI不超买
                    rsi = RSI(CLOSE(), 14)
                    rsi.set_context(stock, query)
                    
                    if len(rsi) > 0 and 30 < rsi[-1] < 70:
                        return True
            
            return False
            
        except Exception:
            return False
    
    # 筛选股票
    selected_stocks = []
    active_stocks = get_active_stocks(50)  # 获取有足够数据的股票
    
    print(f"开始筛选，候选股票数量: {len(active_stocks)}")
    
    for i, stock in enumerate(active_stocks[:100]):  # 限制检查数量以提高速度
        if check_bullish_signals(stock):
            selected_stocks.append(stock)
            
        if (i + 1) % 20 == 0:
            print(f"已检查 {i + 1} 只股票，筛选出 {len(selected_stocks)} 只")
    
    return selected_stocks

# 基于量价关系的选股
def volume_price_selection():
    """基于量价关系的选股"""
    
    def check_volume_breakout(stock):
        """检查量价突破"""
        try:
            kdata = stock.getKData(Query(-20))
            if len(kdata) < 20:
                return False
            
            # 最近5天平均成交量
            recent_volume = sum(k.volume for k in kdata[-5:]) / 5
            # 前15天平均成交量
            prev_volume = sum(k.volume for k in kdata[-20:-5]) / 15
            
            # 成交量放大
            volume_ratio = recent_volume / prev_volume if prev_volume > 0 else 0
            
            # 价格上涨
            price_change = (kdata[-1].close - kdata[-5].close) / kdata[-5].close
            
            return volume_ratio > 1.5 and price_change > 0.03  # 量增价涨
            
        except Exception:
            return False
    
    active_stocks = get_active_stocks(30)
    breakout_stocks = []
    
    for stock in active_stocks[:50]:  # 限制检查数量
        if check_volume_breakout(stock):
            breakout_stocks.append(stock)
    
    return breakout_stocks

# 执行选股
print("=== 技术指标选股 ===")
tech_stocks = technical_stock_selection()
print(f"技术面看涨股票: {len(tech_stocks)}只")
for stock in tech_stocks[:5]:  # 显示前5只
    print(f"  {stock.name} ({stock.market_code})")

print("\n=== 量价突破选股 ===")
volume_stocks = volume_price_selection()
print(f"量价突破股票: {len(volume_stocks)}只")
for stock in volume_stocks[:5]:  # 显示前5只
    print(f"  {stock.name} ({stock.market_code})")
```

### 风险管理工具

```python
# 投资组合风险分析
def portfolio_risk_analysis(stock_codes, weights=None):
    """投资组合风险分析"""
    
    if weights is None:
        weights = [1.0/len(stock_codes)] * len(stock_codes)  # 等权重
    
    # 获取股票数据
    stocks_data = []
    for code in stock_codes:
        stock = sm[code]
        if stock.valid:
            kdata = stock.getKData(Query(-252))  # 一年数据
            if len(kdata) >= 200:  # 确保足够数据
                returns = []
                for i in range(1, len(kdata)):
                    ret = (kdata[i].close - kdata[i-1].close) / kdata[i-1].close
                    returns.append(ret)
                stocks_data.append({
                    'stock': stock,
                    'returns': returns
                })
    
    if len(stocks_data) < 2:
        print("数据不足，无法进行风险分析")
        return
    
    print(f"=== 投资组合风险分析 ({len(stocks_data)}只股票) ===")
    
    # 计算个股风险指标
    for i, data in enumerate(stocks_data):
        returns = data['returns']
        stock = data['stock']
        
        # 计算统计指标
        import statistics
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        # 计算最大回撤
        cumulative = [1]
        for ret in returns:
            cumulative.append(cumulative[-1] * (1 + ret))
        
        peak = cumulative[0]
        max_drawdown = 0
        for value in cumulative:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        print(f"{stock.name}:")
        print(f"  年化收益率: {mean_return * 252:.2%}")
        print(f"  年化波动率: {std_return * (252**0.5):.2%}")
        print(f"  最大回撤: {max_drawdown:.2%}")
        print(f"  夏普比率: {(mean_return * 252) / (std_return * (252**0.5)):.2f}")

# 动态止损策略
class DynamicStopLoss:
    """动态止损策略"""
    
    def __init__(self, initial_stop_pct=0.05, trailing_pct=0.03):
        self.initial_stop_pct = initial_stop_pct  # 初始止损比例
        self.trailing_pct = trailing_pct          # 移动止损比例
        self.positions = {}                       # 持仓记录
    
    def add_position(self, stock_code, entry_price):
        """添加持仓"""
        self.positions[stock_code] = {
            'entry_price': entry_price,
            'stop_price': entry_price * (1 - self.initial_stop_pct),
            'highest_price': entry_price
        }
    
    def update_stop_loss(self, stock_code, current_price):
        """更新止损价格"""
        if stock_code not in self.positions:
            return None
        
        position = self.positions[stock_code]
        
        # 更新最高价
        if current_price > position['highest_price']:
            position['highest_price'] = current_price
            # 更新移动止损价格
            new_stop = current_price * (1 - self.trailing_pct)
            if new_stop > position['stop_price']:
                position['stop_price'] = new_stop
        
        return position['stop_price']
    
    def should_stop_loss(self, stock_code, current_price):
        """判断是否应该止损"""
        if stock_code not in self.positions:
            return False
        
        stop_price = self.update_stop_loss(stock_code, current_price)
        return current_price <= stop_price

# 使用风险管理工具
sample_portfolio = ['sz000001', 'sh600000', 'sz000002']
portfolio_risk_analysis(sample_portfolio)

# 动态止损示例
stop_loss = DynamicStopLoss(initial_stop_pct=0.08, trailing_pct=0.05)
stop_loss.add_position('sz000001', 10.0)

# 模拟价格变化
price_changes = [10.5, 11.0, 10.8, 11.2, 10.9, 10.3]
for price in price_changes:
    stop_price = stop_loss.update_stop_loss('sz000001', price)
    should_stop = stop_loss.should_stop_loss('sz000001', price)
    print(f"价格: {price:.2f}, 止损价: {stop_price:.2f}, 是否止损: {should_stop}")
```

### 策略回测优化

```python
# 参数优化工具
def optimize_ma_strategy(stock, param_ranges):
    """优化移动平均策略参数"""
    
    results = []
    
    # 遍历参数组合
    for fast_ma in param_ranges['fast_ma']:
        for slow_ma in param_ranges['slow_ma']:
            if fast_ma >= slow_ma:
                continue
                
            try:
                # 创建交易系统
                tm = crtTM(init_cash=100000)
                sg = SG_Cross(MA(CLOSE(), fast_ma), MA(CLOSE(), slow_ma))
                mm = MM_FixedPercent(0.8)
                st = ST_FixedPercent(0.05)
                
                sys = SYS_Simple(tm=tm, sg=sg, mm=mm, st=st)
                
                # 运行回测
                query = Query(-252)  # 一年数据
                sys.run(stock, query)
                
                # 获取绩效
                performance = tm.get_performance(Datetime.now(), Query.DAY)
                
                # 提取关键指标
                total_return = 0
                max_drawdown = 0
                trade_count = len(tm.get_trade_list())
                
                # 尝试获取收益率和回撤
                try:
                    names = performance.names()
                    values = performance.values()
                    perf_dict = dict(zip(names, values))
                    
                    total_return = perf_dict.get('总收益率', 0)
                    max_drawdown = perf_dict.get('最大回撤', 0)
                except:
                    pass
                
                results.append({
                    'fast_ma': fast_ma,
                    'slow_ma': slow_ma,
                    'total_return': total_return,
                    'max_drawdown': max_drawdown,
                    'trade_count': trade_count,
                    'profit_factor': total_return / abs(max_drawdown) if max_drawdown != 0 else 0
                })
                
            except Exception as e:
                print(f"参数组合 ({fast_ma}, {slow_ma}) 测试失败: {e}")
                continue
    
    # 按收益率排序
    results.sort(key=lambda x: x['total_return'], reverse=True)
    
    return results

# 批量回测工具
def batch_backtest(stock_codes, strategy_func, **kwargs):
    """批量回测多只股票"""
    
    results = []
    
    for code in stock_codes:
        stock = sm[code]
        if not stock.valid:
            continue
            
        try:
            result = strategy_func(stock, **kwargs)
            result['stock_code'] = code
            result['stock_name'] = stock.name
            results.append(result)
            
            print(f"完成 {stock.name} ({code}) 回测")
            
        except Exception as e:
            print(f"{code} 回测失败: {e}")
            continue
    
    return results

# 策略组合测试
def strategy_combination_test(stock):
    """测试策略组合效果"""
    
    strategies = []
    
    # 策略1: 短期均线策略
    tm1 = crtTM(init_cash=100000)
    sg1 = SG_Cross(MA(CLOSE(), 5), MA(CLOSE(), 20))
    sys1 = SYS_Simple(tm=tm1, sg=sg1, mm=MM_FixedPercent(0.5))
    
    # 策略2: 长期均线策略
    tm2 = crtTM(init_cash=100000)
    sg2 = SG_Cross(MA(CLOSE(), 20), MA(CLOSE(), 60))
    sys2 = SYS_Simple(tm=tm2, sg=sg2, mm=MM_FixedPercent(0.5))
    
    # 策略3: RSI策略
    tm3 = crtTM(init_cash=100000)
    rsi_condition = (RSI(CLOSE(), 14) < 30) & (RSI(CLOSE(), 14) > RSI(CLOSE(), 14).delay(1))
    sg3 = SG_Bool(rsi_condition)
    sys3 = SYS_Simple(tm=tm3, sg=sg3, mm=MM_FixedPercent(0.3))
    
    strategies = [
        ('短期均线策略', sys1),
        ('长期均线策略', sys2),
        ('RSI策略', sys3)
    ]
    
    query = Query(-252)
    
    print(f"=== {stock.name} 策略组合测试 ===")
    
    for name, strategy in strategies:
        try:
            strategy.run(stock, query)
            tm = strategy.tm
            
            # 获取交易统计
            trades = tm.get_trade_list()
            positions = tm.get_history_position_list()
            
            print(f"\n{name}:")
            print(f"  交易次数: {len(trades)}")
            print(f"  持仓次数: {len(positions)}")
            print(f"  最终资金: {tm.currentCash:.2f}")
            
        except Exception as e:
            print(f"{name} 测试失败: {e}")

# 使用优化工具
stock = sm['sz000001']

# 参数优化
param_ranges = {
    'fast_ma': [5, 10, 15],
    'slow_ma': [20, 30, 40, 50]
}

print("=== 移动平均策略参数优化 ===")
optimization_results = optimize_ma_strategy(stock, param_ranges)

print("最优参数组合:")
for i, result in enumerate(optimization_results[:3]):  # 显示前3个
    print(f"第{i+1}名: MA({result['fast_ma']}, {result['slow_ma']}) "
          f"收益率: {result['total_return']:.2%} "
          f"最大回撤: {result['max_drawdown']:.2%}")

# 策略组合测试
strategy_combination_test(stock)
```

## 完整示例

### 双均线策略完整实现

```python
from hikyuu import *
import matplotlib.pyplot as plt

def dual_ma_strategy():
    """双均线交易策略完整示例"""
    
    # 1. 初始化框架
    load_hikyuu()
    
    # 2. 创建交易账户
    tm = crtTM(init_cash=1000000, name="双均线策略")
    
    # 3. 创建信号指示器（5日均线上穿20日均线买入，下穿卖出）
    sg = SG_Cross(MA(CLOSE(), 5), MA(CLOSE(), 20))
    
    # 4. 创建资金管理策略（每次投入20%资金）
    mm = MM_FixedPercent(0.2)
    
    # 5. 创建止损策略（5%止损）
    st = ST_FixedPercent(0.05)
    
    # 6. 创建交易系统
    sys = SYS_Simple(tm=tm, sg=sg, mm=mm, st=st)
    
    # 7. 运行回测
    stock = sm['sz000001']  # 平安银行
    query = Query(-252*2)   # 最近2年数据
    sys.run(stock, query)
    
    # 8. 绩效分析
    print("=== 绩效报告 ===")
    performance = tm.get_performance(Datetime.now(), Query.DAY)
    print(performance.report())
    
    # 9. 获取和绘制曲线
    dates = sm.get_trading_calendar(query)
    funds_curve = tm.get_funds_curve(dates)
    
    # 绘制资金曲线
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    PRICELIST(funds_curve).plot()
    plt.title('资金曲线')
    
    # 绘制股价和均线
    plt.subplot(2, 1, 2)
    kdata = stock.getKData(query)
    ma5 = MA(CLOSE(), 5)
    ma20 = MA(CLOSE(), 20)
    ma5.set_context(stock, query)
    ma20.set_context(stock, query)
    
    # 绘制K线和均线
    close_prices = [k.close for k in kdata]
    plt.plot(close_prices, label='收盘价')
    plt.plot(ma5.get_result_as_price_list(), label='MA5')
    plt.plot(ma20.get_result_as_price_list(), label='MA20')
    plt.legend()
    plt.title(f'{stock.name} 价格和均线')
    
    plt.tight_layout()
    plt.show()
    
    # 10. 导出详细数据
    tm.tocsv("./dual_ma_results/")
    print("详细数据已导出到 ./dual_ma_results/ 目录")

    return tm, sys

# 运行策略
if __name__ == "__main__":
    tm, sys = dual_ma_strategy()
```

### 多股票投资组合示例

```python
def multi_stock_portfolio():
    """多股票投资组合示例"""
    
    # 初始化
    load_hikyuu()
    
    # 选择股票池
    stock_codes = ['sz000001', 'sh600000', 'sz000002', 'sh600036', 'sz000858']
    stocks = [sm[code] for code in stock_codes if sm[code].valid]
    
    # 创建投资组合账户
    pf_tm = crtTM(init_cash=5000000, name="多股票组合")
    
    # 创建基础交易系统
    sg = SG_Cross(MA(CLOSE(), 10), MA(CLOSE(), 30))
    mm = MM_FixedPercent(0.8)  # 每只股票分配80%可用资金
    st = ST_FixedPercent(0.08)
    base_sys = SYS_Simple(sg=sg, mm=mm, st=st)
    
    # 创建系统选择器和资产分配器
    se = SE_Fixed(stocks, base_sys)
    af = AF_EqualWeight()  # 等权重分配
    
    # 创建投资组合
    pf = PF_Simple(
        tm=pf_tm,
        se=se,
        af=af,
        adjust_cycle=5,      # 每5个交易日调仓一次
        adjust_mode="day"
    )
    
    # 运行投资组合回测
    query = Query(-252)  # 最近一年
    pf.run(query)
    
    # 分析结果
    print("=== 投资组合绩效 ===")
    pf_tm.performance(query)
    
    # 对比各股票表现
    print("\n=== 个股表现对比 ===")
    for stock in stocks:
        # 单独测试每只股票
        single_tm = crtTM(init_cash=1000000)
        single_sys = SYS_Simple(tm=single_tm, sg=sg, mm=MM_FixedPercent(0.8), st=st)
        single_sys.run(stock, query)
        
        perf = single_tm.get_performance(Datetime.now(), Query.DAY)
        total_return = perf['总收益率'] if '总收益率' in perf.names() else 0
        print(f"{stock.name} ({stock.market_code}): {total_return:.2%}")

# 运行投资组合策略
multi_stock_portfolio()
```

## API参考速查

### 核心类层次结构

```
StockManager          # 股票数据管理器
├── Stock            # 股票对象
├── KData            # K线数据集合
└── KRecord          # 单条K线记录

TradeManager         # 交易管理器
├── TradeRecord      # 交易记录
├── PositionRecord   # 持仓记录
└── Performance      # 绩效分析

System               # 交易系统
├── SignalBase       # 信号指示器基类
├── MoneyManagerBase # 资金管理基类
├── StoplossBase     # 止损策略基类
└── ...              # 其他组件基类

Portfolio            # 投资组合
├── SelectorBase     # 选择器基类
└── AllocateFundsBase # 资产分配基类

Strategy             # 策略框架
Indicator            # 技术指标
```

### 常用函数速查

| 功能分类 | 函数名 | 说明 |
|---------|--------|------|
| 初始化 | `load_hikyuu()` | 初始化框架 |
| 数据获取 | `sm.getStock()` | 获取股票对象 |
| | `stock.getKData()` | 获取K线数据 |
| 技术指标 | `MA()`, `EMA()` | 移动平均 |
| | `MACD()`, `RSI()` | 技术指标 |
| | `CROSS()`, `IF()` | 逻辑指标 |
| 交易系统 | `crtTM()` | 创建交易账户 |
| | `SYS_Simple()` | 创建交易系统 |
| | `SG_Cross()` | 交叉信号 |
| | `MM_FixedPercent()` | 资金管理 |
| 投资组合 | `PF_Simple()` | 创建投资组合 |
| | `SE_Fixed()` | 固定选择器 |
| | `AF_EqualWeight()` | 等权分配 |
| 绩效分析 | `tm.performance()` | 绩效分析 |
| | `tm.get_trade_list()` | 获取交易记录 |
| 工具函数 | `select()` | 条件选股 |
| | `Datetime()` | 日期时间 |
| | `Query()` | 数据查询 |

---

**使用建议**: 
1. 从简单的单股票System开始学习
2. 逐步过渡到多股票Portfolio管理
3. 在熟练掌握基础API后再使用Strategy框架
4. 重视绩效分析和风险控制
5. 利用完整示例作为开发模板

**注意事项**:
- 在事件驱动回测中避免使用未来数据
- 合理设置预加载参数以平衡内存和性能
- 定期备份交易数据和配置文件
- 充分测试策略的鲁棒性

## API修正说明

本文档已修正了以下常见的API使用错误：

### 1. 止盈策略API修正
**错误用法**: `TP_FixedPercent(0.15)`  
**正确用法**: `ST_FixedPercent(0.15)`

**说明**: hikyuu框架中的止盈策略实际使用 `StoplossBase` 类，与止损策略共享相同的基类。

### 2. MACD指标访问修正
**错误用法**: 
```python
dif = macd[0]
dea = macd[1]
```

**正确用法**: 
```python
if len(macd) > 0:
    dif = macd.get_result(0)      # DIF线
    dea = macd.get_result(1)      # DEA线
    histogram = macd.get_result(2) # 柱状图
```

### 3. 指标上下文设置修正
**错误用法**: `indicator.setContext(stock, query)`  
**正确用法**: `indicator.set_context(stock, query)`

### 4. SYS_Simple参数修正
**错误用法**: `SYS_Simple(tm=tm, sg=sg, mm=mm, name="系统名")`  
**正确用法**: `SYS_Simple(tm=tm, sg=sg, mm=mm)`

**说明**: `SYS_Simple` 函数不接受 `name` 参数。

### 5. 安全的指标值访问
**建议做法**: 在访问指标值前检查长度
```python
if len(indicator) > 0:
    value = indicator[-1]
```

---

**文档编制**: 基于DeepWiki对fasiondog/hikyuu项目的API分析  
**API修正**: 基于实际编程经验和错误调试  
**最后更新**: 2025年8月25日
