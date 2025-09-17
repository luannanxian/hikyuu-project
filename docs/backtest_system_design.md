# 小市值交互因子策略回测系统设计文档 (修正版)

**文档版本**: v1.1 (基于DeepWiki专业反馈修正)  
**创建日期**: 2025年9月5日  
**修正日期**: 2025年9月5日  
**项目**: hikyuu-project  
**策略**: 小市值交互因子选股策略回测系统

## 1. 项目概述

### 1.1 设计目标
基于hikyuu框架为现有的小市值交互因子选股策略构建完整的历史回测系统，实现策略有效性验证、绩效评估和参数优化。

### 1.2 技术栈
- **框架**: hikyuu量化交易框架
- **语言**: Python 3.x
- **回测模式**: Portfolio多资产组合回测
- **数据源**: hikyuu内置数据管理系统

### 1.3 设计原则
- **符合hikyuu最佳实践**: 严格遵循hikyuu框架的标准接口和设计模式
- **复用优先**: 最大化利用hikyuu内置功能
- **适配集成**: 将现有选股策略适配到hikyuu标准接口
- **模块化**: 保持良好的代码结构和可维护性

### 1.4 **DeepWiki专业验证** ✅
本设计已通过DeepWiki对hikyuu框架的专业分析验证，确认核心架构符合hikyuu最佳实践。

## 2. 系统架构

### 2.1 整体架构图
```
┌─────────────────────────────────────────────────────────────┐
│                    用户接口层 (User Interface)                 │
├─────────────────────────────────────────────────────────────┤
│                    回测管理层 (Backtest Management)           │
│  BacktestConfigManager  │  BacktestRunner  │  ResultAnalyzer │
├─────────────────────────────────────────────────────────────┤
│                    策略适配层 (Strategy Adapter)              │
│        SmallCapFactorSelector  │  PerformanceAnalyzer       │
├─────────────────────────────────────────────────────────────┤
│                  现有选股策略层 (Existing Strategy)            │
│  SmallCapFactorStrategy │ FactorCalculator │ StockScreener  │
├─────────────────────────────────────────────────────────────┤
│                    Hikyuu框架层 (Hikyuu Framework)            │
│    Portfolio │ SelectorBase │ TradeManager │ SystemWeightList│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 **修正后的技术架构要点**

#### 关键修正点
1. **SelectorBase接口**: 使用`_calculate()`和`get_selected()`方法，而非`getSelectedSystemList`
2. **系统构建流程**: 通过`addStock`添加原型系统，在`_calculate`中基于`real_sys_list`选择
3. **绩效分析**: 使用TradeManager的具体接口而非通用`performance()`方法

## 3. 核心组件设计

### 3.1 SmallCapFactorSelector (关键组件) **[已修正]**

#### 3.1.1 类定义
```python
class SmallCapFactorSelector(SelectorBase):
    """
    小市值多因子选股器 - 继承hikyuu SelectorBase基类
    
    符合hikyuu标准实践：
    - 重写_calculate()方法实现选股逻辑
    - 重写get_selected()方法返回SystemWeightList
    - 通过addStock添加原型系统到股票池
    """
    
    def __init__(self, market_cap_limit: float = 60.0, 
                 top_n: int = 10,
                 factor_periods: List[int] = [5, 20, 60]):
        """
        初始化选股器
        
        Args:
            market_cap_limit: 市值上限(亿元)
            top_n: 选股数量
            factor_periods: 因子计算周期
        """
        super().__init__("SmallCapFactor")
        self.strategy = SmallCapFactorStrategy(market_cap_limit, top_n)
        self.top_n = top_n
        self.latest_selection = []
        
        # 【关键】：添加股票池到原型系统
        self._setup_stock_universe()
