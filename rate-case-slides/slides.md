---
theme: default
title: Rate Case Baseline Analysis
class: text-center
highlighter: shiki
colorSchema: dark
transition: fade-out
mdc: true
---

# Rate Case Baseline Analysis

California Investor-Owned Utilities 2018 to 2023

<div class="mt-8 text-lg opacity-70">
Adrian Nie
</div>

<div class="mt-4 text-sm opacity-50">
A practice analysis using publicly available federal regulatory data
</div>

---
class: px-20 py-10
---

# What is a General Rate Case

<div class="mt-8" />

A General Rate Case (GRC) is a formal regulatory proceeding where a utility requests approval to change the rates it charges customers.

<div class="mt-8 grid grid-cols-3 gap-6 text-sm">

<div class="bg-white/5 rounded-lg p-4">
<div class="font-bold mb-2">Utility Files</div>
Proposes revenue requirement and cost justifications
</div>

<div class="bg-white/5 rounded-lg p-4">
<div class="font-bold mb-2">Staff Analyzes</div>
Reviews costs for reasonableness and prudence
</div>

<div class="bg-white/5 rounded-lg p-4">
<div class="font-bold mb-2">Commission Decides</div>
Approves, modifies, or denies the request
</div>

</div>

<div class="mt-8 text-sm opacity-60">
The outcome directly determines what customers pay on their monthly bills.
</div>

---
class: px-20 py-10
---

# GRC Analysis Requirements

<div class="mt-6 text-sm opacity-70">
What CPUC staff evaluates in a rate case proceeding
</div>

<div class="mt-6 grid grid-cols-2 gap-8">

<div>

<div class="font-bold mb-3">Revenue Requirement</div>

- O&M Expenses
- Depreciation
- Rate Base
- Return on Investment
- Taxes

</div>

<div>

<div class="font-bold mb-3">Reasonableness Tests</div>

- Historical trend analysis
- Peer benchmarking
- Cost driver analysis
- Outlier detection

</div>

<div>

<div class="font-bold mb-3">Customer Impact</div>

- Cost allocation by class
- Rate design
- Bill impact analysis
- Affordability review

</div>

<div>

<div class="font-bold mb-3">Policy Compliance</div>

- Safety requirements
- Reliability standards
- Clean energy mandates
- Wildfire mitigation

</div>

</div>

---
class: px-20 py-10
---

# Public Data vs Full Access

<div class="mt-4 grid grid-cols-2 gap-12">

<div class="border border-white/10 rounded-lg p-6 bg-white/5">

<div class="font-bold text-lg mb-4">What Public Data Enabled</div>

<div class="text-sm mb-4 opacity-70">Using FERC Form 1 and EIA-861</div>
```python
# Cost driver regression
model = OLS(om_total ~ customers 
            + sales + rate_base)

# Result: R² = 0.93
# Rate base is primary driver
```

<div class="mt-4 text-sm">
This identifies that rate base expansion explains most cost growth. I can flag that 27% remains unexplained — but cannot determine what specifically drives it.
</div>

<div class="mt-4 text-sm">

**Analyses Possible**
- Trend analysis and CAGR
- Peer benchmarking
- Cost driver regression
- Bill impact estimation

</div>

</div>

<div class="border border-white/10 rounded-lg p-6 bg-white/5">

<div class="font-bold text-lg mb-4">What Full Access Would Enable</div>

<div class="text-sm mb-4 opacity-70">Data I did not have access to</div>

<div class="text-sm space-y-3">

<div>
<div class="font-medium">Line-item workpapers</div>
<div class="opacity-60">Identify specific programs causing cost growth</div>
</div>

<div>
<div class="font-medium">Utility testimony</div>
<div class="opacity-60">Understand proposed justifications</div>
</div>

<div>
<div class="font-medium">CPUC decision history</div>
<div class="opacity-60">Compare to previously authorized amounts</div>
</div>

<div>
<div class="font-medium">Contract details</div>
<div class="opacity-60">Verify if costs are competitively sourced</div>
</div>

<div>
<div class="font-medium">Asset-level depreciation</div>
<div class="opacity-60">Replace assumed 3.5% with actual schedules</div>
</div>

</div>

</div>

</div>

