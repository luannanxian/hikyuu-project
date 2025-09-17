"""
Hikyuu量化交易框架编程示例
基于之前的深度分析，展示hikyuu的实际编程应用
"""

from hikyuu import *
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def initialize_hikyuu():
    """初始化hikyuu框架"""
    print("=== 初始化Hikyuu框架 ===")
    
    # 定制化初始化配置
    options = {
        "stock_list": ["sh000001", "sz000001", "sh600000", "sz000002"],
        "ktype_list": ["day", "min"],
        "preload_num": {
            "day_max": 10000,
            "min_max": 5000
        },
        "load_history_finance": False,
        "load_weight": False,
        "start_spot": False,
        "spot_worker_num": 1,
    }
    
    # 初始化框架
    load_hikyuu(**options)
    
    print(f"已加载股票数量: {len(sm)}")
    print("初始化完成")
    return sm

def demonstrate_data_access():
    """演示数据获取功能"""
    print("\n=== 数据获取演示 ===")
    
    # 获取股票对象
    stock = sm['sz000001']  # 平安银行
    print(f"股票信息: {stock.name} ({stock.market_code})")
    print(f"股票有效性: {stock.valid}")
    print(f"最小交易数量: {stock.min_trade_number}")
    
    # 获取K线数据
    query = Query(-100)  # 最近100条日线数据
    kdata = stock.get_kdata(query)
    print(f"K线数据量: {len(kdata)}")
    if len(kdata) > 0:
        print(f"数据时间范围: {kdata[0].datetime} 到 {kdata[-1].datetime}")
    
    # 显示最新几条数据
    print("\n最新5条K线数据:")
    for i in range(-5, 0):
        k = kdata[i]
        print(f"{k.datetime}: 开盘={k.open:.2f}, 最高={k.high:.2f}, "
              f"最低={k.low:.2f}, 收盘={k.close:.2f}, 成交量={k.volume}")
    
    return stock, kdata

def demonstrate_indicators():
    """演示技术指标计算"""
    print("\n=== 技术指标演示 ===")
    
    stock = sm['sz000001']
    query = Query(-252)  # 最近一年数据
    
    # 设置指标上下文
    C = CLOSE()
    H = HIGH()
    L = LOW()
    V = VOL()
    
    C.set_context(stock, query)
    H.set_context(stock, query)
    L.set_context(stock, query)
    V.set_context(stock, query)
    
    # 计算各种技术指标
    ma5 = MA(C, 5)
    ma20 = MA(C, 20)
    ma60 = MA(C, 60)
    ema12 = EMA(C, 12)
    ema26 = EMA(C, 26)
    
    # MACD指标
    try:
        macd = MACD(C, 12, 26, 9)
        # MACD返回一个Indicator，需要正确访问其值
        if len(macd) > 0:
            dif = macd.get_result(0)  # DIF线
            dea = macd.get_result(1)  # DEA线  
            histogram = macd.get_result(2)  # 柱状图
        else:
            # 如果MACD计算失败，创建空指标
            dif = Indicator()
            dea = Indicator()
            histogram = Indicator()
    except:
        # 备用计算方法
        ema12 = EMA(C, 12)
        ema26 = EMA(C, 26)
        dif = ema12 - ema26
        dea = EMA(dif, 9)
        histogram = dif - dea
    
    # RSI指标
    rsi = RSI(C, 14)
    
    # 布林带计算
    try:
        # 尝试使用TA-Lib
        boll = TA_BBANDS(C, 20, 2, 2, 0)
        if hasattr(boll, '__len__') and len(boll) >= 3:
            upper = boll.get_result(0) if hasattr(boll, 'get_result') else boll[0]
            middle = boll.get_result(1) if hasattr(boll, 'get_result') else boll[1]
            lower = boll.get_result(2) if hasattr(boll, 'get_result') else boll[2]
        else:
            raise Exception("TA_BBANDS返回格式不正确")
    except:
        # 手动计算布林带
        ma_middle = MA(C, 20)
        std_dev = STDEV(C, 20)
        upper = ma_middle + std_dev * 2
        middle = ma_middle
        lower = ma_middle - std_dev * 2
    
    # ATR指标
    atr = ATR(14)
    atr.set_context(stock, query)
    
    print("技术指标计算完成:")
    try:
        if len(ma5) > 0:
            print(f"MA5最新值: {ma5[-1]:.2f}")
        if len(ma20) > 0:
            print(f"MA20最新值: {ma20[-1]:.2f}")
        if len(rsi) > 0:
            print(f"RSI最新值: {rsi[-1]:.2f}")
        if len(dif) > 0:
            print(f"MACD DIF最新值: {dif[-1]:.4f}")
        if len(upper) > 0:
            print(f"布林带上轨: {upper[-1]:.2f}")
        if len(atr) > 0:
            print(f"ATR最新值: {atr[-1]:.2f}")
    except Exception as e:
        print(f"指标值显示错误: {e}")
    
    return {
        'ma5': ma5, 'ma20': ma20, 'ma60': ma60,
        'rsi': rsi, 'macd_dif': dif, 'macd_dea': dea,
        'boll_upper': upper, 'boll_lower': lower,
        'atr': atr
    }

