#!/usr/bin/env python3
"""
简化版因子挖掘示例 - 快速上手指南
演示因子工厂系统的基本使用方法
"""

import sys
import os
# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hikyuu import *
from factor_factory.factor_registry import get_factor_registry
from factor_factory.multi_factor_engine import get_multi_factor_engine
from factor_factory.evaluation_pipeline import get_evaluation_pipeline
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def quick_start_example():
    """快速开始示例：注册并评估一个简单因子"""
    print("\n" + "="*60)
    print("快速开始示例")
    print("="*60)
    
    # 初始化
    registry = get_factor_registry()
    engine = get_multi_factor_engine()
    
    # 1. 注册一个简单的均线交叉因子
    print("\n1. 注册因子...")
    factor_name = f"ma_cross_{datetime.now().strftime('%H%M%S')}"
    factor_id = registry.register_factor(
        name=factor_name,
        expression="MA(CLOSE(), 5) - MA(CLOSE(), 20)",
        category="trend",
        description="5日均线与20日均线的差值"
    )
    print(f"✅ 成功注册因子: {factor_name} (ID: {factor_id})")
    
    # 2. 评估因子
    print("\n2. 评估因子...")
    test_stocks = engine._get_a_stocks()[:50]  # 使用50只股票确保有足够数据
    
    # 使用更长的时间周期确保有足够数据计算IC
    result = engine.evaluate_single_factor(
        expression="MA(CLOSE(), 5) - MA(CLOSE(), 20)",
        stock_list=test_stocks,
        query=Query(-100)  # 使用最近100天数据
    )
    
    print(f"📊 评估结果:")
    print(f"  IC均值: {result['ic_mean']:.4f}")
    print(f"  IC标准差: {result['ic_std']:.4f}")
    print(f"  ICIR: {result['icir_mean']:.4f}")
    
    # 3. 判断因子质量
    if result['ic_mean'] > 0.03:
        print("  ✅ 因子质量: 优秀 (IC > 0.03)")
    elif result['ic_mean'] > 0.01:
        print("  📊 因子质量: 良好 (0.01 < IC < 0.03)")
    elif result['ic_mean'] > 0:
        print("  ⚠️ 因子质量: 一般 (0 < IC < 0.01)")
    else:
        print("  ❌ 因子质量: 较差 (IC <= 0)")
    
    return factor_id, result


def batch_factor_mining():
    """批量因子挖掘示例"""
    print("\n" + "="*60)
    print("批量因子挖掘")
    print("="*60)
    
    registry = get_factor_registry()
    engine = get_multi_factor_engine()
    
    # 定义要测试的因子
    test_factors = [
        ("动量因子", "(CLOSE() - REF(CLOSE(), 20)) / REF(CLOSE(), 20)", "momentum"),
        ("RSI因子", "RSI(CLOSE(), 14)", "momentum"),
        ("成交量比", "VOL() / MA(VOL(), 20)", "volume"),
        ("价格位置", "(CLOSE() - LLV(LOW(), 20)) / (HHV(HIGH(), 20) - LLV(LOW(), 20))", "technical"),
        ("均线偏离", "CLOSE() / MA(CLOSE(), 20) - 1", "trend"),
    ]
    
    # 注册并评估因子
    results = []
    test_stocks = engine._get_a_stocks()[:50]  # 使用50只股票确保数据充足
    
    print(f"\n使用 {len(test_stocks)} 只股票进行评估")
    print("-"*60)
    print(f"{'因子名称':<20} {'IC均值':>10} {'评级':>10}")
    print("-"*60)
    
    for name, expression, category in test_factors:
        try:
            # 注册因子
            unique_name = f"{name}_{datetime.now().strftime('%H%M%S')}"
            factor_id = registry.register_factor(
                name=unique_name,
                expression=expression,
                category=category,
                description=name
            )
            
            # 评估因子
            result = engine.evaluate_single_factor(
                expression=expression,
                stock_list=test_stocks,
                query=Query(-100)  # 使用100天数据
            )
            
            ic_mean = result['ic_mean']
            
            # 评级
            if ic_mean > 0.03:
                rating = "★★★★★"
            elif ic_mean > 0.01:
                rating = "★★★"
            elif ic_mean > 0:
                rating = "★"
            else:
                rating = "-"
            
            results.append((name, ic_mean, rating))
            print(f"{name:<20} {ic_mean:>10.4f} {rating:>10}")
            
        except Exception as e:
            print(f"{name:<20} {'Error':>10} {'失败':>10}")
            logger.error(f"因子评估失败 {name}: {e}")
    
    # 输出最佳因子
    if results:
        results.sort(key=lambda x: x[1], reverse=True)
        print(f"\n🏆 最佳因子: {results[0][0]} (IC={results[0][1]:.4f})")
    
    return results


