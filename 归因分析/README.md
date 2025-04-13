# 零售销售额环比变化归因分析框架

## 项目概述

本项目提供了一个完整的零售销售额环比变化归因分析框架，通过多维度分析找出影响销售额环比增长/下降的关键因素及其贡献度。框架结合了销售额分解法和贡献度分析方法，可以系统地分析并量化不同因素对营业额变化的影响。

## 分析维度

分析框架涵盖以下维度：

1. **客流量与客单价**：将销售额变化分解为客流量变化、客单价变化及交叉项的贡献
2. **店铺类型**：分析不同类型店铺(a, b, c, d)对销售额环比变化的贡献
3. **促销活动**：分析有促销与无促销时段对销售额环比变化的贡献
4. **假期因素**：分析学校假期与非假期时段对销售额环比变化的贡献

## 项目结构

```
├── README.md                     # 项目说明文档
├── revenue_analysis_mom.md       # 分析框架和方法论说明
├── sales_analysis.py             # 数据处理和分析脚本
├── visualize_results.py          # 数据可视化脚本
├── analysis_conclusion.md        # 结论文档模板
├── run_analysis.py               # 分析流程主脚本
├── output/                       # 分析结果输出目录
│   ├── monthly_sales.csv         # 月度销售数据
│   ├── contribution_analysis.csv # 客流量与客单价贡献分析
│   ├── store_type_contribution.csv # 店铺类型贡献分析
│   ├── promo_contribution.csv    # 促销活动贡献分析
│   ├── holiday_contribution.csv  # 假期因素贡献分析
│   ├── final_conclusion.md       # 最终分析结论
│   └── figures/                  # 数据可视化图表
│       ├── monthly_sales_trend.png  # 月度销售额趋势图
│       ├── sales_change_waterfall.png # 销售额变化贡献因素瀑布图
│       ├── store_type_contribution.png # 店铺类型贡献图
│       ├── promo_contribution.png # 促销贡献图 
│       ├── holiday_contribution.png # 假期贡献图
│       └── overall_contribution_comparison.png # 各维度贡献比较图
```

## 使用方法

### 环境准备

1. 确保已安装Python 3.6+
2. 安装所需依赖包：

```bash
pip install pandas numpy matplotlib seaborn tabulate
```

### 数据要求

本分析框架需要以下数据文件：

1. `train.csv`：销售数据，包含字段：Store, DayOfWeek, Date, Sales, Customers, Open, Promo, StateHoliday, SchoolHoliday
2. `store.csv`：店铺信息，包含字段：Store, StoreType, Assortment, CompetitionDistance等

### 运行分析

执行以下命令运行完整分析流程：

```bash
python run_analysis.py
```

这将依次执行数据分析、可视化图表生成和结论文档生成。

或者，您可以单独运行各个脚本：

```bash
# 只运行数据分析
python sales_analysis.py

# 只生成可视化图表
python visualize_results.py
```

### 查看结果

分析完成后，您可以查看以下文件：

1. `output/final_conclusion.md`：包含完整分析结论的Markdown文档
2. `output/figures/`：包含所有可视化图表的目录

## 分析框架说明

### 指标定义

1. **营业额环比变动额** = 当月销售额 - 上月销售额
2. **营业额环比变动率** = (当月销售额 - 上月销售额) / 上月销售额 * 100%
3. **贡献度** = 某因素的变化量 / 总体变化量 * 100%

### 销售额分解

销售额 = 客流量 × 客单价，因此销售额的变化可以分解为：

- **客流量变化的贡献** = (当期客流 - 上期客流) × 上期客单价
- **客单价变化的贡献** = (当期客单价 - 上期客单价) × 当期客流
- **交叉项贡献** = (当期客流 - 上期客流) × (当期客单价 - 上期客单价)

### 贡献度计算

对于每个维度（店铺类型、促销、假期等），计算：

1. **变化量** = 当期该维度值 - 上期该维度值
2. **贡献度** = 变化量 / 总体变化量 * 100%

## 结果解读

分析结果将帮助您理解：

1. 环比变化的主要原因是什么？是客流变化还是客单价变化？
2. 哪些店铺类型贡献最大？
3. 促销活动的效果如何？
4. 假期因素的影响大小？
5. 综合来看，哪些因素的贡献度最高？

## 定制化分析

您可以通过修改以下文件进行定制化分析：

1. `sales_analysis.py`：调整分析维度或添加新的维度
2. `visualize_results.py`：调整可视化图表的样式和内容
3. `analysis_conclusion.md`：修改结论文档的结构和内容

## 贡献

欢迎对本项目提出改进建议或贡献代码。

## 许可证

[MIT License](LICENSE) 