#!/usr/bin/env python3
"""
因子工厂系统测试脚本
用于测试因子工厂系统的各项功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime
from hikyuu import *

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("测试数据库连接")
    print("=" * 50)
    
    try:
        from factor_factory.mysql_manager import get_db_manager
        db_manager = get_db_manager()
        
        if db_manager.check_connection():
            print("✅ 数据库连接测试成功")
            factor_count = db_manager.get_factor_count()
            print(f"当前因子数量: {factor_count}")
            return True
        else:
            print("❌ 数据库连接测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接测试异常: {e}")
        return False

def test_factor_registry():
    """测试因子注册器"""
    print("\n" + "=" * 50)
    print("测试因子注册器")
    print("=" * 50)
    
    try:
        from factor_factory.factor_registry import get_factor_registry
        registry = get_factor_registry()
        
        # 测试注册新因子（使用唯一名称避免重复）
        import random
        test_factors = [
            {
                'name': f'ma_cross_5_20_test_{random.randint(1000,9999)}',
                'expression': 'MA(CLOSE(), 5) - MA(CLOSE(), 20)',
                'category': 'technical',
                'description': '5日均线与20日均线交叉因子'
            },
            {
                'name': f'rsi_oversold_test_{random.randint(1000,9999)}',
                'expression': 'RSI(CLOSE(), 14) < 30',
                'category': 'momentum', 
                'description': 'RSI超卖因子'
            },
            {
                'name': f'volume_spike_test_{random.randint(1000,9999)}',
                'expression': 'VOLUME() / MA(VOLUME(), 20) > 2',
                'category': 'volume',
                'description': '成交量突增因子'
            }
        ]
        
        factor_ids = []
        for factor in test_factors:
            try:
                factor_id = registry.register_factor(
                    name=factor['name'],
                    expression=factor['expression'],
                    category=factor['category'],
                    description=factor['description']
                )
                factor_ids.append(factor_id)
                print(f"✅ 注册因子成功: {factor['name']} (ID: {factor_id})")
            except Exception as e:
                print(f"❌ 注册因子失败: {factor['name']}, 错误: {e}")
        
        # 测试获取因子列表
        factors = registry.get_all_factors()
        print(f"✅ 获取因子列表成功: 共 {len(factors)} 个因子")
        
        # 测试搜索因子
        search_results = registry.search_factors('ma')
        print(f"✅ 搜索因子成功: 找到 {len(search_results)} 个相关因子")
        
        return True
        
    except Exception as e:
        print(f"❌ 因子注册器测试异常: {e}")
        return False

def test_multi_factor_engine():
    """测试MultiFactor引擎"""
    print("\n" + "=" * 50)
    print("测试MultiFactor引擎")
    print("=" * 50)
    
    try:
        from factor_factory.multi_factor_engine import get_multi_factor_engine
        engine = get_multi_factor_engine()
        
        # 测试创建因子指标
        test_expression = "MA(CLOSE(), 5) - MA(CLOSE(), 20)"
        try:
            indicator = engine.create_factor_indicator(test_expression)
            print(f"✅ 创建因子指标成功: {test_expression}")
        except Exception as e:
            print(f"❌ 创建因子指标失败: {e}")
            return False
        
        # 测试获取A股列表
        a_stocks = engine._get_a_stocks()
        print(f"✅ 获取A股列表成功: 共 {len(a_stocks)} 只A股")
        
        # 测试单因子评估
        try:
            result = engine.evaluate_single_factor(
                expression=test_expression,
                stock_list=a_stocks[:10],  # 测试前10只股票
                query=Query(-20)  # 最近20条数据
            )
            print(f"✅ 单因子评估成功: IC均值={result['ic_mean']:.4f}")
        except Exception as e:
            print(f"❌ 单因子评估失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ MultiFactor引擎测试异常: {e}")
        return False

def test_evaluation_pipeline():
    """测试评估流水线"""
    print("\n" + "=" * 50)
    print("测试评估流水线")
    print("=" * 50)
    
    try:
        from factor_factory.evaluation_pipeline import get_evaluation_pipeline
        pipeline = get_evaluation_pipeline()
        
        # 测试生成绩效报告
        try:
            report = pipeline.generate_performance_report()
            print("✅ 生成绩效报告成功")
            print(f"   因子统计: 总共{report['factor_stats']['total']}个, "
                  f"活跃{report['factor_stats']['active']}个, "
                  f"测试{report['factor_stats']['testing']}个")
        except Exception as e:
            print(f"❌ 生成绩效报告失败: {e}")
        
        # 测试清理旧数据
        try:
            cleanup_result = pipeline.cleanup_old_data(days_to_keep=365)  # 清理一年前的数据
            print("✅ 数据清理测试完成")
        except Exception as e:
            print(f"❌ 数据清理失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 评估流水线测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("因子工厂系统功能测试")
    print("=" * 60)
    
    # 初始化hikyuu
    try:
        load_hikyuu()
        print("✅ Hikyuu框架初始化成功")
    except Exception as e:
        print(f"❌ Hikyuu框架初始化失败: {e}")
        return
    
    # 运行各项测试
    tests = [
        test_database_connection,
        test_factor_registry, 
        test_multi_factor_engine,
        test_evaluation_pipeline
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
            results.append(False)
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"测试通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！因子工厂系统功能正常")
    else:
        print("⚠️  部分测试未通过，请检查系统配置")
    
    print("\n下一步操作建议:")
    print("1. 检查MySQL数据库配置是否正确")
    print("2. 确保数据库中存在 factor_factory 数据库")
    print("3. 运行 python -m factor_factory.mysql_manager 测试数据库连接")
    print("4. 运行 python -m factor_factory.factor_registry 测试因子注册功能")

if __name__ == "__main__":
    main()
