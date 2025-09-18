from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from hikyuu import *
from .mysql_manager import get_db_manager
from .factor_registry import get_factor_registry

logger = logging.getLogger(__name__)

class MultiFactorEngine:
    """MultiFactor引擎，用于批量因子计算和评估"""
    
    def __init__(self):
        self.db = get_db_manager()
        self.registry = get_factor_registry()
        self.sm = StockManager.instance()
    
    def create_factor_indicator(self, expression: str) -> Indicator:
        """
        根据表达式创建技术指标
        
        Args:
            expression: 因子表达式，如 "MA(CLOSE(), 5) - MA(CLOSE(), 20)"
            
        Returns:
            Indicator: hikyuu指标对象
        """
        try:
            # 构建安全的函数映射，使用正确的函数名称
            safe_context = {
                'MA': MA, 'EMA': EMA, 'SMA': SMA, 'WMA': WMA,
                'CLOSE': CLOSE, 'OPEN': OPEN, 'HIGH': HIGH, 'LOW': LOW,
                'VOL': VOL, 'AMO': AMO,
                'RSI': RSI, 'MACD': MACD, 'ATR': ATR, 'TA_BBANDS': TA_BBANDS,  # 使用TA_BBANDS而不是BOLL
                'HHV': HHV, 'LLV': LLV, 'REF': REF, 'STD': STD,
                'CROSS': CROSS, 'IF': IF, 'ABS': ABS, 'LOG': LOG, 'SQRT': SQRT
            }
            
            # 检查表达式中是否包含不安全的代码
            if any(char in expression for char in ['import', 'exec', 'eval', '__']):
                raise ValueError("表达式包含不安全字符")
            
            # 执行表达式
            indicator = eval(expression, safe_context)
            return indicator
            
        except NameError as e:
            # 处理未定义的函数名
            missing_function = str(e).split("'")[1]
            logger.error(f"函数未定义: {missing_function}，请检查函数名称是否正确")
            raise ValueError(f"未定义的函数: {missing_function}")
        except Exception as e:
            logger.error(f"创建因子指标失败: {expression}, 错误: {e}")
            raise
    
    def create_factor_safely(self, expression_parts: List[str]) -> Indicator:
        """
        安全地创建因子指标（推荐使用）
        避免使用eval，通过编程方式构建表达式
        
        Args:
            expression_parts: 表达式组成部分，如 ["MA", "CLOSE", "5", "-", "MA", "CLOSE", "20"]
            
        Returns:
            Indicator: hikyuu指标对象
        """
        # 这里可以实现一个安全的表达式解析器
        # 由于时间关系，暂时使用简化版本
        
        # 示例：解析简单的MA交叉表达式
        if len(expression_parts) >= 7 and expression_parts[0] == "MA" and expression_parts[3] == "-" and expression_parts[4] == "MA":
            try:
                # 解析 MA(CLOSE(), 5) - MA(CLOSE(), 20)
                ma1_period = int(expression_parts[2].strip('()'))
                ma2_period = int(expression_parts[6].strip('()'))
                
                ma1 = MA(CLOSE(), ma1_period)
                ma2 = MA(CLOSE(), ma2_period)
                return ma1 - ma2
                
            except (ValueError, IndexError):
                logger.error("无法解析表达式格式")
                raise
        
        # 可以继续添加其他表达式的解析逻辑
        logger.error("不支持的表达式格式")
        raise ValueError("不支持的表达式格式")
    
    def batch_evaluate_factors(self, factor_ids: List[int], 
                              stock_list: List[Stock] = None,
                              query: Query = None) -> Dict[int, Dict[str, Any]]:
        """
        批量评估多个因子
        
        Args:
            factor_ids: 因子ID列表
            stock_list: 股票列表，如果为None则使用所有A股
            query: 查询条件，如果为None则使用最近100条数据
            
        Returns:
            Dict: 每个因子的评估结果
        """
        if stock_list is None:
            stock_list = self._get_a_stocks()
        
        if query is None:
            query = Query(-100)  # 最近100条数据
        
        results = {}
        
        for factor_id in factor_ids:
            try:
                factor_info = self.registry.get_factor(factor_id)
                if not factor_info:
                    logger.warning(f"因子不存在: {factor_id}")
                    continue
                
                result = self.evaluate_single_factor(
                    factor_info['expression'], stock_list, query
                )
                
                results[factor_id] = {
                    'factor_info': factor_info,
                    'evaluation_result': result
                }
                
                logger.info(f"因子评估完成: {factor_info['name']}")
                
            except Exception as e:
                logger.error(f"因子评估失败: {factor_id}, 错误: {e}")
                results[factor_id] = {'error': str(e)}
        
        return results
    
    def evaluate_single_factor(self, expression: str, 
                             stock_list: List[Stock],
                             query: Query) -> Dict[str, Any]:
        """
        评估单个因子
        
        Args:
            expression: 因子表达式
            stock_list: 股票列表
            query: 查询条件
            
        Returns:
            Dict: 评估结果
        """
        try:
            # 创建因子指标
            factor_indicator = self.create_factor_indicator(expression)
            
            # 创建MultiFactor
            src_inds = [factor_indicator]  # IndicatorList就是普通的Python列表
            ref_stk = stock_list[0] if stock_list else self.sm['sh000001']
            
            multifactor = MF_EqualWeight(src_inds, stock_list, query, ref_stk, save_all_factors=True)
            
            # 计算因子值
            all_factors = multifactor.get_all_factors()
            
            # 获取IC和ICIR
            ic_series = multifactor.get_ic()
            icir_series = multifactor.get_icir(20)  # 20日窗口
            
            # 计算统计指标
            ic_values = [float(ic) for ic in ic_series if ic is not None]
            icir_values = [float(icir) for icir in icir_series if icir is not None]
            
            # 返回评估结果
            return {
                'ic_mean': sum(ic_values) / len(ic_values) if ic_values else 0,
                'ic_std': self._calculate_std(ic_values) if ic_values else 0,
                'icir_mean': sum(icir_values) / len(icir_values) if icir_values else 0,
                'factor_values': all_factors,
                'stock_count': len(stock_list),
                'evaluation_date': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"单因子评估失败: {expression}, 错误: {e}")
            raise
    
    def run_backtest_for_factor(self, factor_id: int, 
                               initial_cash: float = 1000000,
                               query: Query = None) -> Dict[str, Any]:
        """
        运行因子回测
        
        Args:
            factor_id: 因子ID
            initial_cash: 初始资金
            query: 查询条件
            
        Returns:
            Dict: 回测结果
        """
        factor_info = self.registry.get_factor(factor_id)
        if not factor_info:
            raise ValueError(f"因子不存在: {factor_id}")
        
        if query is None:
            query = Query(-252)  # 最近一年数据
        
        try:
            # 创建交易账户
            tm = crtTM(init_cash=initial_cash, name=f"factor_{factor_id}")
            
            # 创建因子指标
            factor_indicator = self.create_factor_indicator(factor_info['expression'])
            
            # 创建信号指示器（基于因子值的简单策略）
            # 这里使用因子值排名前10%的股票
            sg = self._create_factor_signal(factor_indicator)
            
            # 创建交易系统
            mm = MM_FixedPercent(0.1)  # 每次投入10%资金
            st = ST_FixedPercent(0.05)  # 5%止损
            
            sys = SYS_Simple(tm=tm, sg=sg, mm=mm, st=st)
            
            # 运行回测（使用第一个股票作为示例）
            sample_stock = self.sm['sz000001']
            sys.run(sample_stock, query)
            
            # 获取绩效结果
            performance = tm.get_performance(Datetime.now(), Query.DAY)
            trade_list = tm.get_trade_list()
            
            # 提取关键指标
            performance_dict = {}
            if hasattr(performance, 'names') and hasattr(performance, 'values'):
                names = performance.names()
                values = performance.values()
                performance_dict = dict(zip(names, values))
            
            return {
                'factor_id': factor_id,
                'performance': performance_dict,
                'trade_count': len(trade_list),
                'final_cash': tm.currentCash,
                'backtest_date': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"因子回测失败: {factor_id}, 错误: {e}")
            raise
    
    def _create_factor_signal(self, factor_indicator: Indicator) -> SignalBase:
        """创建基于因子值的信号指示器"""
        # 简化的信号生成：因子值大于0时买入
        condition = factor_indicator > 0
        return SG_Bool(condition)
    
    def _get_a_stocks(self) -> List[Stock]:
        """获取所有A股股票"""
        from hikyuu import constant
        
        a_stocks = []
        
        # 直接迭代StockManager实例来获取所有股票
        for stock in self.sm:
            # 检查股票是否为Null对象
            if stock.is_null():
                continue
                
            # 检查股票是否有效且为A股
            if stock.valid and stock.type in (constant.STOCKTYPE_A, constant.STOCKTYPE_A_BJ):
                a_stocks.append(stock)
        
        return a_stocks
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def auto_evaluate_all_factors(self):
        """自动评估所有测试中的因子"""
        testing_factors = self.registry.get_testing_factors()
        logger.info(f"开始自动评估 {len(testing_factors)} 个测试因子")
        
        for factor in testing_factors:
            try:
                # 评估因子
                evaluation_result = self.evaluate_single_factor(
                    factor['expression'], self._get_a_stocks(), Query(-100)
                )
                
                # 保存绩效结果
                self.registry.save_performance_result(
                    factor_id=factor['id'],
                    evaluation_date=datetime.now(),
                    ic_value=evaluation_result['ic_mean'],
                    icir_value=evaluation_result['icir_mean']
                )
                
                # 如果IC均值显著大于0，激活因子
                if evaluation_result['ic_mean'] > 0.05:  # IC大于5%
                    self.registry.update_factor(
                        factor['id'], status='active'
                    )
                    logger.info(f"因子激活: {factor['name']} (IC: {evaluation_result['ic_mean']:.3f})")
                else:
                    logger.info(f"因子保持测试状态: {factor['name']} (IC: {evaluation_result['ic_mean']:.3f})")
                    
            except Exception as e:
                logger.error(f"自动评估失败: {factor['name']}, 错误: {e}")
        
        logger.info("自动评估完成")


# 全局MultiFactor引擎实例
multi_factor_engine = None

def get_multi_factor_engine() -> MultiFactorEngine:
    """获取全局MultiFactor引擎实例"""
    global multi_factor_engine
    if multi_factor_engine is None:
        multi_factor_engine = MultiFactorEngine()
    return multi_factor_engine


if __name__ == "__main__":
    # 测试MultiFactor引擎
    engine = get_multi_factor_engine()
    
    # 测试创建因子指标
    try:
        indicator = engine.create_factor_indicator("MA(CLOSE(), 5) - MA(CLOSE(), 20)")
        print("因子指标创建成功")
    except Exception as e:
        print(f"因子指标创建失败: {e}")
    
    # 测试获取A股列表
    a_stocks = engine._get_a_stocks()
    print(f"A股数量: {len(a_stocks)}")