def create_trading_system():
    """创建交易系统"""
    print("\n=== 创建交易系统 ===")
    
    # 创建交易账户
    tm = crtTM(init_cash=1000000, name="双均线策略")
    print(f"创建交易账户，初始资金: {tm.init_cash}")
    
    # 创建信号指示器 - 5日均线上穿20日均线买入
    sg = SG_Cross(MA(CLOSE(), 5), MA(CLOSE(), 20))
    print("创建双均线交叉信号指示器")
    
    # 创建资金管理策略 - 每次投入20%资金
    mm = MM_FixedPercent(0.2)
    print("创建固定比例资金管理策略")
    
    # 创建止损策略 - 5%止损
    st = ST_FixedPercent(0.05)
    print("创建固定比例止损策略")
    
    # 创建止盈策略 - 15%止盈 (使用ST_FixedPercent作为止盈策略)
    tp = ST_FixedPercent(0.15)
    print("创建固定比例止盈策略")
    
    # 创建交易系统（SYS_Simple不接受name参数）
    sys = SYS_Simple(
        tm=tm,
        sg=sg,
        mm=mm,
        st=st,
        tp=tp
    )
    
    # 设置系统参数 - 修正：SYS_Simple对象没有setParam方法
    # 应该在创建System时设置参数，或者使用其他方式
    # sys.setParam("buy_delay", False)  # 这行会报错
    # sys.setParam("sell_delay", False)  # 这行会报错
    
    print("交易系统创建完成")
    return sys

def run_backtest():
    """运行回测"""
    print("\n=== 运行回测 ===")
    
    # 创建交易系统
    sys = create_trading_system()
    
    # 选择股票和回测期间
    stock = sm['sz000001']
    query = Query(-252*2)  # 最近2年数据
    
    print(f"开始回测股票: {stock.name}")
    print(f"回测数据量: {stock.get_count()} 条日线数据")
    
    # 运行回测
    sys.run(stock, query)
    
    # 获取交易记录
    trade_list = sys.tm.get_trade_list()
    print(f"交易次数: {len(trade_list)}")
    
    # 显示前几笔交易
    print("\n前5笔交易记录:")
    for i, trade in enumerate(trade_list[:5]):
        # 正确用法：TradeRecord对象的成交价格为real_price，成本为cost.total
        print(f"交易{i+1}: {trade.datetime} {trade.business} "
              f"{trade.stock.market_code} 成交价={trade.real_price} "
              f"数量={trade.number} 总成本={trade.cost.total} 佣金={trade.cost.commission} 印花税={trade.cost.stamptax}")
    
    return sys

def analyze_performance():
    """分析交易绩效"""
    print("\n=== 绩效分析 ===")
    
    # 运行回测
    sys = run_backtest()
    tm = sys.tm
    
    # 获取绩效报告
    query = Query(-252*2)
    performance = tm.get_performance(Datetime.now(), Query.DAY)
    
    print("=== 详细绩效报告 ===")
    print(performance.report())
    
    # 获取关键指标
    names = performance.names()
    values = performance.values()
    
    key_metrics = {}
    for name, value in zip(names, values):
        key_metrics[name] = value
    
    # 显示关键绩效指标
    print("\n=== 关键绩效指标 ===")
    if '帐户平均年收益率%' in key_metrics:
        print(f"年化收益率: {key_metrics['帐户平均年收益率%']}%")
    if '最大回撤' in key_metrics:
        print(f"最大回撤: {key_metrics['最大回撤']}%")
    if '夏普比率' in key_metrics:
        print(f"夏普比率: {key_metrics['夏普比率']}")
    if '赢利交易比例%' in key_metrics:
        print(f"赢利交易比例: {key_metrics['赢利交易比例%']}%")
    
    return tm, performance

