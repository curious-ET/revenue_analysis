# 零售销售额环比增长/下降归因分析

## 1. 分析框架与思路

### 1.1 分析目标
分析最近三个月营业额环比增长/下降的原因，找出哪些维度/因素的贡献度和占比最高。

### 1.2 核心指标
- **营业额环比变动额**：当月销售额 - 上月销售额
- **营业额环比变动率**：(当月销售额 - 上月销售额) / 上月销售额 * 100%

### 1.3 数据理解
根据提供的数据，我们有以下字段可用于分析：
- **Store**：商店ID，可关联到store.csv获取更多店铺特征
- **DayOfWeek**：星期几（1-7）
- **Date**：销售日期
- **Sales**：营业额/销售额
- **Customers**：顾客数量
- **Open**：店铺是否开门营业（0=关闭，1=开放）
- **Promo**：店铺是否在当天进行促销活动（0=无，1=有）
- **StateHoliday**：是否为国家法定假日
- **SchoolHoliday**：是否为学校假期

从store.csv获取的额外店铺特征：
- **StoreType**：商店类型（a, b, c, d）
- **Assortment**：商品分类水平（a=基础, b=额外, c=扩展）
- **CompetitionDistance**：最近竞争对手的距离（米）
- **CompetitionOpenSince[Month/Year]**：竞争者开业的月份/年份
- **Promo2**：是否参与持续促销（0=不参与，1=参与）
- **Promo2Since[Week/Year]**：持续促销开始的周/年
- **PromoInterval**：描述持续促销开始的月份

### 1.4 分析维度与思路

#### 1.4.1 时间维度分析
- 按月汇总销售数据，计算环比变化
- 分析每月工作日与假日的分布差异
- 考虑季节性因素对销售的影响

#### 1.4.2 店铺维度分析
- 按不同店铺类型(StoreType)分组分析环比变化
- 按商品结构水平(Assortment)分组分析环比变化
- 分析竞争者距离(CompetitionDistance)与销售变化的关系

#### 1.4.3 促销维度分析
- 分析促销活动(Promo)对销售的影响
- 分析持续促销(Promo2)对销售的影响
- 比较有促销和无促销时段的销售表现

#### 1.4.4 客流维度分析
- 分析客流量(Customers)变化
- 计算客单价(Sales/Customers)的变动
- 将营业额变动拆分为客流变动和客单价变动的贡献

#### 1.4.5 假期维度分析
- 分析国家法定假日(StateHoliday)对销售的影响
- 分析学校假期(SchoolHoliday)对销售的影响

## 2. 分析代码实现

### 2.1 数据准备与预处理

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import calendar

# 1. 读取数据
train_data = pd.read_csv('train.csv')
store_data = pd.read_csv('store.csv')

# 2. 数据预处理
# 转换日期列为datetime类型
train_data['Date'] = pd.to_datetime(train_data['Date'])

# 提取年份和月份信息
train_data['Year'] = train_data['Date'].dt.year
train_data['Month'] = train_data['Date'].dt.month
train_data['MonthName'] = train_data['Date'].dt.strftime('%b')
train_data['YearMonth'] = train_data['Date'].dt.strftime('%Y-%m')

# 与店铺信息合并
data = pd.merge(train_data, store_data, on='Store', how='left')

# 3. 计算客单价
data['AvgTicket'] = data['Sales'] / data['Customers']

# 4. 筛选最近四个月数据（假设数据集包含连续的月份）
# 找出数据集中的最近四个月
recent_months = sorted(data['YearMonth'].unique())[-4:]
recent_data = data[data['YearMonth'].isin(recent_months)]

print(f"分析的月份: {recent_months}")
```

### 2.2 计算月度环比变化

```python
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

print("月度总体销售情况及环比变化:")
print(monthly_sales[['YearMonth', 'Sales', 'Sales_MoM_Change', 'Sales_MoM_Change_Pct', 
                     'Customers', 'AvgTicket']])
```

### 2.3 客流与客单价贡献度分析

```python
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
```

### 2.4 店铺类型维度分析

```python
# 按店铺类型和月份分组
store_type_monthly = recent_data.groupby(['StoreType', 'YearMonth']).agg({
    'Sales': 'sum',
    'Customers': 'sum'
}).reset_index()

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
        total_sales_change = monthly_sales[monthly_sales['YearMonth'] == current_month]['Sales_MoM_Change'].values[0]
        
        # 计算贡献度
        contribution_pct = (sales_change / total_sales_change) * 100 if total_sales_change != 0 else 0
        
        print(f"{current_month}相比{prev_month}, 店铺类型 {store_type} 的贡献度: {contribution_pct:.2f}%")
