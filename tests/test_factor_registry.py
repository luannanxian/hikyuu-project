#!/usr/bin/env python3
"""
因子注册器单元测试
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFactorRegistry(unittest.TestCase):
    """因子注册器测试类"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock()

    @patch('factor_factory.factor_registry.get_db_manager')
    def test_register_factor_success(self, mock_get_db):
        """测试成功注册因子"""
        from factor_factory.factor_registry import FactorRegistry

        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_insert.return_value = 123

        registry = FactorRegistry()

        factor_id = registry.register_factor(
            name="test_ma_factor",
            expression="MA(CLOSE(), 5) - MA(CLOSE(), 20)",
            category="technical",
            description="测试均线因子"
        )

        self.assertEqual(factor_id, 123)
        self.mock_db.execute_insert.assert_called_once()

    @patch('factor_factory.factor_registry.get_db_manager')
    def test_get_factor_by_id(self, mock_get_db):
        """测试根据ID获取因子"""
        from factor_factory.factor_registry import FactorRegistry

        mock_get_db.return_value = self.mock_db

        # 模拟数据库返回结果
        mock_result = (
            1, "test_factor", "MA(CLOSE(), 5)", "technical",
            datetime.now(), "active", "测试因子"
        )
        self.mock_db.execute_query.return_value = [mock_result]

        registry = FactorRegistry()
        factor = registry.get_factor(1)

        self.assertIsNotNone(factor)
        self.assertEqual(factor['id'], 1)
        self.assertEqual(factor['name'], "test_factor")

    @patch('factor_factory.factor_registry.get_db_manager')
    def test_get_factor_not_found(self, mock_get_db):
        """测试获取不存在的因子"""
        from factor_factory.factor_registry import FactorRegistry

        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_query.return_value = []

        registry = FactorRegistry()
        factor = registry.get_factor(999)

        self.assertIsNone(factor)

    @patch('factor_factory.factor_registry.get_db_manager')
    def test_search_factors(self, mock_get_db):
        """测试搜索因子"""
        from factor_factory.factor_registry import FactorRegistry

        mock_get_db.return_value = self.mock_db

        # 模拟搜索结果
        mock_results = [
            (1, "ma_factor_1", "MA(CLOSE(), 5)", "technical",
             datetime.now(), "active", "均线因子1"),
            (2, "ma_factor_2", "MA(CLOSE(), 10)", "technical",
             datetime.now(), "active", "均线因子2")
        ]
        self.mock_db.execute_query.return_value = mock_results

        registry = FactorRegistry()
        factors = registry.search_factors("ma")

        self.assertEqual(len(factors), 2)
        self.assertIn("MA", factors[0]['expression'])

    @patch('factor_factory.factor_registry.get_db_manager')
    def test_update_factor_status(self, mock_get_db):
        """测试更新因子状态"""
        from factor_factory.factor_registry import FactorRegistry

        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_update.return_value = 1  # 影响1行

        registry = FactorRegistry()
        result = registry.update_factor(1, status='active')

        self.assertTrue(result)
        self.mock_db.execute_update.assert_called_once()

    @patch('factor_factory.factor_registry.get_db_manager')
    def test_delete_factor(self, mock_get_db):
        """测试删除因子"""
        from factor_factory.factor_registry import FactorRegistry

        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_update.return_value = 1  # 影响1行

        registry = FactorRegistry()
        result = registry.delete_factor(1)

        self.assertTrue(result)

    @patch('factor_factory.factor_registry.get_db_manager')
    def test_save_performance_result(self, mock_get_db):
        """测试保存绩效结果"""
        from factor_factory.factor_registry import FactorRegistry

        mock_get_db.return_value = self.mock_db
        self.mock_db.execute_insert.return_value = 456

        registry = FactorRegistry()

        performance_id = registry.save_performance_result(
            factor_id=1,
            evaluation_date=datetime.now(),
            ic_value=0.05,
            icir_value=0.8,
            annual_return=0.12,
            sharpe_ratio=1.5
        )

        self.assertEqual(performance_id, 456)

    @patch('factor_factory.factor_registry.get_db_manager')
    def test_format_factor_result(self, mock_get_db):
        """测试格式化因子结果"""
        from factor_factory.factor_registry import FactorRegistry

        mock_get_db.return_value = self.mock_db
        registry = FactorRegistry()

        # 模拟数据库查询结果
        raw_result = (
            1, "test_factor", "MA(CLOSE(), 5)", "technical",
            datetime(2024, 1, 1), "active", "测试因子"
        )

        formatted = registry._format_factor_result(raw_result)

        expected_keys = ['id', 'name', 'expression', 'category',
                        'created_date', 'status', 'description']

        for key in expected_keys:
            self.assertIn(key, formatted)

        self.assertEqual(formatted['id'], 1)
        self.assertEqual(formatted['name'], "test_factor")


if __name__ == '__main__':
    # 设置日志级别避免测试时的日志干扰
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)

    unittest.main(verbosity=2)