def view_factor_status():
    """查看因子库状态"""
    print("\n" + "="*60)
    print("因子库状态")
    print("="*60)
    
    registry = get_factor_registry()
    pipeline = get_evaluation_pipeline()
    
    # 生成报告
    report = pipeline.generate_performance_report()
    
    print(f"\n📊 因子统计:")
    print(f"  总计: {report['factor_stats']['total']} 个")
    print(f"  活跃: {report['factor_stats']['active']} 个")
    print(f"  测试: {report['factor_stats']['testing']} 个")
    print(f"  停用: {report['factor_stats']['inactive']} 个")
    
    # 显示最近的因子
    all_factors = registry.get_all_factors()
    if all_factors:
        print(f"\n📝 最近注册的5个因子:")
        recent_factors = sorted(all_factors, key=lambda x: x['created_date'], reverse=True)[:5]
        for factor in recent_factors:
            print(f"  - {factor['name']}: {factor['description']}")


def create_custom_factor():
    """创建自定义因子示例"""
    print("\n" + "="*60)
    print("创建自定义因子")
    print("="*60)
    
    engine = get_multi_factor_engine()
    
    # 示例：创建一个复合因子
    print("\n创建复合因子示例:")
    
    # 价量配合因子
    custom_expression = """
    IF(MA(CLOSE(), 5) > MA(CLOSE(), 20),
       VOL() / MA(VOL(), 20),
       0)
    """
    
    print(f"表达式: {custom_expression}")
    
    try:
        # 验证表达式
        indicator = engine.create_factor_indicator(custom_expression.strip())
        print("✅ 因子表达式验证成功")
        
        # 快速测试
        test_stocks = engine._get_a_stocks()[:5]
        result = engine.evaluate_single_factor(
            expression=custom_expression.strip(),
            stock_list=test_stocks,
            query=Query(-20)
        )
        
        print(f"📊 快速测试结果: IC={result['ic_mean']:.4f}")
        
    except Exception as e:
        print(f"❌ 因子创建失败: {e}")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("因子工厂系统 - 简化版使用示例")
    print("="*80)
    
    # 初始化Hikyuu
    print("\n初始化系统...")
    try:
        load_hikyuu()
        print("✅ Hikyuu框架初始化成功")
    except Exception as e:
        print(f"❌ Hikyuu初始化失败: {e}")
        return
    
    # 功能菜单
    print("\n请选择要运行的功能:")
    print("1. 快速开始示例（推荐）")
    print("2. 批量因子挖掘")
    print("3. 查看因子库状态")
    print("4. 创建自定义因子")
    print("0. 运行所有示例")
    
    try:
        choice = input("\n请输入选项 (0-4): ").strip()
        
        if choice == '1':
            quick_start_example()
        elif choice == '2':
            batch_factor_mining()
        elif choice == '3':
            view_factor_status()
        elif choice == '4':
            create_custom_factor()
        elif choice == '0':
            quick_start_example()
            batch_factor_mining()
            view_factor_status()
            create_custom_factor()
        else:
            print("无效选项，运行默认示例...")
            quick_start_example()
            
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
    except Exception as e:
        logger.error(f"运行出错: {e}")
        print(f"\n❌ 运行失败: {e}")
    
    print("\n" + "="*80)
    print("因子挖掘完成！")
    print("="*80)
    
    print("\n📚 使用说明:")
    print("1. 快速开始: 运行选项1，了解基本流程")
    print("2. 批量挖掘: 运行选项2，测试多个因子")
    print("3. 查看状态: 运行选项3，查看因子库情况")
    print("4. 自定义因子: 运行选项4，创建自己的因子")
    
    print("\n💡 下一步建议:")
    print("1. 尝试修改因子表达式，创建更多因子")
    print("2. 使用更多股票和更长时间周期进行评估")
    print("3. 将IC值较高的因子组合成多因子模型")
    print("4. 定期运行评估，监控因子表现变化")


if __name__ == "__main__":
    main()