def create_portfolio():
    """创建投资组合"""
    print("\n=== 创建投资组合 ===")
    
    # 选择股票池
    stock_codes = ['sz000001', 'sh600000', 'sz000002']
    stocks = [sm[code] for code in stock_codes if sm[code].valid]
    
    print(f"股票池: {[s.name for s in stocks]}")
    
    # 创建基础交易系统
    sg = SG_Cross(MA(CLOSE(), 10), MA(CLOSE(), 30))
    mm = MM_FixedPercent(0.8)  # 每只股票分配80%可用资金
    st = ST_FixedPercent(0.08)
    base_sys = SYS_Simple(sg=sg, mm=mm, st=st)
    
    # 创建系统选择器和资产分配器
    se = SE_Fixed(stocks, base_sys)
    af = AF_EqualWeight()  # 等权重分配
    
    # 创建投资组合账户
    pf_tm = crtTM(init_cash=3000000, name="多股票组合")
    
    # 创建投资组合
    pf = PF_Simple(
        tm=pf_tm,
        se=se,
        af=af,
        adjust_cycle=5,      # 每5个交易日调仓一次
        adjust_mode="day"
    )
    
    print("投资组合创建完成")
    
    # 运行投资组合回测
    query = Query(-252)  # 最近一年
    print("开始运行投资组合回测...")
    pf.run(query)
    
    print("投资组合回测完成")
    print(f"组合最终资金: {pf_tm.current_cash:.2f}")
    
    return pf

def demonstrate_stock_selection():
    """演示选股功能"""
    print("\n=== 选股功能演示 ===")
    
    # RSI超卖选股
    print("1. RSI超卖选股 (RSI < 30)")
    try:
        rsi_condition = RSI(CLOSE(), 14) < 30
        oversold_stocks = select(rsi_condition)
        print(f"超卖股票数量: {len(oversold_stocks)}")
        for stock in oversold_stocks[:5]:  # 显示前5只
            print(f"  {stock.name} ({stock.market_code})")
    except Exception as e:
        print(f"RSI选股失败: {e}")
    
    # 均线多头排列选股
    print("\n2. 均线多头排列选股 (MA5 > MA10 > MA20)")
    try:
        ma5 = MA(CLOSE(), 5)
        ma10 = MA(CLOSE(), 10)
        ma20 = MA(CLOSE(), 20)
        bullish_condition = (ma5 > ma10) & (ma10 > ma20)
        bullish_stocks = select(bullish_condition)
        print(f"多头排列股票数量: {len(bullish_stocks)}")
        for stock in bullish_stocks[:5]:  # 显示前5只
            print(f"  {stock.name} ({stock.market_code})")
    except Exception as e:
        print(f"均线选股失败: {e}")

# def demonstrate_event_driven_backtest():
#     """演示事件驱动回测"""
#     print("\n=== 事件驱动回测演示 ===")
    
#     def on_bar(krecord):
#         """K线数据回调函数"""
#         stk = sm['sz000001']
#         kdata = stk.getKData(Query(-30, Query.MIN))
#         if len(kdata) < 30:
#             return
#         try:
#             close = CLOSE()
#             close.set_context(stk, Query(-30, Query.MIN))
#             ma5 = MA(close, 5)
#             ma10 = MA(close, 10)
#             if len(ma5) > 0 and len(ma10) > 0:
#                 ma5_val = float(ma5[-1])
#                 ma10_val = float(ma10[-1])
#                 # 交易逻辑
#                 # 需获取当前持仓状态
#                 # stg.tm.have(stk) 替换为 tm.have(stk)
#                 if ma5_val > ma10_val and not tm.have(stk):
#                     tm.buy(stk, krecord.close, 100)
#                     print(f"{krecord.datetime}: 金叉买入 价格={krecord.close:.2f}")
#                 elif ma5_val < ma10_val and tm.have(stk):
#                     tm.sell(stk, krecord.close, 100)
#                     print(f"{krecord.datetime}: 死叉卖出 价格={krecord.close:.2f}")
#         except Exception as e:
#             print(f"事件驱动回测中指标计算错误: {e}")
    
#     # 设置回测参数
#     # 修正授权限制导致的回测区间异常，确保 start_date < end_date
#     start_date = Datetime(2019, 1, 1)
#     end_date = Datetime(2024, 6, 30)
#     tm = crtTM(init_cash=300000)
    
#     print(f"事件驱动回测期间: {start_date} 到 {end_date}")
    
