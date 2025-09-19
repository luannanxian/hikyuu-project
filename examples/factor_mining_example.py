#!/usr/bin/env python3
"""
因子工厂实战示例 - 完整的因子挖掘流程
演示如何使用因子工厂系统进行量化因子研究
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


def step1_create_factor_candidates():
    """步骤1: 创建因子候选池"""
    print("\n" + "="*60)
    print("步骤1: 创建因子候选池")
    print("="*60)
    
    factor_candidates = {
        # 动量类因子
        "momentum": [
            ("mom_5d", "(CLOSE() - REF(CLOSE(), 5)) / REF(CLOSE(), 5)", "5日动量"),
            ("mom_20d", "(CLOSE() - REF(CLOSE(), 20)) / REF(CLOSE(), 20)", "20日动量"),
            ("mom_60d", "(CLOSE() - REF(CLOSE(), 60)) / REF(CLOSE(), 60)", "60日动量"),
        ],
        
        # 均线类因子
        "moving_average": [
            ("ma_cross_5_20", "MA(CLOSE(), 5) - MA(CLOSE(), 20)", "5-20日均线差"),
            ("ma_cross_10_30", "MA(CLOSE(), 10) - MA(CLOSE(), 30)", "10-30日均线差"),
            ("price_to_ma20", "CLOSE() / MA(CLOSE(), 20) - 1", "价格与20日均线偏离度"),
        ],
        
        # RSI类因子
        "rsi": [
            ("rsi_14", "RSI(CLOSE(), 14)", "14日RSI"),
            ("rsi_oversold", "IF(RSI(CLOSE(), 14) < 30, 1, 0)", "RSI超卖信号"),
            ("rsi_overbought", "IF(RSI(CLOSE(), 14) > 70, -1, 0)", "RSI超买信号"),
        ],
        
        # 成交量因子
        "volume": [
            ("vol_ratio", "VOL() / MA(VOL(), 20)", "成交量比率"),
            ("vol_trend", "MA(VOL(), 5) / MA(VOL(), 20)", "成交量趋势"),
            ("price_vol", "(CLOSE() - REF(CLOSE(), 1)) * VOL()", "价量配合"),
        ],
        
        # 波动率因子
        "volatility": [
            ("volatility_20d", "STD(LOG(CLOSE()/REF(CLOSE(), 1)), 20)", "20日波动率"),
            ("atr_ratio", "ATR(HIGH(), LOW(), CLOSE(), 14) / CLOSE()", "ATR相对值"),
            ("price_range", "(HIGH() - LOW()) / CLOSE()", "振幅"),
        ]
    }
    
    print(f"已创建 {sum(len(v) for v in factor_candidates.values())} 个候选因子")
    for category, factors in factor_candidates.items():
        print(f"  {category}: {len(factors)} 个因子")
    
    return factor_candidates


def step2_register_factors(factor_candidates):
    """步骤2: 注册因子到数据库"""
    print("\n" + "="*60)
    print("步骤2: 注册因子到数据库")
    print("="*60)
    
    registry = get_factor_registry()
    registered_factors = []
    
    for category, factors in factor_candidates.items():
        print(f"\n注册 {category} 类因子:")
        for name, expression, description in factors:
            try:
                # 使用时间戳确保名称唯一性
                unique_name = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                factor_id = registry.register_factor(
                    name=unique_name,
                    expression=expression,
                    category=category,
                    description=description
                )
                registered_factors.append((factor_id, unique_name, expression, category))
                print(f"  ✅ {name}: {description} (ID: {factor_id})")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
    
    print(f"\n成功注册 {len(registered_factors)} 个因子")
    return registered_factors


def step3_quick_evaluation(registered_factors):
    """步骤3: 快速评估因子"""
    print("\n" + "="*60)
    print("步骤3: 快速评估因子")
    print("="*60)
    
    engine = get_multi_factor_engine()
    
    # 获取测试股票（使用少量股票快速测试）
    print("\n获取测试股票...")
    test_stocks = engine._get_a_stocks()[:20]  # 使用前20只A股
    print(f"使用 {len(test_stocks)} 只股票进行快速评估")
    
    evaluation_results = []
    print("\n评估因子IC值:")
    print("-"*60)
    print(f"{'因子名称':<30} {'IC均值':>10} {'IC标准差':>10} {'评级':>10}")
    print("-"*60)
    
    for factor_id, name, expression, category in registered_factors:
        try:
            result = engine.evaluate_single_factor(
                expression=expression,
                stock_list=test_stocks,
                query=Query(-30)  # 使用最近30天数据
            )
            
            ic_mean = result['ic_mean']
            ic_std = result['ic_std']
            
            # 评级
            if ic_mean > 0.05:
                rating = "★★★★★"
            elif ic_mean > 0.03:
                rating = "★★★★"
            elif ic_mean > 0.01:
                rating = "★★★"
            elif ic_mean > 0:
                rating = "★★"
            else:
                rating = "★"
            
            evaluation_results.append({
                'factor_id': factor_id,
                'name': name,
                'category': category,
                'ic_mean': ic_mean,
                'ic_std': ic_std,
                'rating': rating
            })
            
            print(f"{name[:30]:<30} {ic_mean:>10.4f} {ic_std:>10.4f} {rating:>10}")
            
        except Exception as e:
            print(f"{name[:30]:<30} {'Error':>10} {'Error':>10} {'失败':>10}")
            logger.error(f"评估失败 {name}: {e}")
    
    return evaluation_results


def step4_select_effective_factors(evaluation_results):
    """步骤4: 筛选有效因子"""
    print("\n" + "="*60)
    print("步骤4: 筛选有效因子")
    print("="*60)
    
    # 按IC值排序
    evaluation_results.sort(key=lambda x: x['ic_mean'], reverse=True)
    
    # 筛选IC > 0.01的因子
    effective_factors = [r for r in evaluation_results if r['ic_mean'] > 0.01]
    
    print(f"\n发现 {len(effective_factors)} 个有效因子 (IC > 0.01):")
    
    if effective_factors:
        print("\nTop 5 因子:")
        print("-"*60)
        for i, factor in enumerate(effective_factors[:5], 1):
            print(f"{i}. {factor['name']}")
            print(f"   类别: {factor['category']}")
            print(f"   IC值: {factor['ic_mean']:.4f}")
            print(f"   评级: {factor['rating']}")
    
    # 更新因子状态
    registry = get_factor_registry()
    for factor in effective_factors:
        if factor['ic_mean'] > 0.03:
            try:
                registry.update_factor(factor['factor_id'], status='active')
                print(f"\n✅ 激活因子: {factor['name']}")
            except Exception as e:
                logger.error(f"更新因子状态失败: {e}")
    
    return effective_factors


def step5_generate_report():
    """步骤5: 生成因子挖掘报告"""
    print("\n" + "="*60)
    print("步骤5: 生成因子挖掘报告")
    print("="*60)
    
    pipeline = get_evaluation_pipeline()
    registry = get_factor_registry()
    
    # 生成绩效报告
    report = pipeline.generate_performance_report()
    
    print("\n📊 因子库统计:")
    print(f"  总因子数: {report['factor_stats']['total']}")
    print(f"  活跃因子: {report['factor_stats']['active']}")
    print(f"  测试因子: {report['factor_stats']['testing']}")
    print(f"  停用因子: {report['factor_stats']['inactive']}")
    
    # 按类别统计
    print("\n📈 按类别统计:")
    categories = ['momentum', 'moving_average', 'rsi', 'volume', 'volatility']
    for category in categories:
        factors = registry.get_factors_by_category(category)
        active = sum(1 for f in factors if f['status'] == 'active')
        print(f"  {category}: 总计 {len(factors)} 个, 活跃 {active} 个")
    
    # 最近的高质量因子
    print("\n⭐ 最近注册的活跃因子:")
    active_factors = [f for f in registry.get_all_factors() if f['status'] == 'active']
    active_factors.sort(key=lambda x: x['created_date'], reverse=True)
    for factor in active_factors[:5]:
        print(f"  - {factor['name']}: {factor['description']}")
    
    return report


def step6_create_factor_portfolio():
    """步骤6: 创建因子组合建议"""
    print("\n" + "="*60)
    print("步骤6: 创建因子组合建议")
    print("="*60)
    
    registry = get_factor_registry()
    
    # 获取各类别最佳因子
    best_factors = {}
    categories = ['momentum', 'moving_average', 'rsi', 'volume', 'volatility']
    
    for category in categories:
        factors = registry.get_factors_by_category(category)
        active_factors = [f for f in factors if f['status'] == 'active']
        if active_factors:
            # 这里简化处理，实际应该根据IC值排序
            best_factors[category] = active_factors[0]
    
    print("\n推荐的因子组合:")
    print("-"*60)
    
    if best_factors:
        print("多因子模型配置:")
        for category, factor in best_factors.items():
            print(f"  {category}: {factor['name']}")
            print(f"    表达式: {factor['expression'][:50]}...")
        
        print("\n组合建议:")
        print("  1. 使用不同类别的因子可以提高模型稳定性")
        print("  2. 建议权重分配: 动量30%, 均线20%, RSI20%, 成交量20%, 波动率10%")
        print("  3. 定期（每月）重新评估因子有效性")
        print("  4. 根据市场环境动态调整因子权重")
    else:
        print("暂无活跃因子，建议扩大因子搜索范围")


def main():
    """主函数: 完整的因子挖掘流程"""
    print("\n" + "="*80)
    print("因子工厂实战示例 - 完整因子挖掘流程")
    print("="*80)
    print(f"开始时间: {datetime.now()}")
    
    # 初始化Hikyuu
    print("\n初始化系统...")
    try:
        load_hikyuu()
        print("✅ Hikyuu框架初始化成功")
    except Exception as e:
        print(f"❌ Hikyuu初始化失败: {e}")
        return
    
    try:
        # 执行因子挖掘流程
        factor_candidates = step1_create_factor_candidates()
        registered_factors = step2_register_factors(factor_candidates)
        
        if registered_factors:
            evaluation_results = step3_quick_evaluation(registered_factors)
            effective_factors = step4_select_effective_factors(evaluation_results)
            report = step5_generate_report()
            step6_create_factor_portfolio()
        else:
            print("\n没有成功注册的因子，请检查因子表达式")
    
    except Exception as e:
        logger.error(f"执行过程出错: {e}")
        print(f"\n❌ 执行失败: {e}")
    
    print("\n" + "="*80)
    print("因子挖掘流程完成!")
    print(f"结束时间: {datetime.now()}")
    print("="*80)
    
    print("\n下一步建议:")
    print("1. 使用更多股票和更长时间进行详细回测")
    print("2. 对有效因子进行参数优化")
    print("3. 构建多因子组合策略")
    print("4. 集成到实盘交易系统")


if __name__ == "__main__":
    main()
