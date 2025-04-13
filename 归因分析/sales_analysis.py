import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import calendar
import os

# 确保输出文件夹存在
if not os.path.exists('output'):
    os.makedirs('output')

# 1. 读取数据
print("正在读取数据...")
train_data = pd.read_csv('train.csv')
store_data = pd.read_csv('store.csv')

# 2. 数据预处理
print("正在处理数据...")
# 转换日期列为datetime类型
train_data['Date'] = pd.to_datetime(train_data['Date'])

# 提取年份和月份信息
train_data['Year'] = train_data['Date'].dt.year
train_data['Month'] = train_data['Date'].dt.month
train_data['MonthName'] = train_data['Date'].dt.strftime('%b')
train_data['YearMonth'] = train_data['Date'].dt.strftime('%Y-%m')

# 与店铺信息合并
data = pd.merge(train_data, store_data, on='Store', how='left')

# 计算客单价
data['AvgTicket'] = data['Sales'] / data['Customers']

# 3. 筛选最近四个月数据
recent_months = sorted(data['YearMonth'].unique())[-4:]
recent_data = data[data['YearMonth'].isin(recent_months)]

print(f"分析的月份: {recent_months}")

# 4. 计算月度环比变化
# 按月汇总销售数据
monthly_sales = recent_data.groupby('YearMonth').agg({
    'Sales': 'sum',
    'Customers': 'sum',
    'Open': 'sum'  # 开门天数总和
}).reset_index()

# 计算月度环比变化
monthly_sales['Sales_MoM_Change'] = monthly_sales['Sales'].diff()
monthly_sales['Sales_MoM_Change_Pct'] = monthly_sales['Sales'].pct_change() * 100
monthly_sales['Customers_MoM_Change'] = monthly_sales['Customers'].diff()
monthly_sales['Customers_MoM_Change_Pct'] = monthly_sales['Customers'].pct_change() * 100

# 计算平均客单价
monthly_sales['AvgTicket'] = monthly_sales['Sales'] / monthly_sales['Customers']
monthly_sales['AvgTicket_MoM_Change'] = monthly_sales['AvgTicket'].diff()
monthly_sales['AvgTicket_MoM_Change_Pct'] = monthly_sales['AvgTicket'].pct_change() * 100

print("\n月度总体销售情况及环比变化:")
print(monthly_sales[['YearMonth', 'Sales', 'Sales_MoM_Change', 'Sales_MoM_Change_Pct', 
                   'Customers', 'AvgTicket']])

# 5. 保存月度总体数据到CSV
monthly_sales.to_csv('output/monthly_sales.csv', index=False)

# 6. 客流与客单价贡献度分析
print("\n正在分析客流量与客单价贡献度...")
contribution_results = []

# 最近三个月的环比分析
for i in range(1, len(monthly_sales)):
    current_month = monthly_sales.iloc[i]['YearMonth']
    prev_month = monthly_sales.iloc[i-1]['YearMonth']
    
    # 本月与上月的销售额和客流量
    current_sales = monthly_sales.iloc[i]['Sales']
    prev_sales = monthly_sales.iloc[i-1]['Sales']
    current_customers = monthly_sales.iloc[i]['Customers']
    prev_customers = monthly_sales.iloc[i-1]['Customers']
    
    # 本月与上月的客单价
    current_avg_ticket = monthly_sales.iloc[i]['AvgTicket']
    prev_avg_ticket = monthly_sales.iloc[i-1]['AvgTicket']
    
    # 销售额变化
    sales_change = current_sales - prev_sales
    
    # 客流量变化的贡献
    customer_contribution = (current_customers - prev_customers) * prev_avg_ticket
    
    # 客单价变化的贡献
    avg_ticket_contribution = (current_avg_ticket - prev_avg_ticket) * current_customers
    
    # 交叉项贡献（客流变化 * 客单价变化）
    cross_contribution = (current_customers - prev_customers) * (current_avg_ticket - prev_avg_ticket)
    
    # 计算贡献度占比
    customer_contrib_pct = (customer_contribution / sales_change) * 100 if sales_change != 0 else 0
    avg_ticket_contrib_pct = (avg_ticket_contribution / sales_change) * 100 if sales_change != 0 else 0
    cross_contrib_pct = (cross_contribution / sales_change) * 100 if sales_change != 0 else 0
    
    print(f"\n{current_month}相比{prev_month}的环比分析:")
    print(f"销售额变化: {sales_change:.2f} ({(sales_change/prev_sales)*100:.2f}%)")
    print(f"客流量贡献: {customer_contribution:.2f} (占比: {customer_contrib_pct:.2f}%)")
    print(f"客单价贡献: {avg_ticket_contribution:.2f} (占比: {avg_ticket_contrib_pct:.2f}%)")
    print(f"交叉项贡献: {cross_contribution:.2f} (占比: {cross_contrib_pct:.2f}%)")
    
    # 保存结果
    contribution_results.append({
        'Current_Month': current_month,
        'Prev_Month': prev_month,
        'Sales_Change': sales_change,
        'Sales_Change_Pct': (sales_change/prev_sales)*100,
        'Customer_Contribution': customer_contribution,
        'Customer_Contrib_Pct': customer_contrib_pct,
        'AvgTicket_Contribution': avg_ticket_contribution,
        'AvgTicket_Contrib_Pct': avg_ticket_contrib_pct,
        'Cross_Contribution': cross_contribution,
        'Cross_Contrib_Pct': cross_contrib_pct
    })