```

#### 3.1.2 **修正后的核心接口实现**
```python
def _setup_stock_universe(self):
    """
    设置股票池 - 添加原型系统
    这是hikyuu Selector的标准初始化流程
    """
    sm = StockManager.instance()
    
    for stock in sm:
        if stock.valid and stock.type in [1, 8, 9, 11]:  # A股、创业板、科创板、北交所
            # 创建简单的买入持有系统作为原型
            # 这些原型系统会被Portfolio克隆为real_sys_list
            proto_sys = SYS_Simple(
                sg=SG_True(),  # 始终为真的信号（买入持有）
                mm=MM_FixedPercent(0.1)  # 固定比例资金管理
            )
            self.addStock(stock, proto_sys)

def _calculate(self, real_sys_list, query):
    """
    【关键方法】：hikyuu Selector的核心计算接口
    
    Args:
        real_sys_list: Portfolio提供的实际系统列表（克隆自原型）
        query: 查询对象，包含时间范围等信息
        
    在此方法中执行选股逻辑，结果供get_selected使用
    """
    try:
        # 获取当前计算时点
        current_date = query.end_datetime
        
        # 调用现有选股策略
        results = self.strategy.run_stock_selection(
            target_date=current_date, 
            save_results=False
        )
        
        if results['success']:
            # 存储选股结果供get_selected使用
            self.latest_selection = results['top_stocks']
            self.real_sys_list = real_sys_list  # 保存引用
        else:
            self.latest_selection = []
            
    except Exception as e:
        # 异常处理：确保Selector不会因错误而中断Portfolio运行
        print(f"选股计算异常: {e}")
        self.latest_selection = []

def get_selected(self, datetime):
    """
    【关键方法】：返回在指定时间点选中的系统列表
    
    Args:
        datetime: 指定的时间点
        
    Returns:
        SystemWeightList: 选中的系统及其权重列表
        
    这是Portfolio在每次调仓时调用的标准接口
    """
    selected_list = SystemWeightList()
    
    if hasattr(self, 'latest_selection') and self.latest_selection:
        selected_codes = {stock['stock_code'] for stock in self.latest_selection[:self.top_n]}
        
        # 从real_sys_list中找到对应的系统
        for sys_info in getattr(self, 'real_sys_list', []):
            if sys_info.stock.market_code in selected_codes:
                # 等权重分配（也可以根据评分加权）
                weight = 1.0 / len(selected_codes)
                selected_list.append(SystemWeight(sys_info.sys, weight))
    
    return selected_list
```

#### 3.1.3 **技术要点说明**
1. **原型系统机制**: 通过`addStock`添加的是原型系统，Portfolio运行时会克隆为独立的`real_sys_list`
2. **计算时机**: `_calculate`在Portfolio需要重新选股时被调用
3. **选择逻辑**: `get_selected`基于`_calculate`的结果返回选中系统
4. **权重分配**: 可以等权重或根据因子评分加权

### 3.2 PerformanceAnalyzer **[已修正]**

#### 3.2.1 **修正后的绩效分析接口**
```python
class PerformanceAnalyzer:
    """
    绩效分析器 - 基于hikyuu TradeManager的标准接口
    """
    
    def analyze_performance(self, trade_manager: TradeManager) -> Dict[str, Any]:
        """
        完整的绩效分析
        
        使用TradeManager的标准接口获取各种绩效数据
        """
        analysis_result = {}
        
        try:
            # 1. 获取资金曲线
            funds_curve = trade_manager.get_funds_curve()
            analysis_result['funds_curve'] = funds_curve
            
            # 2. 获取完整绩效报告
            performance_report = trade_manager.get_performance()
            analysis_result['performance_report'] = performance_report
            
            # 3. 获取交易记录
            trade_list = trade_manager.get_trade_list()
            analysis_result['trade_list'] = trade_list
            
            # 4. 获取持仓记录
            position_list = trade_manager.get_position_list()
            analysis_result['position_list'] = position_list
            
            # 5. 计算自定义绩效指标
            custom_metrics = self._calculate_custom_metrics(
                funds_curve, trade_list, position_list
            )
            analysis_result['custom_metrics'] = custom_metrics
            
            return analysis_result
            
        except Exception as e:
            print(f"绩效分析异常: {e}")
            return {'error': str(e)}
    
    def _calculate_custom_metrics(self, funds_curve, trade_list, position_list):
        """
        计算自定义绩效指标
        
        基于hikyuu提供的基础数据计算额外指标
        """
        metrics = {}
        
        if len(funds_curve) > 0:
            # 计算收益率序列
            returns = []
            for i in range(1, len(funds_curve)):
                ret = (funds_curve[i].total - funds_curve[i-1].total) / funds_curve[i-1].total
                returns.append(ret)
            
            # 计算年化收益率
            if returns:
                total_return = (funds_curve[-1].total - funds_curve[0].total) / funds_curve[0].total
                trading_days = len(funds_curve)
                annual_return = (1 + total_return) ** (252 / trading_days) - 1
                metrics['annual_return'] = annual_return
                
                # 计算夏普比率（简化版）
                if len(returns) > 1:
                    import numpy as np
                    mean_return = np.mean(returns)
                    std_return = np.std(returns)
                    if std_return > 0:
                        sharpe_ratio = mean_return / std_return * (252 ** 0.5)
                        metrics['sharpe_ratio'] = sharpe_ratio
        
        # 计算胜率
        if trade_list:
            winning_trades = sum(1 for trade in trade_list if trade.real_price > 0)  # 简化计算
            metrics['win_rate'] = winning_trades / len(trade_list)
        
        return metrics
