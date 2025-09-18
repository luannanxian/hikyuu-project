from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
from .mysql_manager import get_db_manager

logger = logging.getLogger(__name__)

class FactorRegistry:
    """因子注册器，管理因子的增删改查"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def register_factor(self, name: str, expression: str, category: str = None, 
                       description: str = None, status: str = 'testing') -> int:
        """
        注册新因子
        
        Args:
            name: 因子名称
            expression: 因子表达式
            category: 因子类别
            description: 因子描述
            status: 因子状态 (active/testing/inactive)
            
        Returns:
            int: 因子ID
        """
        query = """
        INSERT INTO factors (name, expression, category, status, description)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        try:
            factor_id = self.db.execute_insert(
                query, (name, expression, category, status, description)
            )
            logger.info(f"因子注册成功: {name} (ID: {factor_id})")
            return factor_id
        except Exception as e:
            logger.error(f"因子注册失败: {e}")
            raise
    
    def update_factor(self, factor_id: int, **kwargs) -> bool:
        """
        更新因子信息
        
        Args:
            factor_id: 因子ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        if not kwargs:
            return False
        
        set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        query = f"UPDATE factors SET {set_clause} WHERE id = %s"
        params = list(kwargs.values()) + [factor_id]
        
        try:
            affected_rows = self.db.execute_update(query, tuple(params))
            success = affected_rows > 0
            if success:
                logger.info(f"因子更新成功: ID {factor_id}")
            else:
                logger.warning(f"因子更新失败: ID {factor_id} 不存在")
            return success
        except Exception as e:
            logger.error(f"因子更新失败: {e}")
            return False
    
    def delete_factor(self, factor_id: int) -> bool:
        """
        删除因子
        
        Args:
            factor_id: 因子ID
            
        Returns:
            bool: 是否删除成功
        """
        query = "DELETE FROM factors WHERE id = %s"
        
        try:
            affected_rows = self.db.execute_update(query, (factor_id,))
            success = affected_rows > 0
            if success:
                logger.info(f"因子删除成功: ID {factor_id}")
            else:
                logger.warning(f"因子删除失败: ID {factor_id} 不存在")
            return success
        except Exception as e:
            logger.error(f"因子删除失败: {e}")
            return False
    
    def get_factor(self, factor_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个因子信息
        
        Args:
            factor_id: 因子ID
            
        Returns:
            Optional[Dict]: 因子信息字典
        """
        query = "SELECT * FROM factors WHERE id = %s"
        
        try:
            result = self.db.execute_query(query, (factor_id,))
            if result:
                return self._format_factor_result(result[0])
            return None
        except Exception as e:
            logger.error(f"获取因子失败: {e}")
            return None
    
    def get_factor_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取因子信息
        
        Args:
            name: 因子名称
            
        Returns:
            Optional[Dict]: 因子信息字典
        """
        query = "SELECT * FROM factors WHERE name = %s"
        
        try:
            result = self.db.execute_query(query, (name,))
            if result:
                return self._format_factor_result(result[0])
            return None
        except Exception as e:
            logger.error(f"获取因子失败: {e}")
            return None
    
    def get_all_factors(self, status: str = None, category: str = None) -> List[Dict[str, Any]]:
        """
        获取所有因子信息
        
        Args:
            status: 筛选状态
            category: 筛选类别
            
        Returns:
            List[Dict]: 因子信息列表
        """
        query = "SELECT * FROM factors WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        query += " ORDER BY created_date DESC"
        
        try:
            results = self.db.execute_query(query, tuple(params) if params else None)
            return [self._format_factor_result(row) for row in results]
        except Exception as e:
            logger.error(f"获取因子列表失败: {e}")
            return []
    
    def get_active_factors(self) -> List[Dict[str, Any]]:
        """
        获取所有活跃因子
        
        Returns:
            List[Dict]: 活跃因子列表
        """
        return self.get_all_factors(status='active')
    
    def get_testing_factors(self) -> List[Dict[str, Any]]:
        """
        获取所有测试中的因子
        
        Returns:
            List[Dict]: 测试因子列表
        """
        return self.get_all_factors(status='testing')
    
    def search_factors(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索因子
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        query = """
        SELECT * FROM factors 
        WHERE name LIKE %s OR expression LIKE %s OR description LIKE %s
        ORDER BY created_date DESC
        """
        search_pattern = f"%{keyword}%"
        
        try:
            results = self.db.execute_query(query, (search_pattern, search_pattern, search_pattern))
            return [self._format_factor_result(row) for row in results]
        except Exception as e:
            logger.error(f"搜索因子失败: {e}")
            return []
    
    def _format_factor_result(self, row: tuple) -> Dict[str, Any]:
        """格式化数据库查询结果"""
        return {
            'id': row[0],
            'name': row[1],
            'expression': row[2],
            'category': row[3],
            'created_date': row[4],
            'status': row[5],
            'description': row[6]
        }
    
    def save_performance_result(self, factor_id: int, evaluation_date: datetime,
                              ic_value: float = None, icir_value: float = None,
                              annual_return: float = None, sharpe_ratio: float = None,
                              max_drawdown: float = None, information_ratio: float = None) -> int:
        """
        保存因子绩效结果
        
        Args:
            factor_id: 因子ID
            evaluation_date: 评估日期
            ic_value: IC值
            icir_value: ICIR值
            annual_return: 年化收益率
            sharpe_ratio: 夏普比率
            max_drawdown: 最大回撤
            information_ratio: 信息比率
            
        Returns:
            int: 绩效记录ID
        """
        query = """
        INSERT INTO factor_performance 
        (factor_id, evaluation_date, ic_value, icir_value, annual_return, 
         sharpe_ratio, max_drawdown, information_ratio)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            factor_id, evaluation_date, ic_value, icir_value, 
            annual_return, sharpe_ratio, max_drawdown, information_ratio
        )
        
        try:
            performance_id = self.db.execute_insert(query, params)
            logger.info(f"因子绩效保存成功: 因子ID {factor_id}, 记录ID {performance_id}")
            return performance_id
        except Exception as e:
            logger.error(f"因子绩效保存失败: {e}")
            raise
    
    def save_backtest_result(self, factor_id: int, backtest_date: datetime,
                           total_return: float = None, annual_return: float = None,
                           volatility: float = None, sharpe_ratio: float = None,
                           max_drawdown: float = None, trade_count: int = None,
                           win_rate: float = None) -> int:
        """
        保存回测结果
        
        Args:
            factor_id: 因子ID
            backtest_date: 回测日期
            total_return: 总收益率
            annual_return: 年化收益率
            volatility: 波动率
            sharpe_ratio: 夏普比率
            max_drawdown: 最大回撤
            trade_count: 交易次数
            win_rate: 胜率
            
        Returns:
            int: 回测记录ID
        """
        query = """
        INSERT INTO backtest_results 
        (factor_id, backtest_date, total_return, annual_return, volatility,
         sharpe_ratio, max_drawdown, trade_count, win_rate)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            factor_id, backtest_date, total_return, annual_return, volatility,
            sharpe_ratio, max_drawdown, trade_count, win_rate
        )
        
        try:
            backtest_id = self.db.execute_insert(query, params)
            logger.info(f"回测结果保存成功: 因子ID {factor_id}, 记录ID {backtest_id}")
            return backtest_id
        except Exception as e:
            logger.error(f"回测结果保存失败: {e}")
            raise


# 全局因子注册器实例
factor_registry = None

def get_factor_registry() -> FactorRegistry:
    """获取全局因子注册器实例"""
    global factor_registry
    if factor_registry is None:
        factor_registry = FactorRegistry()
    return factor_registry


if __name__ == "__main__":
    # 测试因子注册器
    registry = get_factor_registry()
    
    # 测试注册新因子
    try:
        factor_id = registry.register_factor(
            name="ma_cross",
            expression="MA(CLOSE(), 5) - MA(CLOSE(), 20)",
            category="technical",
            description="5日均线与20日均线交叉因子"
        )
        print(f"注册因子成功，ID: {factor_id}")
    except Exception as e:
        print(f"注册因子失败: {e}")
    
    # 测试获取因子列表
    factors = registry.get_all_factors()
    print(f"当前因子数量: {len(factors)}")
    for factor in factors:
        print(f"因子: {factor['name']} - {factor['expression']}")