# 保存贡献度结果到CSV
pd.DataFrame(contribution_results).to_csv('output/contribution_analysis.csv', index=False)

# 7. 店铺类型维度分析
print("\n正在分析店铺类型维度...")
# 按店铺类型和月份分组
store_type_monthly = recent_data.groupby(['StoreType', 'YearMonth']).agg({
    'Sales': 'sum',
    'Customers': 'sum'
}).reset_index()

store_type_results = []

# 计算每种店铺类型的月度环比变化
for store_type in store_type_monthly['StoreType'].unique():
    st_data = store_type_monthly[store_type_monthly['StoreType'] == store_type].sort_values('YearMonth')
    
    st_data['Sales_MoM_Change'] = st_data['Sales'].diff()
    st_data['Sales_MoM_Change_Pct'] = st_data['Sales'].pct_change() * 100
    
    print(f"\n店铺类型 {store_type} 的月度销售额及环比变化:")
    print(st_data[['YearMonth', 'Sales', 'Sales_MoM_Change', 'Sales_MoM_Change_Pct']])
    
    # 计算每种店铺类型对总体销售额环比变化的贡献度
    for i in range(1, len(st_data)):
        current_month = st_data.iloc[i]['YearMonth']
        prev_month = st_data.iloc[i-1]['YearMonth']
        
        # 该店铺类型的销售额变化
        sales_change = st_data.iloc[i]['Sales'] - st_data.iloc[i-1]['Sales']
        
        # 总体销售额变化（从monthly_sales中获取）
        total_month_data = monthly_sales[monthly_sales['YearMonth'] == current_month]
        if len(total_month_data) > 0:
            total_sales_change = total_month_data['Sales_MoM_Change'].values[0]
            
            # 计算贡献度
            contribution_pct = (sales_change / total_sales_change) * 100 if total_sales_change != 0 else 0
            
            print(f"{current_month}相比{prev_month}, 店铺类型 {store_type} 的贡献度: {contribution_pct:.2f}%")
            
            # 保存结果
            store_type_results.append({
                'StoreType': store_type,
                'Current_Month': current_month,
                'Prev_Month': prev_month,
                'Sales_Change': sales_change,
                'Total_Sales_Change': total_sales_change,
                'Contribution_Pct': contribution_pct
            })

# 保存店铺类型贡献度结果到CSV
pd.DataFrame(store_type_results).to_csv('output/store_type_contribution.csv', index=False)

# 8. 促销维度分析
print("\n正在分析促销维度...")
# 按促销状态和月份分组
promo_monthly = recent_data.groupby(['Promo', 'YearMonth']).agg({
    'Sales': 'sum',
    'Customers': 'sum',
    'Store': 'count'  # 统计天数
}).rename(columns={'Store': 'Days'}).reset_index()

promo_results = []