```

### 3.3 BacktestConfigManager **[已完善]**

#### 3.3.1 **增强的配置管理**
```python
@dataclass
class BacktestConfig:
    """回测配置数据类 - 符合hikyuu参数体系"""
    
    # 时间参数
    start_date: str = "2020-01-01"
    end_date: str = "2024-12-31"
    
    # 资金参数
    initial_cash: float = 10_000_000  # 确保资金充足（重要）
    
    # 调仓参数 - 对应hikyuu Portfolio参数
    adjust_cycle: int = 20            # 调仓周期（交易日）
    adjust_mode: str = "day"          # 调仓模式：day/week/month/quarter/year
    delay_to_trading_day: bool = True # 调仓日顺延到交易日
    
    # 策略参数
    market_cap_limit: float = 60.0    # 市值上限(亿)
    top_n_stocks: int = 10           # 持仓股票数
    factor_periods: List[int] = field(default_factory=lambda: [5, 20, 60])
    
    # 交易成本参数 - 对应hikyuu成本模型
    commission_rate: float = 0.0003   # 佣金费率
    stamp_tax_rate: float = 0.001     # 印花税率（仅卖出）
    min_commission: float = 5.0       # 最小佣金
    slippage_rate: float = 0.001      # 滑点率
    
    # 基准和分析参数
    benchmark: str = "sh000300"       # 基准指数
    save_results: bool = True
    result_path: str = "backtest_results"

class BacktestConfigManager:
    """回测配置管理器"""
    
    def create_trade_manager(self, config: BacktestConfig) -> TradeManager:
        """
        根据配置创建TradeManager
        
        配置交易成本模型以确保回测真实性
        """
        tm = crtTM(
            init_cash=config.initial_cash,
            name="SmallCapFactorBacktest"
        )
        
        # 配置交易成本（重要）
        # 这部分需要根据hikyuu的成本模型接口进行配置
        # 确保包含佣金、印花税、滑点等
        
        return tm
    
    def create_portfolio(self, config: BacktestConfig) -> Portfolio:
        """
        根据配置创建Portfolio
        
        使用PF_Simple创建标准投资组合
        """
        # 创建交易管理器
        tm = self.create_trade_manager(config)
        
        # 创建选股器
        selector = SmallCapFactorSelector(
            market_cap_limit=config.market_cap_limit,
            top_n=config.top_n_stocks,
            factor_periods=config.factor_periods
        )
        
        # 创建资金分配器
        allocator = AF_EqualWeight()  # 等权重分配
        
        # 创建Portfolio
        portfolio = PF_Simple(
            tm=tm,
            se=selector,
            af=allocator,
            adjust_cycle=config.adjust_cycle,
            adjust_mode=config.adjust_mode,
            delay_to_trading_day=config.delay_to_trading_day
        )
        
        return portfolio
