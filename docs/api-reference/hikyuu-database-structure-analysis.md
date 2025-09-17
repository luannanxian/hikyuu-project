# Hikyuu数据库结构分析

## 概述

通过MySQL MCP服务器对hikyuu数据库结构的深入分析，本文档详细说明了数据库的组织方式、表结构和数据含义，为hikyuu量化交易编程提供重要参考。

## 数据库架构

### 1. 数据库分类

Hikyuu使用分层数据库架构，按交易所和时间周期进行组织：

#### 交易所分类
- **SH (上海证券交易所)**: `sh_*` 系列数据库
- **SZ (深圳证券交易所)**: `sz_*` 系列数据库  
- **BJ (北京证券交易所)**: `bj_*` 系列数据库
- **HKU_BASE (基础数据库)**: `hku_base` - 存储元数据和基础信息

#### 时间周期分类
每个交易所按时间周期分为以下数据库：
- `*_day` - 日线数据
- `*_week` - 周线数据
- `*_month` - 月线数据
- `*_quarter` - 季线数据
- `*_halfyear` - 半年线数据
- `*_year` - 年线数据
- `*_min` - 1分钟数据
- `*_min5` - 5分钟数据
- `*_min15` - 15分钟数据
- `*_min30` - 30分钟数据
- `*_min60` - 60分钟数据
- `*_hour2` - 2小时数据
- `*_time` - 时间数据
- `*_trans` - 交易数据

### 2. 基础数据库 (hku_base)

#### 核心表结构

**stock表** - 股票基本信息
```sql
Field       Type                  Description
stockid     int(10) unsigned      股票ID (主键，自增)
marketid    int(10) unsigned      市场ID
code        varchar(20)           股票代码
name        varchar(60)           股票名称
type        int(10) unsigned      股票类型
valid       int(10) unsigned      是否有效
startDate   bigint(20) unsigned   开始日期
endDate     bigint(20) unsigned   结束日期
```

**market表** - 市场信息
```sql
Field       Type       Description
marketid    int        市场ID
market      varchar    市场代码 (SH/SZ/BJ)
name        varchar    市场名称
description varchar    市场描述
code        varchar    指数代码
lastDate    int        最后更新日期
openTime1   int        上午开盘时间 (930)
closeTime1  int        上午收盘时间 (1130)
openTime2   int        下午开盘时间 (1300)
closeTime2  int        下午收盘时间 (1500)
```

#### 详细表分析

**block表** - 板块分类信息
```sql
Field         Type           Description
id            int unsigned   主键ID
category      varchar(100)   板块类别 (如：行业板块)
name          varchar(100)   板块名称 (如：航天航空)
market_code   varchar(30)    股票市场代码 (如：SZ302132)
```
用途：管理股票的行业板块分类，支持板块轮动分析

**BlockIndex表** - 板块索引表
结构与block表相同，但当前为空表，可能用于板块指数数据

**holiday表** - 交易日历
```sql
Field    Type           Description
id       int unsigned   主键ID
date     bigint         节假日期 (格式：YYYYMMDD)
```
数据示例：20210101(元旦), 20210211-20210217(春节)等
用途：确定交易日，排除节假日进行回测分析

**stocktypeinfo表** - 股票类型配置
```sql
Field           Type           Description
id              int unsigned   类型ID
type            int unsigned   股票类型编号
precision       int            价格精度
tick            double         最小变动单位
tickValue       double         最小变动价值
minTradeNumber  double         最小交易数量
maxTradeNumber  double         最大交易数量
description     varchar(100)   类型描述
```

股票类型详细说明：
- Type 0: Block (板块)
- Type 1: A股 (精度2位，tick=0.01，最小100股)
- Type 2: 指数 (精度3位，tick=0.001，最小1股)
- Type 3: B股 (精度3位，tick=0.001，最小100股)
- Type 4: 基金 (精度3位，tick=0.001，最小100股)
- Type 5: ETF (精度3位，tick=0.001，最小1000股)
- Type 6: 国债 (精度2位，tick=0.01，最小10股)
- Type 7: 其他债券 (精度2位，tick=0.01，最小10股)
- Type 8: 创业板 (精度2位，tick=0.01，最小100股)
- Type 9: 科创板 (精度2位，tick=0.01，最小1股)
- Type 11: 北交所 (精度2位，tick=0.01，最小1股)

**coderuletype表** - 股票代码规则
```sql
Field       Type           Description
id          int unsigned   规则ID
marketid    int unsigned   市场ID
codepre     varchar(20)    代码前缀
TYPE        int unsigned   股票类型
description varchar(100)   规则描述
```

代码前缀规则示例：
- 上海：60(A股), 000(指数), 688(科创板), 51/56/58(ETF)
- 深圳：00(A股), 39(指数), 300/301/302(创业板), 159(ETF)
- 北京：43/83/87/88/92(A股), 899(指数)

**stkfinance表** - 股票财务数据
包含37个财务指标字段：
- 基本信息：stockid, updated_date, ipo_date
- 股本结构：zongguben(总股本), liutongguben(流通股本)
- 资产负债：zongzichan(总资产), jingzichan(净资产)
- 损益数据：zhuyingshouru(主营收入), jinglirun(净利润)
- 现金流量：jingyingxianjinliu(经营现金流)