# 计算有促销和无促销的月度环比变化
for promo in [0, 1]:
    promo_data = promo_monthly[promo_monthly['Promo'] == promo].sort_values('YearMonth')
    
    # 计算环比变化
    promo_data['Sales_MoM_Change'] = promo_data['Sales'].diff()
    promo_data['Sales_MoM_Change_Pct'] = promo_data['Sales'].pct_change() * 100
    
    promo_label = "有促销" if promo == 1 else "无促销"
    print(f"\n{promo_label}时段的月度销售额及环比变化:")
    print(promo_data[['YearMonth', 'Sales', 'Days', 'Sales_MoM_Change', 'Sales_MoM_Change_Pct']])
    
    # 计算促销状态对总体销售额环比变化的贡献度
    for i in range(1, len(promo_data)):
        current_month = promo_data.iloc[i]['YearMonth']
        prev_month = promo_data.iloc[i-1]['YearMonth']
        
        # 该促销状态的销售额变化
        sales_change = promo_data.iloc[i]['Sales'] - promo_data.iloc[i-1]['Sales']
        
        # 总体销售额变化
        total_month_data = monthly_sales[monthly_sales['YearMonth'] == current_month]
        if len(total_month_data) > 0:
            total_sales_change = total_month_data['Sales_MoM_Change'].values[0]
            
            # 计算贡献度
            contribution_pct = (sales_change / total_sales_change) * 100 if total_sales_change != 0 else 0
            
            print(f"{current_month}相比{prev_month}, {promo_label}的贡献度: {contribution_pct:.2f}%")
            
            # 保存结果
            promo_results.append({
                'Promo': promo,
                'Promo_Label': promo_label,
                'Current_Month': current_month,
                'Prev_Month': prev_month,
                'Sales_Change': sales_change,
                'Total_Sales_Change': total_sales_change,
                'Contribution_Pct': contribution_pct
            })

# 保存促销贡献度结果到CSV
pd.DataFrame(promo_results).to_csv('output/promo_contribution.csv', index=False)

# 9. 假期维度分析
print("\n正在分析假期维度...")
# 按学校假期状态和月份分组
holiday_monthly = recent_data.groupby(['SchoolHoliday', 'YearMonth']).agg({
    'Sales': 'sum',
    'Customers': 'sum',
    'Store': 'count'  # 统计天数
}).rename(columns={'Store': 'Days'}).reset_index()

holiday_results = []

# 计算假期和非假期的月度环比变化
for holiday in [0, 1]:
    holiday_data = holiday_monthly[holiday_monthly['SchoolHoliday'] == holiday].sort_values('YearMonth')
    
    # 计算环比变化
    holiday_data['Sales_MoM_Change'] = holiday_data['Sales'].diff()
    holiday_data['Sales_MoM_Change_Pct'] = holiday_data['Sales'].pct_change() * 100
    
    holiday_label = "学校假期" if holiday == 1 else "非学校假期"
    print(f"\n{holiday_label}的月度销售额及环比变化:")
    print(holiday_data[['YearMonth', 'Sales', 'Days', 'Sales_MoM_Change', 'Sales_MoM_Change_Pct']])
    
    # 计算假期状态对总体销售额环比变化的贡献度
    for i in range(1, len(holiday_data)):
        current_month = holiday_data.iloc[i]['YearMonth']
        prev_month = holiday_data.iloc[i-1]['YearMonth']
        
        # 该假期状态的销售额变化
        sales_change = holiday_data.iloc[i]['Sales'] - holiday_data.iloc[i-1]['Sales']
        
        # 总体销售额变化
        total_month_data = monthly_sales[monthly_sales['YearMonth'] == current_month]
        if len(total_month_data) > 0:
            total_sales_change = total_month_data['Sales_MoM_Change'].values[0]
            
            # 计算贡献度
            contribution_pct = (sales_change / total_sales_change) * 100 if total_sales_change != 0 else 0
            
            print(f"{current_month}相比{prev_month}, {holiday_label}的贡献度: {contribution_pct:.2f}%")
            
            # 保存结果
            holiday_results.append({
                'SchoolHoliday': holiday,
                'Holiday_Label': holiday_label,
                'Current_Month': current_month,
                'Prev_Month': prev_month,
                'Sales_Change': sales_change,
                'Total_Sales_Change': total_sales_change,
                'Contribution_Pct': contribution_pct
            })

# 保存假期贡献度结果到CSV
pd.DataFrame(holiday_results).to_csv('output/holiday_contribution.csv', index=False)

print("\n分析完成，结果已保存到output文件夹。") 