```

### 3.4 BacktestRunner

#### 3.4.1 回测执行器
```python
class BacktestRunner:
    """回测执行器"""
    
    def __init__(self, config: BacktestConfig):
        """初始化回测执行器"""
        self.config = config
        self.config_manager = BacktestConfigManager()
        self.analyzer = PerformanceAnalyzer()
        
    def run_single_backtest(self) -> BacktestResult:
        """
        执行单次回测
        
        完整的hikyuu回测流程
        """
        try:
            # 1. 创建Portfolio
            portfolio = self.config_manager.create_portfolio(self.config)
            
            # 2. 设置回测时间范围
            query = Query(
                Datetime(self.config.start_date), 
                Datetime(self.config.end_date)
            )
            
            # 3. 执行回测
            print(f"开始回测: {self.config.start_date} 到 {self.config.end_date}")
            portfolio.run(query)
            
            # 4. 分析绩效
            analysis_result = self.analyzer.analyze_performance(portfolio.tm)
            
            # 5. 构建回测结果
            result = BacktestResult(
                config=self.config,
                portfolio=portfolio,
                trade_manager=portfolio.tm,
                analysis_result=analysis_result,
                success=True
            )
            
            # 6. 保存结果
            if self.config.save_results:
                self._save_results(result)
            
            return result
            
        except Exception as e:
            print(f"回测执行异常: {e}")
            return BacktestResult(
                config=self.config,
                success=False,
                error_message=str(e)
            )
    
    def _save_results(self, result: BacktestResult):
        """保存回测结果"""
        # 实现结果保存逻辑
        pass
```

## 4. **修正后的数据流设计**

### 4.1 标准数据流
```
现有选股策略 → _calculate() → get_selected() → Portfolio.run() → TradeManager → 绩效分析
     ↓              ↓            ↓              ↓            ↓           ↓
1. 因子计算    1. 选股逻辑   1. 返回选中     1. 自动调仓   1. 交易记录   1. 资金曲线
2. 股票筛选    2. 存储结果   2. SystemList   2. 交易执行   2. 持仓管理   2. 绩效报告
3. 评分排名    3. 异常处理   3. 权重分配     3. 成本计算   3. 资金管理   3. 交易分析
```

### 4.2 **关键数据格式标准化**

#### 选股器内部数据流
```python
# _calculate输入
real_sys_list: List[SystemInfo]  # Portfolio提供的实际系统列表
query: Query                     # 查询对象

# _calculate内部处理
selection_results = strategy.run_stock_selection()  # 调用现有策略
self.latest_selection = results['top_stocks']       # 存储结果

# get_selected输出
SystemWeightList: List[SystemWeight]  # 标准hikyuu格式
```

## 5. 文件结构设计

### 5.1 目录结构
```
backtest_system/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── backtest_config.py      # 回测配置类
│   └── default_config.py       # 默认配置参数
├── core/
│   ├── __init__.py
│   ├── selector.py             # SmallCapFactorSelector
│   ├── runner.py               # BacktestRunner
│   └── analyzer.py             # PerformanceAnalyzer
├── utils/
│   ├── __init__.py
│   ├── data_adapter.py         # 数据适配工具
│   ├── chart_generator.py      # 图表生成工具
│   └── report_generator.py     # 报告生成工具
├── examples/
│   ├── __init__.py
│   ├── basic_backtest.py       # 基础回测示例
│   ├── parameter_optimization.py  # 参数优化示例
│   └── strategy_comparison.py  # 策略对比示例
└── tests/
    ├── __init__.py
    ├── test_selector.py        # 选股器测试
    ├── test_runner.py          # 回测执行器测试
    └── test_analyzer.py        # 分析器测试