```

### 2.5 促销维度分析

```python
# 按促销状态和月份分组
promo_monthly = recent_data.groupby(['Promo', 'YearMonth']).agg({
    'Sales': 'sum',
    'Customers': 'sum',
    'Store': 'count'  # 统计天数
}).rename(columns={'Store': 'Days'}).reset_index()

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
        total_sales_change = monthly_sales[monthly_sales['YearMonth'] == current_month]['Sales_MoM_Change'].values[0]
        
        # 计算贡献度
        contribution_pct = (sales_change / total_sales_change) * 100 if total_sales_change != 0 else 0
        
        print(f"{current_month}相比{prev_month}, {promo_label}的贡献度: {contribution_pct:.2f}%")
```

### 2.6 假期维度分析

```python
# 按学校假期状态和月份分组
holiday_monthly = recent_data.groupby(['SchoolHoliday', 'YearMonth']).agg({
    'Sales': 'sum',
    'Customers': 'sum',
    'Store': 'count'  # 统计天数
}).rename(columns={'Store': 'Days'}).reset_index()

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
```

### 2.7 贡献度可视化

```python
# 创建贡献度汇总表
def create_contribution_summary():
    # 假设我们已经计算了各维度的贡献度
    # 这里只是一个示例框架，实际执行时需要替换为真实的计算结果
    
    # 客流与客单价贡献度
    customer_atk_contrib = []
    
    # 店铺类型贡献度
    store_type_contrib = []
    
    # 促销活动贡献度
    promo_contrib = []
    
    # 假期贡献度
    holiday_contrib = []
    
    # 整合所有贡献度数据并可视化
    # 使用横向堆积柱状图展示不同维度的贡献度
    
    # plt.figure(figsize=(12, 8))
    # 创建瀑布图或堆积柱状图来可视化贡献度
    
    return "贡献度可视化函数"
```

## 3. 分析结果说明

### 3.1 月度营业额总体变化

通过分析最近三个月的销售数据，我们观察到以下总体变化趋势：
（实际执行代码后填写具体数据结果）

### 3.2 客流量与客单价贡献分析

将营业额变化拆分为客流量变化和客单价变化两部分：
（实际执行代码后填写具体数据结果）

### 3.3 店铺类型贡献分析

不同类型店铺对营业额环比变化的贡献：
（实际执行代码后填写具体数据结果）

### 3.4 促销活动贡献分析

促销活动对营业额环比变化的影响：
（实际执行代码后填写具体数据结果）

### 3.5 假期因素贡献分析

学校假期对营业额环比变化的影响：
（实际执行代码后填写具体数据结果）

## 4. 结论与建议

### 4.1 主要发现

1. （根据分析结果填写主要发现）
2. （根据分析结果填写主要发现）
3. （根据分析结果填写主要发现）

### 4.2 营业额变化的主要贡献因素

1. 贡献度最高的因素：（根据分析结果填写）
2. 第二重要的因素：（根据分析结果填写）
3. 第三重要的因素：（根据分析结果填写）

### 4.3 业务建议

基于上述分析，提出以下业务建议：

1. （根据分析结果提出建议）
2. （根据分析结果提出建议）
3. （根据分析结果提出建议）

## 5. 参考提示词

在进行类似的营业额环比分析时，可以使用以下提示词与AI助手交流：

```
请分析我的零售销售数据中最近三个月的营业额环比变化，并回答：
1. 环比变化的主要原因是什么？
2. 哪些因素（如客流量、客单价、促销、店铺类型、假期等）对环比变化的贡献最大？
3. 请提供各因素的贡献度占比，并用图表可视化展示。
4. 基于分析结果，提出3-5条提升营业额的业务建议。

请使用销售额分解法和贡献度分析法，步骤包括：
- 计算环比增长/下降绝对值和百分比
- 将销售额变化分解为客流和客单价变化
- 分析不同维度（如促销、店铺类型、假期等）的贡献度
- 找出贡献度最高的几个因素
```

## 6. 附录：概念解释

### 6.1 环比增长/下降

环比增长是指当前时期的数据与上一时期数据相比的变化率。对于月度数据，环比增长率表示当月与上月相比的变化百分比。

计算公式：环比增长率 = (当期数值 - 上期数值) / 上期数值 × 100%

### 6.2 贡献度分析

贡献度分析是量化各个因素对总体变化影响程度的方法。它通过计算每个因素的变化量占总体变化量的比例，来确定各因素的相对重要性。

计算公式：贡献度 = 某因素的变化量 / 总体变化量 × 100%

### 6.3 销售额分解

销售额 = 客流量 × 客单价

因此销售额的变化可以分解为：
- 客流量变化的贡献：(当期客流 - 上期客流) × 上期客单价
- 客单价变化的贡献：(当期客单价 - 上期客单价) × 当期客流
- 交叉项贡献：(当期客流 - 上期客流) × (当期客单价 - 上期客单价) 