---
class: px-20 py-10
---

# Context: Real PG&E GRC Filing (2027-2030)

<div class="mt-4 text-sm opacity-70">
PG&E 2027 General Rate Case Application (filed May 15, 2025)
<br/>
<a href="https://www.pge.com/en/regulation/general-rate-case.html" class="underline">pge.com/en/regulation/general-rate-case.html</a>
</div>

<div class="mt-6 grid grid-cols-2 gap-12">

<div>

**What PG&E Requested**

- Test year revenue requirement: $16.6B
- Increase from 2026: 8%
- Attrition years (2028-2030): 6.1% annually
- Bill impact: $215 → $226/month (+5.2%)

**Filing Contents**

- 351 pages of application
- 11 exhibits of testimony
- Tens of thousands of workpaper pages
- Line-item cost justifications by program

</div>

<div>

**What My Analysis Replicated**

- Revenue requirement calculation structure
- O&M trend analysis (found 6.2% CAGR)
- Bill impact estimation (~5% increase)
- Peer comparison across CA IOUs

**What I Could Not Replicate**

- Test year forecasting (no escalation factors)
- Program-level cost review (no workpapers)
- Contract verification (confidential)
- Asset-specific depreciation (assumed 3.5%)

</div>

</div>

<div class="mt-8 text-sm opacity-60">
Note: My analysis covers electric operations only. PG&E's GRC includes both electric and gas.
</div>

<div class="mt-2 text-sm opacity-60">
Source: A.25-05-XXX, PG&E 2027 GRC Application
</div>

---
class: px-16 py-8
---

# Connecting to a Real GRC Filing

<div class="text-sm opacity-70">
PG&E 2027 General Rate Case Application (A.25-05-XXX, filed May 15, 2025)
</div>

<div class="mt-4 grid grid-cols-2 gap-8">

<div>

<img src="/pge_grc_table5.png" class="h-64 border border-white/20 rounded" />

<div class="mt-2 text-xs opacity-50">
Source: PG&E 2027 GRC Application, Table 5, p.41
</div>

<div class="mt-2 text-xs">
<a href="https://docs.cpuc.ca.gov/SearchRes.aspx?DocFormat=ALL&DocID=555555555" class="underline opacity-70">CPUC Docket Search</a>
</div>

</div>

<div class="text-sm">

**How Staff Reviews This Filing**

| Review Area | Where to Look |
|-------------|---------------|
| O&M Reasonableness | Exhibits PG&E-3 to PG&E-9 |
| Rate Base | Exhibit PG&E-10, Ch. 12 |
| Depreciation | Exhibit PG&E-10, Ch. 8-9 |
| Forecast Method | Exhibit PG&E-11 |

<div class="mt-4 font-bold">My Analysis vs This Filing</div>

| Metric | PG&E Filing | My Analysis |
|--------|-------------|-------------|
| O&M Growth | ~8% request | 6.2% CAGR |
| Bill Impact | +5.2% | +4.4% |
| Rate Base | $67B | $47B |

<div class="mt-3 text-xs opacity-60">
Note: PG&E filing covers electric AND gas operations.
My analysis covers electric only.
</div>

</div>

</div>

---
class: px-20 py-10
---

# Key Metrics for 2023

<div class="mt-4 text-sm opacity-70">
Why these metrics matter in a GRC
</div>

<div class="mt-6 grid grid-cols-2 gap-8">

<div class="text-sm space-y-2">

| Metric | GRC Relevance |
|--------|---------------|
| O&M per Customer | Tests cost reasonableness relative to service |
| O&M CAGR | Shows if growth aligns with inflation |
| Monthly Bill | Measures affordability impact |
| Revenue Requirement | Central amount utility seeks to collect |

</div>

<div>

| Metric | PG&E | SCE | SDG&E |
|--------|------|-----|-------|
| O&M per Customer | $4,099 | $1,353 | $2,982 |
| O&M CAGR | 6.2% | 0.7% | 0.6% |
| Monthly Bill | $170 | $162 | $227 |
| Revenue Req. | $27.9B | $22.9B | $6.5B |

<div class="mt-4 text-xs opacity-60">
O&M per Customer excludes production costs
</div>

