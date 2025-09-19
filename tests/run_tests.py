#!/usr/bin/env python3
"""
测试套件运行器
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests():
    """运行所有单元测试"""
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    test_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(test_dir, pattern='test_*.py')

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试结果总结
    print("\n" + "="*60)
    print("测试结果总结")
    
    print("="*60)
    print(f"总共运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            # 安全地提取错误信息
            lines = traceback.split('\n')
            error_line = "未知错误"
            for line in reversed(lines):
                if line.strip() and not line.startswith(' '):
                    error_line = line.strip()
                    break
            print(f"  - {test}: {error_line}")

    # 返回是否成功
    return result.wasSuccessful()


def run_specific_test(test_module):
    """运行特定测试模块"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_module)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='运行因子工厂单元测试')
    parser.add_argument('--module', '-m', help='运行特定测试模块 (例如: test_mysql_manager)')
    parser.add_argument('--quiet', '-q', action='store_true', help='安静模式，减少输出')

    args = parser.parse_args()

    if args.quiet:
        import logging
        logging.getLogger().setLevel(logging.CRITICAL)

    print("因子工厂单元测试套件")
    print("="*40)

    if args.module:
        print(f"运行测试模块: {args.module}")
        success = run_specific_test(args.module)
    else:
        print("运行所有测试...")
        success = run_all_tests()

    # 退出代码
    sys.exit(0 if success else 1)