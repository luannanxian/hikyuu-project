#!/usr/bin/env python3
"""
MySQL管理器单元测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from factor_factory.mysql_manager import MySQLManager, get_db_manager


class TestMySQLManager(unittest.TestCase):
    """MySQL管理器测试类"""

    def setUp(self):
        """测试前准备"""
        self.manager = None

    def tearDown(self):
        """测试后清理"""
        if self.manager:
            del self.manager

    @patch('factor_factory.mysql_manager.mysql.connector')
    def test_database_config_loading(self, mock_connector):
        """测试数据库配置加载"""
        from factor_factory.config.database_config import DATABASE_CONFIG

        # 验证配置项存在
        required_keys = ['host', 'database', 'user', 'password', 'port']
        for key in required_keys:
            self.assertIn(key, DATABASE_CONFIG)

        # 验证端口为整数
        self.assertIsInstance(DATABASE_CONFIG['port'], int)
        self.assertIsInstance(DATABASE_CONFIG['pool_size'], int)

    @patch('factor_factory.mysql_manager.mysql.connector.connect')
    def test_ensure_database_success(self, mock_connect):
        """测试确保数据库存在 - 成功情况"""
        # 模拟数据库连接
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('factor_factory',)

        # 创建管理器实例但不初始化连接池
        with patch.object(MySQLManager, 'initialize_pool'), \
             patch.object(MySQLManager, 'initialize_tables'):
            manager = MySQLManager()
            result = manager.ensure_database()

        self.assertTrue(result)
        mock_cursor.execute.assert_called()

    @patch('factor_factory.mysql_manager.mysql.connector.connect')
    def test_ensure_database_create_new(self, mock_connect):
        """测试创建新数据库"""
        # 模拟数据库不存在
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # 数据库不存在

        with patch.object(MySQLManager, 'initialize_pool'), \
             patch.object(MySQLManager, 'initialize_tables'):
            manager = MySQLManager()
            result = manager.ensure_database()

        self.assertTrue(result)
        # 验证创建数据库的SQL被执行
        create_calls = [call for call in mock_cursor.execute.call_args_list
                       if 'CREATE DATABASE' in str(call)]
        self.assertTrue(len(create_calls) > 0)

    def test_expression_validation_safe(self):
        """测试安全表达式验证"""
        from factor_factory.multi_factor_engine import MultiFactorEngine

        with patch.object(MultiFactorEngine, '__init__', lambda x: None):
            engine = MultiFactorEngine()

            # 安全表达式应该通过
            safe_expressions = [
                "MA(CLOSE(), 5)",
                "RSI(CLOSE(), 14)",
                "CLOSE() - REF(CLOSE(), 1)",
                "VOL() / MA(VOL(), 20)"
            ]

            for expr in safe_expressions:
                try:
                    engine._validate_expression(expr)
                except Exception as e:
                    self.fail(f"安全表达式 '{expr}' 验证失败: {e}")

    def test_expression_validation_unsafe(self):
        """测试不安全表达式验证"""
        from factor_factory.multi_factor_engine import MultiFactorEngine

        with patch.object(MultiFactorEngine, '__init__', lambda x: None):
            engine = MultiFactorEngine()

            # 不安全表达式应该被拒绝
            unsafe_expressions = [
                "import os",
                "exec('print(1)')",
                "__import__('os')",
                "open('/etc/passwd')",
                "eval('1+1')"
            ]

            for expr in unsafe_expressions:
                with self.assertRaises(ValueError):
                    engine._validate_expression(expr)

    def test_expression_validation_edge_cases(self):
        """测试表达式验证边界情况"""
        from factor_factory.multi_factor_engine import MultiFactorEngine

        with patch.object(MultiFactorEngine, '__init__', lambda x: None):
            engine = MultiFactorEngine()

            # 空表达式
            with self.assertRaises(ValueError):
                engine._validate_expression("")

            # None值
            with self.assertRaises(ValueError):
                engine._validate_expression(None)

            # 过长表达式
            long_expr = "MA(CLOSE(), 5)" * 200
            with self.assertRaises(ValueError):
                engine._validate_expression(long_expr)

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = get_db_manager()
        manager2 = get_db_manager()

        # 应该返回同一个实例
        self.assertIs(manager1, manager2)


class TestFactorRegistry(unittest.TestCase):
    """因子注册器测试类"""

    @patch('factor_factory.factor_registry.get_db_manager')
    def test_factor_validation(self, mock_get_db):
        """测试因子验证"""
        from factor_factory.factor_registry import FactorRegistry

        # 模拟数据库管理器
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.execute_insert.return_value = 1

        registry = FactorRegistry()

        # 测试有效因子注册
        factor_id = registry.register_factor(
            name="test_factor",
            expression="MA(CLOSE(), 5)",
            category="test",
            description="测试因子"
        )

        self.assertEqual(factor_id, 1)
        mock_db.execute_insert.assert_called_once()


if __name__ == '__main__':
    # 设置日志级别避免测试时的日志干扰
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)

    unittest.main(verbosity=2)