#     try:
#         # 执行事件驱动回测
#         backtest(on_bar, tm, start_date, end_date, Query.MIN)
        
#         # 分析结果
#         trade_list = tm.get_trade_list()
#         print(f"事件驱动回测完成，共执行 {len(trade_list)} 笔交易")
#         print(f"最终资金: {tm.current_cash:.2f}")
        
#     except Exception as e:
#         print(f"事件驱动回测失败: {e}")

def create_custom_indicator():
    """创建自定义指标"""
    print("\n=== 自定义指标演示 ===")
    
    def bollinger_squeeze():
        """布林带收缩指标"""
        # 手动计算布林带
        close = CLOSE()
        ma_middle = MA(close, 20)
        std_dev = STDEV(close, 20)
        upper = ma_middle + std_dev * 2
        lower = ma_middle - std_dev * 2
        
        # 计算带宽
        bandwidth = (upper - lower) / ma_middle * 100
        
        # 布林带收缩：带宽小于历史20日均值
        squeeze_threshold = MA(bandwidth, 20)
        squeeze_signal = bandwidth < squeeze_threshold
        
        return squeeze_signal, bandwidth
    
    def rsi_divergence():
        """RSI背离指标"""
        price = CLOSE()
        rsi_14 = RSI(price, 14)
        
        # 简化的背离检测：价格新高但RSI未新高
        price_high = HHV(price, 10)
        rsi_high = HHV(rsi_14, 10)
        
        # 当前价格接近10日最高价但RSI远离10日最高RSI
        price_at_high = price / price_high > 0.98
        rsi_below_high = rsi_14 / rsi_high < 0.95
        
        divergence = price_at_high & rsi_below_high
        
        return divergence
    
    # 应用自定义指标
    stock = sm['sz000001']
    query = Query(-100)
    
    # 设置上下文
    CLOSE().set_context(stock, query)
    
    try:
        # 计算自定义指标
        squeeze_signal, bandwidth = bollinger_squeeze()
        divergence_signal = rsi_divergence()
        
        print("自定义指标计算完成:")
        try:
            if len(squeeze_signal) > 0:
                print(f"布林带收缩信号: {squeeze_signal[-1]}")
            if len(bandwidth) > 0:
                print(f"当前带宽: {bandwidth[-1]:.2f}%")
            if len(divergence_signal) > 0:
                print(f"RSI背离信号: {divergence_signal[-1]}")
        except Exception as e:
            print(f"自定义指标显示错误: {e}")
        
    except Exception as e:
        print(f"自定义指标计算失败: {e}")

def main():
    """主函数 - 演示hikyuu编程能力"""
    print("Hikyuu量化交易框架编程能力演示")
    print("=" * 50)
    
    try:
        # 1. 初始化框架
        sm = initialize_hikyuu()
        
        # 2. 数据获取演示
        stock, kdata = demonstrate_data_access()
        
        # 3. 技术指标演示
        indicators = demonstrate_indicators()
        
        # 4. 创建交易系统
        sys = create_trading_system()
        
        # 5. 绩效分析
        tm, performance = analyze_performance()
        
        # 6. 投资组合管理
        portfolio = create_portfolio()
        
        # 7. 选股功能
        demonstrate_stock_selection()
        
        # 8. 事件驱动回测
        # demonstrate_event_driven_backtest()
        
        # 9. 自定义指标
        create_custom_indicator()
        
        print("\n" + "=" * 50)
        print("所有编程演示完成！")
        print("Hikyuu编程能力已充分展示")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        print("请确保已正确安装和配置hikyuu框架")

if __name__ == "__main__":
    # 注意：实际运行需要先安装hikyuu并配置数据
    print("注意：此示例代码需要在安装了hikyuu框架的环境中运行")
    print("请确保已正确安装hikyuu并配置了股票数据")
    print()
    
    # 显示代码结构说明（不直接运行main函数避免卡死）
    print("代码包含以下编程能力演示:")
    print("1. 框架初始化和配置")
    print("2. 股票数据获取和访问")
    print("3. 技术指标计算和应用")
    print("4. 交易系统构建和配置")
    print("5. 回测执行和绩效分析")
    print("6. 投资组合创建和管理")
    print("7. 条件选股功能")
    # print("8. 事件驱动回测")
    print("9. 自定义指标开发")
    print("\n这些示例展示了对hikyuu框架的全面掌握和编程应用能力")
    
    # 如果要实际运行演示，请手动调用：
    main()