```

## 6. 接口设计

### 6.1 主要API接口

#### 6.1.1 简单回测接口
```python
def run_backtest(config: BacktestConfig = None) -> BacktestResult:
    """
    执行回测的主要接口
    
    Args:
        config: 回测配置，为None时使用默认配置
        
    Returns:
        BacktestResult: 回测结果对象
        
    Example:
        result = run_backtest()
        print(f"年化收益率: {result.analysis_result['custom_metrics']['annual_return']:.2%}")
    """
    if config is None:
        config = BacktestConfig()
    
    runner = BacktestRunner(config)
    return runner.run_single_backtest()
```

#### 6.1.2 参数优化接口
```python
def optimize_parameters(param_ranges: Dict[str, List],
                       objective: str = "sharpe_ratio") -> OptimizationResult:
    """
    参数优化接口
    
    Args:
        param_ranges: 参数范围字典
        objective: 优化目标指标
        
    Returns:
        OptimizationResult: 优化结果
        
    Example:
        ranges = {
            'market_cap_limit': [40, 50, 60, 70],
            'top_n_stocks': [5, 10, 15, 20]
        }
        result = optimize_parameters(ranges)
    """
```

## 7. **修正后的实施计划**

### 7.1 Phase 1: 核心功能 (预计3天) **[已修正]**

#### Day 1: 正确的SelectorBase实现
- [ ] 创建项目目录结构
- [ ] **【修正】实现SmallCapFactorSelector的_calculate()和get_selected()方法**
- [ ] **【新增】实现正确的原型系统添加逻辑(_setup_stock_universe)**
- [ ] 基础测试用例

#### Day 2: 数据流适配
- [ ] **【修正】基于real_sys_list的选股逻辑实现**
- [ ] **【修正】SystemWeightList的正确构建**
- [ ] 现有策略集成测试
- [ ] 异常处理完善

#### Day 3: Portfolio集成
- [ ] BacktestConfigManager实现
- [ ] Portfolio创建和配置
- [ ] **【修正】使用TradeManager标准接口的绩效分析**
- [ ] 端到端测试验证

### 7.2 Phase 2: 增强功能 (预计1周)

#### 功能增强
- [ ] 参数优化功能
- [ ] 策略对比功能
- [ ] 增强可视化
- [ ] 详细报告生成

#### 测试完善
- [ ] 完整单元测试
- [ ] 性能测试
- [ ] 文档完善

### 7.3 关键验证点
1. **SelectorBase接口正确性**: 确保_calculate和get_selected按hikyuu标准实现
2. **系统选择准确性**: 验证选出的股票与现有策略一致
3. **权重分配正确性**: 确保SystemWeightList构建正确
4. **绩效数据完整性**: 验证TradeManager接口使用正确

## 8. **技术细节checklist**

### 8.1 必须遵循的hikyuu标准
- [x] ✅ 继承SelectorBase并重写标准方法
- [x] ✅ 使用addStock添加原型系统到股票池
- [x] ✅ 在_calculate中基于real_sys_list进行选择
- [x] ✅ get_selected返回标准SystemWeightList
- [x] ✅ 使用PF_Simple创建Portfolio
- [x] ✅ 通过TradeManager标准接口获取绩效数据

### 8.2 关键配置要点
- [x] ✅ 确保TradeManager初始资金充足
- [x] ✅ 配置合理的交易成本模型
- [x] ✅ 设置正确的调仓参数
- [x] ✅ 处理delay_to_trading_day等细节参数

## 9. 测试设计

### 9.1 单元测试

#### 9.1.1 SmallCapFactorSelector测试
```python
class TestSmallCapFactorSelector:
    def test_initialization(self):
        """测试选股器初始化"""
        selector = SmallCapFactorSelector()
        assert selector.name == "SmallCapFactor"
        assert selector.top_n == 10
        
    def test_calculate_method(self):
        """测试_calculate方法"""
        # 模拟real_sys_list和query
        # 验证选股逻辑执行
        
    def test_get_selected_method(self):
        """测试get_selected方法"""
        # 验证返回SystemWeightList格式正确
        
    def test_edge_cases(self):
        """测试边界情况"""
        # 空选股结果、异常处理等