数据示例显示大部分财务数据为0，仅股本数据有值，表明财务数据可能需要额外数据源

**version表** - 数据库版本
```sql
Field    Type    Description
version  int     当前数据库版本号
```
当前版本：27

**stkweight表** - 股票权重与分红除权数据
```sql
Field               Type           Description
id                  int unsigned   主键ID
stockid             int unsigned   股票ID
date                bigint         日期 (格式：YYYYMMDD)
countAsGift         double         送股数量
countForSell        double         配股数量
priceForSell        double         配股价格
bonus               double         分红金额
countOfIncreasement double         增发数量
totalCount          double         总股本
freeCount           double         流通股本
suogu               double         锁股数量
```
数据示例：记录股票的分红送配、股本变化等除权除息信息
用途：计算复权价格，进行准确的技术分析和回测

**HistoryFinanceField表** - 财务字段定义字典
包含581个财务指标的完整定义，涵盖：
- 每股指标：基本每股收益、每股净资产、每股经营现金流等
- 资产负债表：全部科目详细定义（流动资产、非流动资产、各类负债等）
- 利润表：从营业收入到净利润的完整损益科目
- 现金流量表：经营、投资、筹资三大活动现金流
- 财务比率：偿债能力、营运能力、成长能力、盈利能力分析指标
- 股本股东：股东结构、机构持股、北上资金等
- 业绩预告：业绩预告和快报相关字段

用途：作为财务数据的字典表，定义每个财务指标的含义

**zh_bond10表** - 中国10年期国债收益率
```sql
Field    Type           Description
id       int unsigned   主键ID
date     bigint         日期 (格式：YYYYMMDD)
value    int            收益率 (基点，需除以10000得到百分比)
```
数据示例：20020104日收益率32096基点(约3.21%)
用途：作为无风险利率基准，用于计算夏普比率、资本资产定价模型等

#### 其他表说明
- `HistoryFinance` - 历史财务数据存储表
- `HistoryFinance_copy1` - 历史财务数据备份表
- `test_transactions` - 测试交易数据表

### 3. 交易数据表结构

每个股票在各时间周期数据库中对应一个以股票代码命名的表，如`600000`表：

#### K线数据结构
```sql
Field    Type                  Description
date     bigint(20) unsigned   日期时间 (格式: YYYYMMDDHHMI)
open     double unsigned       开盘价
high     double unsigned       最高价
low      double unsigned       最低价
close    double unsigned       收盘价
amount   double unsigned       成交金额
count    double unsigned       成交量
```

#### 数据示例 (600000 - 浦发银行)
```
日期: 202508220000
开盘: 13.81, 最高: 13.95, 最低: 13.77, 收盘: 13.94
成交金额: 888813.248千元, 成交量: 640980手
```

### 4. 数据含义解析

#### 日期格式
- 日线数据: `YYYYMMDD0000` (如: 202508220000)
- 分钟数据: `YYYYMMDDHHMM` (如: 202508221030表示10:30)

#### 价格单位
- 所有价格数据以元为单位
- 精确到小数点后2位

#### 成交数据
- `amount`: 成交金额，单位为千元
- `count`: 成交量，单位为手 (100股为1手)

### 5. 编程应用指导

#### 数据库连接策略
```python
# 基础信息查询
base_db = "hku_base"

# 交易数据查询 (根据需求选择)
market = "sh"  # sh/sz/bj
period = "day"  # day/min/min5等
trading_db = f"{market}_{period}"
```

#### 常用查询模式
1. **获取股票基本信息**
   ```sql
   SELECT * FROM hku_base.stock WHERE code = '600000'
   ```

2. **获取最新K线数据**
   ```sql
   SELECT * FROM sh_day.`600000` ORDER BY date DESC LIMIT 10
   ```

3. **查询特定时间段数据**
   ```sql
   SELECT * FROM sh_day.`600000` 
   WHERE date >= 20250801 AND date <= 20250825
   ORDER BY date ASC
   ```

### 6. 重要注意事项

1. **股票代码作为表名**: 每个股票对应一个表，表名为股票代码
2. **数据分离**: 不同时间周期的数据存储在不同数据库中
3. **市场区分**: 三大交易所数据完全分离
4. **数据完整性**: 基础信息在hku_base中统一管理
5. **时间格式**: 统一使用数字格式存储日期时间

### 7. 数据库使用最佳实践

#### 编程前的数据库查询
在进行hikyuu量化编程前，应当：
1. 查询`hku_base.market`了解可用市场
2. 查询`hku_base.stock`确认股票代码和基本信息
3. 根据分析需求选择合适的时间周期数据库
4. 理解目标股票的数据范围和质量

#### 性能优化建议
1. 使用日期字段建立索引进行范围查询
2. 避免跨数据库JOIN操作
3. 合理选择时间周期避免数据冗余
4. 缓存基础信息减少重复查询

## 总结

Hikyuu数据库采用了高度结构化的设计，通过交易所和时间周期的分层组织，实现了高效的数据存储和查询。理解这一结构对于编写高效的量化交易程序至关重要。在编程前进行数据库结构分析，可以避免常见的API使用错误，提高代码的稳定性和性能。
