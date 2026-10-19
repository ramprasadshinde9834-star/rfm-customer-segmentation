# Customer Segmentation using RFM Analysis

Segmenting online retail customers by **Recency, Frequency and Monetary value** to decide who to reward, win back, or stop spending on.

## Business problem

A retailer cannot treat all customers the same. Marketing budget is limited, so the business needs to know which customers drive revenue, which are drifting away, and which are worth a win-back effort.

## Dataset

- **Online Retail dataset** (UCI / Kaggle): transactions from a UK-based online retailer, Dec 2010 to Dec 2011.
- About 540,000 rows, 8 columns: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country.
- Prices are in GBP. No currency conversion was applied.
- Download instructions are in [`data/README.md`](data/README.md).

## Approach

1. **Clean:** removed rows with missing CustomerID, cancelled invoices (InvoiceNo starting with "C"), non-positive Quantity or UnitPrice, and duplicates.
2. **Feature creation:** `TotalPrice = Quantity x UnitPrice`.
3. **RFM metrics per customer:**
   - Recency: days since last purchase, measured from a snapshot date (last invoice date + 1 day)
   - Frequency: number of unique invoices
   - Monetary: total spend
4. **Scoring:** each metric scored 1-5 with quantiles (Recency reversed, so recent = 5).
5. **Segmentation:** rule-based on R and F scores.

| Segment | Rule |
|---|---|
| Champions | R >= 4 and F >= 4 |
| Loyal | R >= 3 and F >= 3 |
| Potential Loyalists | R >= 4 and F <= 2 |
| At Risk | R <= 2 and F >= 3 |
| Lost | R <= 2 and F <= 2 |
| Need Attention | everything else (R = 3, F <= 2) |

## Results

> Replace this section with your real numbers after running the project.

- Customers analysed: **X**
- Champions are **X%** of customers and generate **X%** of revenue.
- At Risk customers account for **X%** of revenue.

![Segment size](images/1_segment_size.png)
![Revenue share](images/2_revenue_share.png)
![RFM distributions](images/3_rfm_distributions.png)
![Segment heatmap](images/4_segment_heatmap.png)

## Business recommendations

| Segment | Action |
|---|---|
| Champions | Loyalty rewards, early access, referral program |
| Loyal | Upsell and cross-sell bundles |
| Potential Loyalists | Second-purchase offer, welcome series |
| Need Attention | Time-limited offers |
| At Risk | Personalised win-back campaign |
| Lost | Low-cost last-chance email, then stop |

Full detail: [`reports/business_recommendations.md`](reports/business_recommendations.md)

## Project structure

```
rfm-customer-segmentation/
├── data/                       # put the dataset here (not committed)
├── images/                     # charts
├── notebooks/
│   └── rfm_analysis.ipynb      # step-by-step analysis
├── reports/
│   ├── rfm_customers.csv
│   ├── segment_summary.csv
│   └── business_recommendations.md
├── src/
│   └── rfm_analysis.py         # full pipeline as a script
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## How to run

```bash
git clone https://github.com/YOUR-USERNAME/rfm-customer-segmentation.git
cd rfm-customer-segmentation
pip install -r requirements.txt

# put the dataset in data/, then either:
python src/rfm_analysis.py --data "data/Online Retail.xlsx"
# or open the notebook:
jupyter notebook notebooks/rfm_analysis.ipynb
```

## Limitations

- Cancelled orders were removed, not netted against purchases.
- About 25% of rows had no CustomerID and could not be segmented.
- Segment rules use quintile scores and are a starting point; thresholds can be tuned.
- Data covers only one year, so seasonality (e.g. Christmas) affects Recency and Frequency.

## Next steps

- K-Means clustering on scaled RFM values and comparison with rule-based segments
- Power BI dashboard
- Cohort and retention analysis
- Country-level segment comparison

## Tools

Python, pandas, NumPy, Matplotlib, Seaborn, Jupyter

## Author

**YOUR NAME** | [LinkedIn](https://linkedin.com/in/your-profile) | [GitHub](https://github.com/YOUR-USERNAME)