<div class="text-xs opacity-60">
PG&E CAGR uses 2020-2023 post-bankruptcy baseline
</div>

</div>

</div>

---
class: px-20 py-10
---

# Peer Comparison

<div class="mt-2 text-sm opacity-70">
Why benchmarking matters in a GRC
</div>

<div class="mt-2 text-sm">
CPUC staff compares utilities to assess relative efficiency. A utility significantly above peers must justify the difference.
</div>

<div class="mt-4">
<img src="/peer_comparison_cost_per_customer.png" class="mx-auto h-64" />
</div>

<div class="mt-4 text-center">
PG&E's controllable O&M is <span class="text-red-400 font-bold">46% above peer average</span>
</div>

<div class="mt-2 text-sm opacity-60 text-center">
In a real GRC, this would prompt questions about cost management practices.
</div>

---
class: px-20 py-10
---

# Variance Decomposition

<div class="mt-4 grid grid-cols-2 gap-12">

<div>
```python
# PG&E O&M change 2020-2023
total_change = 2.50  # $B

# Regression attribution
explained = 1.82     # rate base growth
unexplained = 0.68   

pct_explained = explained / total_change
# Result: 73%
```

<div class="mt-4 bg-white/10 rounded-lg p-4 text-sm">
```
Total O&M Change:  $2.50B
Explained:         $1.82B (73%)
Unexplained:       $0.68B
```

</div>

</div>

<div>

<div class="font-bold mb-3">What This Shows</div>

<div class="text-sm mb-4">
The regression explains 73% of PG&E's cost growth through rate base expansion. The remaining $680M is unexplained by the model.
</div>

<div class="font-bold mb-3">Why This Matters Educationally</div>

<div class="text-sm mb-4">
In regulatory analysis, unexplained variance is where questions begin. It could reflect:
</div>

<div class="text-sm space-y-1 opacity-80">

- Legitimate costs not in the model (wildfire, safety)
- Inefficiency or cost overruns
- Limitations in my analysis

</div>

<div class="text-sm mt-4 opacity-60">
I cannot determine which without detailed workpapers.
</div>

</div>

</div>

---
class: px-20 py-10
---

# Questions This Raises

<div class="mt-4 text-sm opacity-70">
What I would want to understand with more data
</div>

<div class="mt-6" />

| Observation | What I Would Want to Understand |
|-------------|--------------------------------|
| PG&E O&M growth 8x peer rate | Is this driven by specific mandates (wildfire, safety) or general cost increases? |
| PG&E cost per customer 46% above peers | Are there service territory factors (geography, density) that justify this? |
| $680M unexplained in regression | What specific cost categories are driving this? |
| SDG&E highest bills despite mid-pack O&M | Is the rate design allocating fixed costs fairly? |

<div class="mt-8 text-sm opacity-60">
I do not know if CPUC staff has access to the data needed to answer these questions, but these are the inquiries this analysis suggests.
</div>

---
class: px-20 py-10
---

# How I Built This

<div class="mt-6 grid grid-cols-2 gap-12">

<div>

<div class="font-bold mb-3">Data Sources</div>

<div class="text-sm space-y-1">

- FERC Form 1 via PUDL (data.catalyst.coop/pudl)
- EIA-861 (eia.gov/electricity/data/eia861)
- Years 2018 to 2023
- Utilities: PG&E, SCE, SDG&E

</div>

<div class="font-bold mb-3 mt-6">Methods</div>

<div class="text-sm space-y-1">

- Cost driver regression (R² = 0.93)
- Trend analysis with CAGR
- Peer benchmarking
- PG&E pre-2020 excluded (bankruptcy)

</div>

</div>

<div>

<div class="font-bold mb-3">Assumptions</div>

<div class="text-sm space-y-1">

- Depreciation rate: 3.5%
- WACC: 7.5%
- Tax rate: 27%
- Avg residential usage: 500 kWh/month

</div>

<div class="font-bold mb-3 mt-6">Tools</div>

<div class="text-sm space-y-1">

- Python (pandas, statsmodels)
- FERC Form 1 parquet files
- EIA-861 Excel files

</div>

</div>

</div>

<div class="mt-8 text-center opacity-60">
github.com/AdrianNie123/utilities-data-practice-rate-case
</div>