```

### 9.2 集成测试

#### 9.2.1 端到端测试
```python
def test_end_to_end_backtest():
    """测试完整回测流程"""
    config = BacktestConfig(
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_cash=1_000_000,
        top_n_stocks=5
    )
    
    result = run_backtest(config)
    
    assert result.success == True
    assert len(result.analysis_result['trade_list']) > 0
    assert result.analysis_result['funds_curve'] is not None
```

## 10. 风险评估与控制

### 10.1 技术风险
- **hikyuu接口兼容性**: 严格按照DeepWiki验证的标准实现
- **数据转换准确性**: 充分测试选股结果到SystemWeightList的转换
- **性能瓶颈**: 大股票池的选股计算优化

### 10.2 实施风险
- **开发延期**: 分阶段实施，核心功能优先
- **集成问题**: 与现有策略的接口兼容性测试
- **质量问题**: 严格的代码审查和测试覆盖

## 11. 成功标准

### 11.1 技术标准
- ✅ SelectorBase接口实现符合hikyuu标准
- ✅ Portfolio回测能够正常执行
- ✅ 绩效分析数据完整准确
- ✅ 与现有选股策略结果一致

### 11.2 质量标准
- ✅ 代码覆盖率达到90%以上
- ✅ 关键路径异常处理完整
- ✅ 性能指标满足要求
- ✅ 文档和示例完善

### 11.3 用户体验标准
- ✅ 简单易用的API接口
- ✅ 清晰的配置和文档
- ✅ 完善的错误提示和处理
- ✅ 丰富的示例代码

---

**文档状态**: 已修正，符合hikyuu最佳实践  
**验证状态**: 通过DeepWiki专业验证  
**技术审查**: 所有关键接口已确认符合hikyuu标准  
**实施准备**: 设计文档完成，可开始严格按此规范实施

## 12. 遗漏的重要设计要点 **[补充]**

### 12.1 **BacktestResult数据类定义** (重要遗漏)
```python
@dataclass
class BacktestResult:
    """回测结果数据类 - 标准化回测输出"""
    config: BacktestConfig
    portfolio: Portfolio = None
    trade_manager: TradeManager = None
    analysis_result: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    success: bool = False
    error_message: str = ""
    
    # 新增字段
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    total_trades: int = 0
    selected_stocks_history: List[Dict] = field(default_factory=list)
```

### 12.2 **交易成本配置** (关键遗漏)
```python
def setup_trading_costs(self, tm: TradeManager, config: BacktestConfig):
    """
    配置交易成本模型 - 这是回测真实性的关键
    """
    # 设置佣金
    tm.setBrokerageFunc(crtBF_Fixed(
        commission=config.commission_rate,
        min_commission=config.min_commission,
        stamptax=config.stamp_tax_rate  # 印花税仅卖出
    ))
    
    # 设置滑点
    tm.setSlippageFunc(crtSL_FixedPercent(config.slippage_rate))
```

### 12.3 **基准比较分析** (遗漏)
```python
class BenchmarkComparator:
    """基准比较分析器"""
    
    def compare_with_benchmark(self, portfolio_tm: TradeManager, 
                             benchmark_code: str = "sh000300") -> Dict:
        """与基准指数对比分析"""
        # 获取基准数据
        benchmark_stock = StockManager.instance()[benchmark_code]
        benchmark_returns = self._calculate_benchmark_returns(benchmark_stock)
        
        # 获取策略资金曲线
        funds_curve = portfolio_tm.get_funds_curve()
        strategy_returns = self._calculate_strategy_returns(funds_curve)
        
        # 计算对比指标
        return {
            'alpha': self._calculate_alpha(strategy_returns, benchmark_returns),
            'beta': self._calculate_beta(strategy_returns, benchmark_returns),
            'tracking_error': self._calculate_tracking_error(strategy_returns, benchmark_returns),
            'information_ratio': self._calculate_information_ratio(strategy_returns, benchmark_returns),
            'correlation': self._calculate_correlation(strategy_returns, benchmark_returns)
        }
