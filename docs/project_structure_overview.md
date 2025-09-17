# Hikyuu量化交易策略项目结构概览

## 项目总体结构

```
hikyuu-project/
├── docs/                          # 文档目录
│   ├── hikyuu-api-usage-guide.md       # Hikyuu API使用指南
│   ├── hikyuu-database-structure-analysis.md  # 数据库结构分析
│   ├── hikyuu-framework-analysis.md     # 框架分析
│   ├── hikyuu-python-api-reference.md  # Python API参考
│   ├── mysql-server.md                 # MySQL服务器配置
│   └── example-code/
│       └── hikyuu_programming_examples.py  # 编程示例
├── strategy_implementation/        # 策略实现模块 ✅ 已完成
│   ├── __init__.py                     # 模块初始化
│   ├── factor_calculation.py           # 多因子计算
│   ├── scoring_system.py              # 评分系统
│   ├── stock_screening.py             # 股票筛选
│   └── main_strategy.py               # 主策略类
├── backtest_system/                # 回测系统 🚧 待实现
│   ├── __init__.py
│   ├── selector.py                     # 策略选择器
│   ├── portfolio.py                   # 投资组合管理
│   ├── performance.py                 # 绩效分析
│   ├── report.py                      # 报告生成
│   └── visualization.py              # 可视化
├── tests/                         # 测试和调试 ✅ 已有部分
│   ├── debug_factors.py               # 因子调试
│   ├── debug_scoring.py               # 评分调试
│   ├── test_market_cap.py             # 市值测试
│   └── test_index_exclusion.py        # 指数排除测试
├── config/                        # 配置文件 🚧 待创建
│   ├── strategy_config.py             # 策略配置
│   └── backtest_config.py             # 回测配置
├── data/                          # 数据目录 🚧 待创建
│   ├── output/                        # 输出结果
│   └── temp/                          # 临时文件
├── requirements_analysis.md        # 需求分析 ✅ 已完成
├── strategy_specification.md       # 策略规格说明 ✅ 已完成
├── backtest_system_design.md       # 回测系统设计 ✅ 已完成
├── run_strategy.py                 # 策略运行入口 ✅ 已完成
└── README.md                       # 项目说明
```

## 当前实现状态

### ✅ 已完成的核心策略模块
1. **多因子计算系统** (`strategy_implementation/factor_calculation.py`)
   - 技术因子：RSI、MACD、MA偏离度、ATR、布林带
   - 结构因子：成交量、换手率、资金流
   - 交互因子：动量×流动性、突破×资金流等
   - 状态：完全实现，经过测试验证

2. **评分系统** (`strategy_implementation/scoring_system.py`)
   - Z-score标准化
   - 横截面因子排序评分
   - 综合因子得分计算
   - 状态：完全实现，修复了序列化和评分bugs

3. **股票筛选系统** (`strategy_implementation/stock_screening.py`)
   - 小盘股筛选（市值<600亿）
   - 指数成分股排除
   - 交易状态过滤
   - 状态：完全实现，正确使用ZONGGUBEN指标

4. **主策略类** (`strategy_implementation/main_strategy.py`)
   - 策略流程编排
   - 中文因子名称本地化
   - JSON序列化输出
   - 状态：完全实现，平均得分84.75，运行正常

### 🚧 待实现的回测系统
根据 `backtest_system_design.md` 设计文档，需要实现：

1. **策略选择器** (`backtest_system/selector.py`)
   - 继承hikyuu.SelectorBase
   - 实现_calculate()和get_selected()方法
   - 集成现有策略逻辑

2. **投资组合管理** (`backtest_system/portfolio.py`)
   - Portfolio配置和管理
   - 资金分配策略
   - 仓位控制

3. **绩效分析** (`backtest_system/performance.py`)
   - 收益率计算
   - 风险指标（夏普比率、最大回撤等）
   - 基准比较

4. **报告生成** (`backtest_system/report.py`)
   - 中文回测报告
   - 绩效统计表格
   - 交易明细

5. **可视化** (`backtest_system/visualization.py`)
   - 净值曲线图
   - 回撤图表
   - 因子分析图

## 技术架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Hikyuu 量化交易系统                        │
├─────────────────────────────────────────────────────────────┤
│                      回测系统层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   选择器     │  │  投资组合    │  │   绩效分析   │         │
│  │  Selector   │  │  Portfolio  │  │ Performance │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                      策略实现层 ✅                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   因子计算   │  │   评分系统   │  │   股票筛选   │         │
│  │   Factors   │  │   Scoring   │  │  Screening  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                      Hikyuu 框架层                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    数据源    │  │    指标库    │  │   交易管理   │         │
│  │ DataSource  │  │ Indicators  │  │TradeManager │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 集成要点

### 1. 数据流向
```
原始数据 → 因子计算 → 评分排序 → 股票筛选 → 策略选择器 → 投资组合 → 绩效分析
```

### 2. 关键接口
- **策略到回测**：`main_strategy.py` → `selector.py`
- **选择器到组合**：`SelectorBase.get_selected()` → `Portfolio`
- **组合到分析**：`Portfolio.performance` → `performance.py`

### 3. 配置管理
- 策略参数配置（因子权重、筛选条件）
- 回测参数配置（起止时间、资金规模、交易费用）

## 下一步实施计划

1. **创建目录结构**
   ```bash
   mkdir -p backtest_system config data/output data/temp
   ```

2. **按优先级实现回测组件**
   - Phase 1: `selector.py` - 策略选择器（核心）
   - Phase 2: `portfolio.py` - 投资组合管理
   - Phase 3: `performance.py` - 绩效分析
   - Phase 4: `report.py` - 报告生成
   - Phase 5: `visualization.py` - 可视化

3. **创建统一入口**
   - `run_backtest.py` - 回测运行脚本
   - 集成策略和回测流程

## 优势特点

✅ **已验证的策略核心**：多因子模型完整实现并测试通过
✅ **标准化架构**：遵循hikyuu框架设计模式
✅ **中文本地化**：因子名称和报告完全中文化
✅ **模块化设计**：各组件独立，便于测试和维护
✅ **完整设计文档**：详细的回测系统设计规格

## 确认事项

请确认以下几点：
1. 项目结构是否符合预期？
2. 策略实现模块的完成度是否满意？
3. 回测系统的设计是否合理？
4. 是否需要调整任何组件的设计？

确认后即可开始回测系统的具体实现。
