from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import schedule
import time
from hikyuu import *
from .mysql_manager import get_db_manager
from .factor_registry import get_factor_registry
from .multi_factor_engine import get_multi_factor_engine

logger = logging.getLogger(__name__)

class EvaluationPipeline:
    """评估流水线，负责自动化因子评估和回测"""
    
    def __init__(self):
        self.db = get_db_manager()
        self.registry = get_factor_registry()
        self.engine = get_multi_factor_engine()
        self.sm = StockManager.instance()
    
    def run_daily_evaluation(self):
        """运行每日因子评估"""
        logger.info("开始每日因子评估")
        
        # 获取所有测试中和活跃的因子
        factors_to_evaluate = (
            self.registry.get_testing_factors() + 
            self.registry.get_active_factors()
        )
        
        logger.info(f"需要评估的因子数量: {len(factors_to_evaluate)}")
        
        # 获取A股列表
        a_stocks = self._get_a_stocks()
        logger.info(f"A股数量: {len(a_stocks)}")
        
        # 设置查询条件（最近100个交易日）
        query = Query(-100)
        
        evaluation_results = {}
        
        for factor in factors_to_evaluate:
            try:
                # 评估因子
                result = self.engine.evaluate_single_factor(
                    factor['expression'], a_stocks, query
                )
                
                # 保存绩效结果
                performance_id = self.registry.save_performance_result(
                    factor_id=factor['id'],
                    evaluation_date=datetime.now().date(),
                    ic_value=result['ic_mean'],
                    icir_value=result['icir_mean']
                )
                
                evaluation_results[factor['id']] = {
                    'factor_name': factor['name'],
                    'ic_value': result['ic_mean'],
                    'icir_value': result['icir_mean'],
                    'performance_id': performance_id
                }
                
                logger.info(
                    f"因子评估完成: {factor['name']} - "
                    f"IC: {result['ic_mean']:.4f}, "
                    f"ICIR: {result['icir_mean']:.4f}"
                )
                
                # 根据IC值更新因子状态
                if result['ic_mean'] > 0.05:  # IC大于5%，激活因子
                    self.registry.update_factor(factor['id'], status='active')
                    logger.info(f"因子激活: {factor['name']}")
                elif result['ic_mean'] < 0.01:  # IC小于1%，标记为待观察
                    self.registry.update_factor(factor['id'], status='testing')
                    logger.info(f"因子标记为测试: {factor['name']}")
                
            except Exception as e:
                logger.error(f"因子评估失败: {factor['name']}, 错误: {e}")
                evaluation_results[factor['id']] = {'error': str(e)}
        
        logger.info("每日因子评估完成")
        return evaluation_results
    
    def run_weekly_backtest(self):
        """运行每周回测"""
        logger.info("开始每周回测")
        
        # 获取所有活跃因子
        active_factors = self.registry.get_active_factors()
        logger.info(f"活跃因子数量: {len(active_factors)}")
        
        # 设置查询条件（最近一年数据）
        query = Query(-252)
        
        backtest_results = {}
        
        for factor in active_factors:
            try:
                # 运行回测
                result = self.engine.run_backtest_for_factor(
                    factor['id'], initial_cash=1000000, query=query
                )
                
                # 保存回测结果
                backtest_id = self.registry.save_backtest_result(
                    factor_id=factor['id'],
                    backtest_date=datetime.now().date(),
                    total_return=result['performance'].get('总收益率', 0),
                    annual_return=result['performance'].get('年化收益率', 0),
                    volatility=result['performance'].get('年化波动率', 0),
                    sharpe_ratio=result['performance'].get('夏普比率', 0),
                    max_drawdown=result['performance'].get('最大回撤', 0),
                    trade_count=result['trade_count'],
                    win_rate=result['performance'].get('胜率', 0)
                )
                
                backtest_results[factor['id']] = {
                    'factor_name': factor['name'],
                    'annual_return': result['performance'].get('年化收益率', 0),
                    'sharpe_ratio': result['performance'].get('夏普比率', 0),
                    'max_drawdown': result['performance'].get('最大回撤', 0),
                    'backtest_id': backtest_id
                }
                
                logger.info(
                    f"回测完成: {factor['name']} - "
                    f"年化收益: {result['performance'].get('年化收益率', 0):.2%}, "
                    f"夏普比率: {result['performance'].get('夏普比率', 0):.2f}"
                )
                
            except Exception as e:
                logger.error(f"回测失败: {factor['name']}, 错误: {e}")
                backtest_results[factor['id']] = {'error': str(e)}
        
        logger.info("每周回测完成")
        return backtest_results
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """生成绩效报告"""
        logger.info("生成绩效报告")
        
        report = {
            'generation_date': datetime.now(),
            'factor_stats': {},
            'performance_summary': {}
        }
        
        # 获取因子统计
        total_factors = self.registry.get_all_factors()
        active_factors = self.registry.get_active_factors()
        testing_factors = self.registry.get_testing_factors()
        
        report['factor_stats'] = {
            'total': len(total_factors),
            'active': len(active_factors),
            'testing': len(testing_factors),
            'inactive': len(total_factors) - len(active_factors) - len(testing_factors)
        }
        
        # 计算平均绩效指标
        active_factor_ids = [f['id'] for f in active_factors]
        if active_factor_ids:
            performance_stats = []
            for factor_id in active_factor_ids:
                stats = self.db.get_factor_performance_stats(factor_id)
                if stats and stats['evaluation_count'] > 0:
                    performance_stats.append(stats)
            
            if performance_stats:
                report['performance_summary'] = {
                    'avg_ic': sum(s['avg_ic'] or 0 for s in performance_stats) / len(performance_stats),
                    'avg_icir': sum(s['avg_icir'] or 0 for s in performance_stats) / len(performance_stats),
                    'avg_annual_return': sum(s['avg_annual_return'] or 0 for s in performance_stats) / len(performance_stats),
                    'avg_sharpe_ratio': sum(s['avg_sharpe_ratio'] or 0 for s in performance_stats) / len(performance_stats),
                    'total_evaluations': sum(s['evaluation_count'] or 0 for s in performance_stats)
                }
        
        logger.info("绩效报告生成完成")
        return report
    
    def start_scheduled_tasks(self):
        """启动定时任务"""
        logger.info("启动定时任务调度器")
        
        # 每日下午4点运行因子评估
        schedule.every().day.at("16:00").do(self.run_daily_evaluation)
        
        # 每周五下午5点运行回测
        schedule.every().friday.at("17:00").do(self.run_weekly_backtest)
        
        # 每月第一天生成绩效报告
        schedule.every().month.at("09:00").do(self.generate_performance_report)
        
        logger.info("定时任务已安排: 每日16:00评估, 每周五17:00回测, 每月1日9:00报告")
        
        # 运行调度器
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("定时任务调度器已停止")
    
    def _get_a_stocks(self) -> List[Stock]:
        """获取所有A股股票"""
        a_stocks = []
        for i in range(len(self.sm)):
            stock = self.sm[i]
            if stock.valid and stock.type == 1:  # A股
                a_stocks.append(stock)
        return a_stocks
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """清理旧数据"""
        logger.info(f"开始清理 {days_to_keep} 天前的数据")
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date()
        
        try:
            # 清理绩效数据
            performance_query = "DELETE FROM factor_performance WHERE evaluation_date < %s"
            performance_deleted = self.db.execute_update(performance_query, (cutoff_date,))
            
            # 清理回测数据
            backtest_query = "DELETE FROM backtest_results WHERE backtest_date < %s"
            backtest_deleted = self.db.execute_update(backtest_query, (cutoff_date,))
            
            logger.info(
                f"数据清理完成: "
                f"删除 {performance_deleted} 条绩效记录, "
                f"删除 {backtest_deleted} 条回测记录"
            )
            
            return {
                'performance_deleted': performance_deleted,
                'backtest_deleted': backtest_deleted
            }
            
        except Exception as e:
            logger.error(f"数据清理失败: {e}")
            return {'error': str(e)}


# 全局评估流水线实例
evaluation_pipeline = None

def get_evaluation_pipeline() -> EvaluationPipeline:
    """获取全局评估流水线实例"""
    global evaluation_pipeline
    if evaluation_pipeline is None:
        evaluation_pipeline = EvaluationPipeline()
    return evaluation_pipeline


if __name__ == "__main__":
    # 测试评估流水线
    pipeline = get_evaluation_pipeline()
    
    # 测试每日评估
    print("运行每日因子评估...")
    results = pipeline.run_daily_evaluation()
    print(f"评估完成: {len(results)} 个因子")
    
    # 测试生成报告
    print("生成绩效报告...")
    report = pipeline.generate_performance_report()
    print(f"报告生成完成: {report}")