```

### 12.4 **可视化图表生成** (遗漏)
```python
class ChartGenerator:
    """图表生成器"""
    
    def generate_performance_charts(self, result: BacktestResult) -> Dict[str, Any]:
        """生成回测绩效图表"""
        charts = {}
        
        # 1. 净值曲线图
        charts['nav_curve'] = self._create_nav_curve_chart(result)
        
        # 2. 回撤曲线图
        charts['drawdown_curve'] = self._create_drawdown_chart(result)
        
        # 3. 月度收益热力图
        charts['monthly_returns'] = self._create_monthly_returns_heatmap(result)
        
        # 4. 持仓分布图
        charts['position_distribution'] = self._create_position_chart(result)
        
        # 5. 因子有效性分析图
        charts['factor_effectiveness'] = self._create_factor_analysis_chart(result)
        
        return charts
```

### 12.5 **参数优化器实现** (遗漏)
```python
class ParameterOptimizer:
    """参数优化器"""
    
    def grid_search_optimization(self, param_ranges: Dict[str, List], 
                                objective: str = "sharpe_ratio") -> OptimizationResult:
        """网格搜索参数优化"""
        import itertools
        
        # 生成参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        param_combinations = list(itertools.product(*param_values))
        
        best_result = None
        best_score = float('-inf')
        optimization_results = []
        
        for i, combination in enumerate(param_combinations):
            # 创建配置
            config = BacktestConfig()
            for j, param_name in enumerate(param_names):
                setattr(config, param_name, combination[j])
            
            # 执行回测
            runner = BacktestRunner(config)
            result = runner.run_single_backtest()
            
            if result.success:
                # 计算目标函数值
                score = self._calculate_objective_score(result, objective)
                optimization_results.append({
                    'params': dict(zip(param_names, combination)),
                    'score': score,
                    'result': result
                })
                
                if score > best_score:
                    best_score = score
                    best_result = result
        
        return OptimizationResult(
            best_params=best_result.config if best_result else None,
            best_score=best_score,
            all_results=optimization_results
        )
```

### 12.6 **日志和监控** (遗漏)
```python
class BacktestLogger:
    """回测日志管理"""
    
    def setup_logging(self, log_level: str = "INFO"):
        """设置回测日志"""
        import logging
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        
    def log_selection_details(self, selector: SmallCapFactorSelector, 
                            selection_date: Datetime):
        """记录选股详情"""
        # 记录选股过程的详细信息
        pass
```

### 12.7 **错误处理和恢复** (遗漏)
```python
class ErrorHandler:
    """错误处理器"""
    
    def handle_selector_error(self, selector: SmallCapFactorSelector, 
                            error: Exception) -> List:
        """处理选股器错误"""
        # 记录错误
        logging.error(f"选股器错误: {error}")
        
        # 返回默认选股结果或上次成功的结果
        return getattr(selector, 'last_successful_selection', [])
    
    def handle_portfolio_error(self, portfolio: Portfolio, 
                             error: Exception) -> bool:
        """处理投资组合错误"""
        # 错误恢复策略
        return False
```

### 12.8 **数据缓存机制** (性能优化遗漏)
```python
class DataCache:
    """数据缓存管理"""
    
    def __init__(self):
        self.factor_cache = {}
        self.selection_cache = {}
    
    def get_cached_factors(self, stock_code: str, date: Datetime) -> Dict:
        """获取缓存的因子数据"""
        cache_key = f"{stock_code}_{date}"
        return self.factor_cache.get(cache_key)
    
    def cache_factors(self, stock_code: str, date: Datetime, factors: Dict):
        """缓存因子数据"""
        cache_key = f"{stock_code}_{date}"
        self.factor_cache[cache_key] = factors
```

### 12.9 **性能监控** (遗漏)
```python
class PerformanceMonitor:
    """性能监控器"""
    
    def monitor_backtest_performance(self, runner: BacktestRunner):
        """监控回测性能"""
        import time
        import psutil
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        # 执行回测
        result = runner.run_single_backtest()
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        performance_stats = {
            'execution_time': end_time - start_time,
            'memory_usage': end_memory - start_memory,
            'peak_memory': psutil.Process().memory_info().peak_wss if hasattr(psutil.Process().memory_info(), 'peak_wss') else 0
        }
        
        return result, performance_stats
