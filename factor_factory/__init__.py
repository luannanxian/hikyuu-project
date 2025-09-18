"""
因子工厂系统 - 基于hikyuu的量化因子挖掘和管理系统

该模块提供了完整的因子生命周期管理功能，包括：
1. 因子注册和管理
2. 批量因子评估
3. 绩效跟踪和统计
4. 自动化回测流水线
"""

from .mysql_manager import get_db_manager, MySQLManager
from .factor_registry import get_factor_registry, FactorRegistry
from .multi_factor_engine import get_multi_factor_engine, MultiFactorEngine
from .evaluation_pipeline import get_evaluation_pipeline, EvaluationPipeline

__version__ = "1.0.0"
__author__ = "Hikyuu Factor Factory Team"
__all__ = [
    'get_db_manager',
    'MySQLManager',
    'get_factor_registry', 
    'FactorRegistry',
    'get_multi_factor_engine',
    'MultiFactorEngine',
    'get_evaluation_pipeline',
    'EvaluationPipeline'
]
