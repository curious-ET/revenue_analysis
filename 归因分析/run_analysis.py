import os
import subprocess
import pandas as pd
import numpy as np
import time
import string

def run_command(command):
    """运行指定的命令并输出结果"""
    print(f"\n执行命令: {command}")
    process = subprocess.Popen(
        command, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 实时输出命令执行过程
    for line in process.stdout:
        print(line.strip())
    
    # 等待命令执行完成
    process.wait()
    if process.returncode != 0:
        print(f"命令执行失败，错误码: {process.returncode}")
        for line in process.stderr:
            print(line.strip())
    else:
        print("命令执行成功")
    
    return process.returncode

def format_table(df):
    """格式化DataFrame为Markdown表格"""
    return df.to_markdown(index=False)

def update_conclusion_document():
    """根据分析结果更新结论文档"""
    print("\n正在更新结论文档...")
    
    try:
        # 读取分析结果
        monthly_sales = pd.read_csv('output/monthly_sales.csv')
        contribution_analysis = pd.read_csv('output/contribution_analysis.csv')
        store_type_contribution = pd.read_csv('output/store_type_contribution.csv')
        promo_contribution = pd.read_csv('output/promo_contribution.csv')
        holiday_contribution = pd.read_csv('output/holiday_contribution.csv')
        
        # 读取结论模板
        with open('analysis_conclusion.md', 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 1. 月份列表
        month_list = ', '.join(monthly_sales['YearMonth'].tolist())
        
        # 2. 月度销售表格
        monthly_sales_display = monthly_sales[['YearMonth', 'Sales', 'Sales_MoM_Change', 'Sales_MoM_Change_Pct', 
                                              'Customers', 'AvgTicket']]
        monthly_sales_display.columns = ['月份', '销售额', '环比变动额', '环比变动率(%)', '客流量', '客单价']
        monthly_sales_table = format_table(monthly_sales_display)
        
        # 3. 客流量与客单价分析
        customer_price_analysis = ""
        for i, row in contribution_analysis.iterrows():
            current_month = row['Current_Month']
            prev_month = row['Prev_Month']
            sales_change = row['Sales_Change']
            sales_change_pct = row['Sales_Change_Pct']
            customer_contrib = row['Customer_Contrib_Pct']
            ticket_contrib = row['AvgTicket_Contrib_Pct']
            
            analysis_text = f"- **{current_month}相比{prev_month}**：销售额{('增长' if sales_change > 0 else '下降')}了{abs(sales_change):.2f}（{sales_change_pct:.2f}%）。"
            
            if abs(customer_contrib) > abs(ticket_contrib):
                analysis_text += f" 主要由**客流量**变化驱动（贡献率{customer_contrib:.2f}%），客单价贡献为{ticket_contrib:.2f}%。"
            else:
                analysis_text += f" 主要由**客单价**变化驱动（贡献率{ticket_contrib:.2f}%），客流量贡献为{customer_contrib:.2f}%。"
                
            customer_price_analysis += analysis_text + "\n\n"
        
        # 4. 最新月的贡献度
        latest_contrib = contribution_analysis.iloc[-1]
        customer_contribution = f"{latest_contrib['Customer_Contrib_Pct']:.2f}%"
        ticket_contribution = f"{latest_contrib['AvgTicket_Contrib_Pct']:.2f}%"
        cross_contribution = f"{latest_contrib['Cross_Contrib_Pct']:.2f}%"
        
        # 5. 店铺类型贡献
        store_pivot = store_type_contribution.pivot_table(
            values='Contribution_Pct', 
            index=['Current_Month'], 
            columns=['StoreType'],
            aggfunc='sum'
        ).reset_index()
        store_pivot.columns.name = None
        storetype_table = format_table(store_pivot)
        
        # 6. 店铺类型主要发现
        # 找出贡献最大的店铺类型
        latest_month = monthly_sales['YearMonth'].iloc[-1]
        latest_store_contrib = store_type_contribution[
            store_type_contribution['Current_Month'] == latest_month
        ].sort_values('Contribution_Pct', ascending=False)
        
        top_store_type = latest_store_contrib.iloc[0]['StoreType'] if len(latest_store_contrib) > 0 else "无数据"
        top_store_contrib = latest_store_contrib.iloc[0]['Contribution_Pct'] if len(latest_store_contrib) > 0 else 0
        
        store_findings = f"分析显示，店铺类型 **{top_store_type}** 对最近一个月环比变化的贡献最大，贡献率为 {top_store_contrib:.2f}%。"
        
        if len(latest_store_contrib) > 1:
            second_store_type = latest_store_contrib.iloc[1]['StoreType']
            second_store_contrib = latest_store_contrib.iloc[1]['Contribution_Pct']
            store_findings += f" 其次是店铺类型 **{second_store_type}**，贡献率为 {second_store_contrib:.2f}%。"
            
        # 分析贡献正负
        positive_stores = latest_store_contrib[latest_store_contrib['Contribution_Pct'] > 0]
        negative_stores = latest_store_contrib[latest_store_contrib['Contribution_Pct'] < 0]
        
        if not positive_stores.empty:
            store_findings += f"\n\n正向贡献的店铺类型有: " + ", ".join([f"**{t}** ({c:.2f}%)" for t, c in 
                             zip(positive_stores['StoreType'], positive_stores['Contribution_Pct'])])
            
        if not negative_stores.empty:
            store_findings += f"\n\n负向贡献的店铺类型有: " + ", ".join([f"**{t}** ({c:.2f}%)" for t, c in 
                             zip(negative_stores['StoreType'], negative_stores['Contribution_Pct'])])
        
        # 7. 促销贡献分析
        promo_pivot = promo_contribution.pivot_table(
            values='Contribution_Pct', 
            index=['Current_Month'], 
            columns=['Promo_Label'],
            aggfunc='sum'
        ).reset_index()
        promo_pivot.columns.name = None
        promo_table = format_table(promo_pivot)
        
        # 8. 促销主要发现
        latest_promo_contrib = promo_contribution[
            promo_contribution['Current_Month'] == latest_month
        ].sort_values('Contribution_Pct', ascending=False)
        
        top_promo = latest_promo_contrib.iloc[0]['Promo_Label'] if len(latest_promo_contrib) > 0 else "无数据"
        top_promo_contrib = latest_promo_contrib.iloc[0]['Contribution_Pct'] if len(latest_promo_contrib) > 0 else 0
        
        promo_findings = f"分析显示，**{top_promo}**时段对最近一个月环比变化的贡献最大，贡献率为 {top_promo_contrib:.2f}%。"
        
        if len(latest_promo_contrib) > 1:
            second_promo = latest_promo_contrib.iloc[1]['Promo_Label']
            second_promo_contrib = latest_promo_contrib.iloc[1]['Contribution_Pct']
            promo_findings += f" 其次是**{second_promo}**时段，贡献率为 {second_promo_contrib:.2f}%。"
        
        # 9. 假期贡献分析
        holiday_pivot = holiday_contribution.pivot_table(
            values='Contribution_Pct', 
            index=['Current_Month'], 
            columns=['Holiday_Label'],
            aggfunc='sum'
        ).reset_index()
        holiday_pivot.columns.name = None
        holiday_table = format_table(holiday_pivot)
        
        # 10. 假期主要发现
        latest_holiday_contrib = holiday_contribution[
            holiday_contribution['Current_Month'] == latest_month
        ].sort_values('Contribution_Pct', ascending=False)
        
        top_holiday = latest_holiday_contrib.iloc[0]['Holiday_Label'] if len(latest_holiday_contrib) > 0 else "无数据"
        top_holiday_contrib = latest_holiday_contrib.iloc[0]['Contribution_Pct'] if len(latest_holiday_contrib) > 0 else 0
        
        holiday_findings = f"分析显示，**{top_holiday}**时段对最近一个月环比变化的贡献最大，贡献率为 {top_holiday_contrib:.2f}%。"
        
        if len(latest_holiday_contrib) > 1:
            second_holiday = latest_holiday_contrib.iloc[1]['Holiday_Label']
            second_holiday_contrib = latest_holiday_contrib.iloc[1]['Contribution_Pct']
            holiday_findings += f" 其次是**{second_holiday}**时段，贡献率为 {second_holiday_contrib:.2f}%。"
        
        # 11. 主要贡献因素排名
        # 合并所有维度的贡献度
        all_dimensions = []
        
        # 客流与客单价
        all_dimensions.append(('客流量', latest_contrib['Customer_Contrib_Pct']))
        all_dimensions.append(('客单价', latest_contrib['AvgTicket_Contrib_Pct']))
        
        # 店铺类型
        for _, row in latest_store_contrib.iterrows():
            all_dimensions.append((f"店铺类型-{row['StoreType']}", row['Contribution_Pct']))
        
        # 促销状态
        for _, row in latest_promo_contrib.iterrows():
            all_dimensions.append((row['Promo_Label'], row['Contribution_Pct']))
        
        # 假期状态
        for _, row in latest_holiday_contrib.iterrows():
            all_dimensions.append((row['Holiday_Label'], row['Contribution_Pct']))
        
        # 按贡献度绝对值排序
        all_dimensions.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # 前三大贡献因素
        top_factor = all_dimensions[0][0] if len(all_dimensions) > 0 else "无数据"
        top_contribution = all_dimensions[0][1] if len(all_dimensions) > 0 else 0
        
        second_factor = all_dimensions[1][0] if len(all_dimensions) > 1 else "无数据"
        second_contribution = all_dimensions[1][1] if len(all_dimensions) > 1 else 0
        
        third_factor = all_dimensions[2][0] if len(all_dimensions) > 2 else "无数据"
        third_contribution = all_dimensions[2][1] if len(all_dimensions) > 2 else 0
        
        # 12. 业务建议
        # 根据分析结果，生成业务建议
        recommendations = []
        
        # 客流量建议
        if latest_contrib['Customer_Contrib_Pct'] < 0:
            recommendations.append("加强客流引导措施，如开展会员营销活动、增加引流促销，提高客流量")
        else:
            recommendations.append("巩固现有客流引导策略，同时关注客单价提升，增加商品交叉销售")
        
        # 客单价建议
        if latest_contrib['AvgTicket_Contrib_Pct'] < 0:
            recommendations.append("优化商品结构，增加高客单价商品的推广力度，提升客单价")
        else:
            recommendations.append("维持当前客单价优势，可考虑推出套餐或捆绑销售策略，进一步提升客单价")
        
        # 店铺类型建议
        if top_store_type != "无数据":
            recommendations.append(f"重点关注店铺类型 {top_store_type} 的运营策略，分析其成功经验并推广到其他类型店铺")
        
        # 促销建议
        if "促销" in top_factor or "有促销" in top_factor:
            recommendations.append("当前促销策略效果良好，建议优化促销商品结构和促销力度，进一步提升促销效率")
        else:
            recommendations.append("检视现有促销策略有效性，考虑调整促销频次、力度或商品范围，提高促销对销售的拉动作用")
        
        # 假期建议
        if "假期" in top_factor:
            recommendations.append("针对学校假期时段，制定专门的营销策略，如学生特惠、亲子活动等，进一步利用假期效应")
        
        # 确保有至少4条建议
        while len(recommendations) < 4:
            recommendations.append("定期分析销售数据，及时调整经营策略，持续优化销售表现")
        
        # 如果超过4条，只保留前4条
        recommendations = recommendations[:4]
        
        # 13. 替换模板中的占位符
        template = template.replace("{MONTH_LIST}", month_list)
        template = template.replace("{MONTHLY_SALES_TABLE}", monthly_sales_table)
        template = template.replace("{CUSTOMER_PRICE_ANALYSIS}", customer_price_analysis)
        template = template.replace("{CUSTOMER_CONTRIBUTION}", customer_contribution)
        template = template.replace("{TICKET_CONTRIBUTION}", ticket_contribution)
        template = template.replace("{CROSS_CONTRIBUTION}", cross_contribution)
        template = template.replace("{STORETYPE_CONTRIBUTION_TABLE}", storetype_table)
        template = template.replace("{STORE_TYPE_FINDINGS}", store_findings)
        template = template.replace("{PROMO_CONTRIBUTION_TABLE}", promo_table)
        template = template.replace("{PROMO_FINDINGS}", promo_findings)
        template = template.replace("{HOLIDAY_CONTRIBUTION_TABLE}", holiday_table)
        template = template.replace("{HOLIDAY_FINDINGS}", holiday_findings)
        template = template.replace("{LATEST_MONTH}", latest_month)
        template = template.replace("{PREV_MONTH}", monthly_sales['YearMonth'].iloc[-2])
        template = template.replace("{TOP_FACTOR}", top_factor)
        template = template.replace("{TOP_CONTRIBUTION}", f"{top_contribution:.2f}")
        template = template.replace("{SECOND_FACTOR}", second_factor)
        template = template.replace("{SECOND_CONTRIBUTION}", f"{second_contribution:.2f}")
        template = template.replace("{THIRD_FACTOR}", third_factor)
        template = template.replace("{THIRD_CONTRIBUTION}", f"{third_contribution:.2f}")
        template = template.replace("{RECOMMENDATION_1}", recommendations[0])
        template = template.replace("{RECOMMENDATION_2}", recommendations[1])
        template = template.replace("{RECOMMENDATION_3}", recommendations[2])
        template = template.replace("{RECOMMENDATION_4}", recommendations[3])
        
        # 14. 写入更新后的结论文件
        with open('output/final_conclusion.md', 'w', encoding='utf-8') as f:
            f.write(template)
            
        print("结论文档已更新并保存至 output/final_conclusion.md")
        return True
        
    except Exception as e:
        print(f"更新结论文档失败: {str(e)}")
        return False

def main():
    """主函数，运行整个分析流程"""
    start_time = time.time()
    
    print("=== 零售销售额环比增长/下降归因分析 ===")
    print("分析流程开始...")
    
    # 创建输出目录
    if not os.path.exists('output'):
        os.makedirs('output')
    
    # 步骤1: 运行销售数据分析
    print("\n步骤1: 运行销售数据分析...")
    sales_analysis_result = run_command("python sales_analysis.py")
    if sales_analysis_result != 0:
        print("销售数据分析失败，流程终止")
        return
    
    # 步骤2: 生成可视化图表
    print("\n步骤2: 生成可视化图表...")
    visualize_result = run_command("python visualize_results.py")
    if visualize_result != 0:
        print("可视化图表生成失败，继续执行后续步骤")
    
    # 步骤3: 更新结论文档
    print("\n步骤3: 生成最终结论文档...")
    conclusion_result = update_conclusion_document()
    if not conclusion_result:
        print("结论文档生成失败，请检查分析结果")
    
    # 完成
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\n分析流程完成! 总执行时间: {execution_time:.2f} 秒")
    print("分析结果和图表保存在output目录中")
    print("最终结论文档: output/final_conclusion.md")

if __name__ == "__main__":
    main() 