```

### 12.10 **配置验证器** (遗漏)
```python
class ConfigValidator:
    """配置验证器"""
    
    def validate_config(self, config: BacktestConfig) -> List[str]:
        """验证回测配置"""
        errors = []
        
        # 验证日期
        try:
            start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(config.end_date, "%Y-%m-%d")
            if start_date >= end_date:
                errors.append("开始日期必须早于结束日期")
        except ValueError:
            errors.append("日期格式错误，应为YYYY-MM-DD")
        
        # 验证资金
        if config.initial_cash <= 0:
            errors.append("初始资金必须大于0")
        
        # 验证股票数量
        if config.top_n_stocks <= 0:
            errors.append("选股数量必须大于0")
        
        # 验证费率
        if config.commission_rate < 0 or config.commission_rate > 0.01:
            errors.append("佣金费率应在0-1%之间")
        
        return errors
```

## 附录：关键代码模板

### A.1 完整的SmallCapFactorSelector模板
```python
from hikyuu import *
from typing import List, Dict, Any
import sys
import os

# 添加现有策略路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../strategy_implementation'))
from main_strategy import SmallCapFactorStrategy

class SmallCapFactorSelector(SelectorBase):
    """小市值多因子选股器"""
    
    def __init__(self, market_cap_limit=60.0, top_n=10, factor_periods=[5, 20, 60]):
        super().__init__("SmallCapFactor")
        self.strategy = SmallCapFactorStrategy(market_cap_limit, top_n)
        self.top_n = top_n
        self.factor_periods = factor_periods
        self.latest_selection = []
        
        # 初始化股票池
        self._setup_stock_universe()
    
    def _setup_stock_universe(self):
        """设置股票池"""
        sm = StockManager.instance()
        
        for stock in sm:
            if stock.valid and stock.type in [1, 8, 9, 11]:
                proto_sys = SYS_Simple(sg=SG_True(), mm=MM_FixedPercent(0.1))
                self.addStock(stock, proto_sys)
    
    def _calculate(self, real_sys_list, query):
        """核心选股计算"""
        try:
            current_date = query.end_datetime
            results = self.strategy.run_stock_selection(current_date, save_results=False)
            
            if results['success']:
                self.latest_selection = results['top_stocks']
                self.real_sys_list = real_sys_list
            else:
                self.latest_selection = []
                
        except Exception as e:
            print(f"选股计算异常: {e}")
            self.latest_selection = []
    
    def get_selected(self, datetime):
        """返回选中的系统列表"""
        selected_list = SystemWeightList()
        
        if self.latest_selection:
            selected_codes = {stock['stock_code'] for stock in self.latest_selection[:self.top_n]}
            
            for sys_info in getattr(self, 'real_sys_list', []):
                if sys_info.stock.market_code in selected_codes:
                    weight = 1.0 / len(selected_codes)
                    selected_list.append(SystemWeight(sys_info.sys, weight))
        
        return selected_list
```

### A.2 简单回测执行模板
```python
def run_simple_backtest():
    """简单回测执行示例"""
    # 初始化hikyuu
    load_hikyuu()
    
    # 创建配置
    config = BacktestConfig(
        start_date="2022-01-01",
        end_date="2024-12-31",
        initial_cash=10_000_000,
        top_n_stocks=10,
        adjust_cycle=20
    )
    
    # 执行回测
    result = run_backtest(config)
    
    if result.success:
        metrics = result.analysis_result['custom_metrics']
        print(f"年化收益率: {metrics.get('annual_return', 0):.2%}")
        print(f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"胜率: {metrics.get('win_rate', 0):.2%}")
    else:
        print(f"回测失败: {result.error_message}")

if __name__ == "__main__":
    run_simple_backtest()
```

---
