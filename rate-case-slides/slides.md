---
theme: default
title: Rate Case Baseline Analysis
class: text-center
highlighter: shiki
colorSchema: dark
transition: fade-out
mdc: true
---

# Jumping into Public Utility Data

California Investor-Owned Utilities 2018 to 2023 ( Energy only* )

<div class="mt-40 text-xl opacity-70">
Adrian Nie
</div>

<div class="mt-4 text-sm opacity-50">
An educational self-driven analysis using publicly available federal regulatory data 
</div>

---
class: flex items-center justify-center
---

<div class="border border-white/20 rounded-xl p-8 bg-white/5 w-96">

<div class="text-xl font-bold mb-6 text-center">Table of Contents</div>

<div class="space-y-3 text-base">

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">3</span>
<span>What is a GRC?</span>
</div>

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">4</span>
<span>What My Analysis Covers</span>
</div>

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">5</span>
<span>Data Constraints</span>
</div>

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">6</span>
<span>Metrics Reference</span>
</div>

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">7</span>
<span>Connecting to a Real GRC</span>
</div>

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">8</span>
<span>Key Metrics (2023)</span>
</div>

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">9</span>
<span>Peer Comparison</span>
</div>

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">10</span>
<span>Variance Decomposition</span>
</div>

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">11</span>
<span>Questions This Raises</span>
</div>

<div class="flex gap-4">
<span class="opacity-40 w-6 text-right">12</span>
<span>Project Specs</span>
</div>

</div>

<div class="mt-6 pt-4 border-t border-white/10 text-center">
<span class="text-xs opacity-50">PG&E • SCE • SDG&E</span>
<span class="mx-2 opacity-30">|</span>
<span class="text-xs opacity-50">2018–2023</span>
<span class="mx-2 opacity-30">|</span>
<span class="text-xs opacity-50">Electric Only</span>
</div>

</div>

---
class: px-20 py-10
---

# To start, I wanted to answer:
<div class="mt-8" />

1. From an analytical view, what kind of changes must take place for a utilities company to need to change their rate?

2. A General Rate Case (GRC) is a formal regulatory proceeding where a utility requests approval to change the rates it charges customers.

3. Let's learn more about GRC's and the data behind utilities-related decisions

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

### What My Analysis Covers

<div class="mt-4 grid grid-cols-2 gap-8">

<div class="border border-white/10 rounded-lg p-5 bg-white/5">

<div class="font-bold text-lg mb-3">Revenue Requirement</div>

<div class="text-sm opacity-80">The total amount a utility needs to collect</div>

<div class="mt-3 text-sm space-y-1">

- O&M Expenses (GRC-scope)
- Depreciation (3.5% of rate base)
- Return on Rate Base (WACC × RB)
- Taxes (simplified)

</div>

<div class="mt-3 text-xs opacity-50">
Formula I found online: RR = O&M + Depreciation + Return + Taxes
</div>

</div>

<div class="border border-white/10 rounded-lg p-5 bg-white/5">

<div class="font-bold text-lg mb-3">Reasonableness Tests</div>

<div class="text-sm opacity-80">Methods to evaluate if costs are justified</div>

<div class="mt-3 text-sm space-y-1">

- Historical trend analysis (CAGR)
- Peer benchmarking (vs SCE, SDG&E)
- Cost driver regression (O&M ~ Rate Base)
- Bill impact estimation

</div>

<div class="mt-3 text-xs opacity-50">
Question: Are these costs reasonable?
</div>

</div>

</div>

<div class="mt-6 text-center text-sm opacity-60">
Focus: Electric operations only | GRC-comparable scope (excludes ERRA, transmission)
</div>

---
class: px-20 py-10
---

### Constraint: Limited Public Data 

<div class="mt-4 grid grid-cols-2 gap-10">

<div class="border border-white/10 rounded-lg p-6 bg-white/5">

<div class="font-bold text-lg mb-4">What Public Data Enabled</div>

<div class="text-sm mb-1 opacity-70">Using FERC Form 1 and EIA-861 (2018 - 2023 Energy)</div>

<div class="mt-1 text-sm">

**Analyses Possible**
- Trend analysis and CAGR
- Peer benchmarking
- Cost driver regression
- Bill impact estimation
- Context-based Visualizations

</div>

</div>

<div class="border border-white/10 rounded-lg p-6 bg-white/5">

<div class="font-bold text-lg mb-4">What Full Access Could Enable</div>

<div class="text-sm mb-4 opacity-70">Analyses-enabling datasources </div>

<div class="text-sm space-y-3">

<div>
<div class="font-medium">Line-item workpapers</div>
<div class="opacity-60">Are there specific programs driving cost growth?</div>
</div>

<div>
<div class="font-medium">Utility testimonials</div>
<div class="opacity-60">Understand proposed justifications</div>
</div>

<div>
<div class="font-medium">CPUC decision history</div>
<div class="opacity-60">Compare to previously authorizations and thresholds</div>
</div>

<div>
<div class="font-medium">Contracts</div>
<div class="opacity-60">Verify costs and efficiency</div>
</div>

<div>
<div class="font-medium">Asset-level depreciation</div>
<div class="opacity-60">Replace assumed 3.5% with actuals</div>
</div>

</div>

</div>

</div>

---
class: px-14 py-6
---

### Possible useful metrics for data-driven insight

<div class="grid grid-cols-3 gap-6 mt-4 text-sm">

<div class="bg-white/5 rounded-lg p-2">

**Cost Reasonableness**

| Metric | Formula |
|--------|---------|
| GRC O&M | Dist, Cust, Weighted A&G |
| O&M per Customer | O&M Customers |
| O&M per MWh | O&M ÷ Sales |
| YoY Change | (Curr - Prior) ÷ Prior |
| CAGR | (End/Start)^(1/n) - 1 |

<div class="mt-1 text-xs opacity-60">
Question: Are costs reasonable compared to peers and history?
</div>

</div>

<div class="bg-white/5 rounded-lg p-2">

**Rate Base & Return**

| Metric | Formula |
|--------|---------|
| Rate Base | Plant - Accum. Depr. |
| Rev Req | O&M + Depreciation + Return + Taxes |
| Return | Rate Base × WACC |
| WACC | (E×ROE + D×CoD) |
| RB Growth | (RB₁ - RB₀)/ RB₀ |

<div class="mt-2 text-xs opacity-60">
Question: Capital investment earning appropriate return?
</div>

</div>

<div class="bg-white/5 rounded-lg p-2">

**Customer Impact**

| Metric | Formula |
|--------|---------|
| Revenue Req | O&M + Dep + Ret + Tax |
| Bill Impact | RR ÷ Cust ÷ 12 |
| RR per MWh | RR ÷ Sales |
| Capital/Cust | Rate Base ÷ Cust |

<div class="mt-2 text-xs opacity-60">
Question: What does this mean in terms of customer impact?
</div>

</div>

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

<img src="/PGE2027GRC.png" class="h-64 border border-white/20 rounded" />
<div class="mt-2 text-xs opacity-50">
Source: PG&E 2027 GRC Application, Table 5, p.41
</div>

<div class="mt-2 text-xs">
<a href="https://www.pge.com/en/regulation/general-rate-case.html" class="underline opacity-70">PGE 2027-2030 GRC Filing</a>
</div>

Note: PG&E filing covers electric AND gas operations. My analysis covers electric only.
</div>

<div class="text-xs">

<div class="mt-4 font-bold">My Analysis vs Filing</div>

**My Analysis vs PG&E 2027 Filing**

| Component | 2027 PG&E Filing | 2023 Analysis |
|-----------|-------------|-------------------|
| Distribution O&M | ~$2.5B | $3.3B |
| Customer Service | ~$0.8B | $1.1B |
| A&G (GRC-recoverable) | $1.6B | 2.5B |
| **GRC-Comparable O&M** | **$5.8B** | **$6.9B** |

<div class="text-xs opacity-60 mt-2">
Est. 70% electric allocation. Remaining gap reflects 
year difference and data source variation.

</div>

<div class="mt-3 text-xs opacity-60">
</div>
</div>

</div>

<!--
**PGE Filing Contents**

- 351 pages of application
- 11 exhibits of testimony
- Tens of thousands of workpaper pages
- Line-item cost justifications by program

</div>
-->
---
class: px-20 py-10
---

# Key Metrics for 2023 (Electricity Only*)

<div class="mt-4 text-sm opacity-70">
Why these metrics matter in a GRC
</div>

<div class="mt-2 grid-cols-1 gap-8">

<div class="text-sm space-y-2">

</div>

<div>

| Metric | PG&E* | SCE* | SDG&E* |
|--------|------|-----|-------|
| Residential Customers | 1.83M | 3.18M | 0.46M |
| O&M per Customer (GRC) | $3,245 | $1,003 | $2,332 |
| O&M CAGR | 7.8% | -2.0% | 11.6% |
| Monthly Bill (500 kWh) | $170 | $162 | $227 |
| Revenue Req (GRC) | $13.9B | $10.3B | $3.3B |

<div class="mt-4 text-xs opacity-60">
GRC O&M = Distribution + Customer Service + A&G (70% electric allocation)
</div>

<div class="text-xs opacity-60">
PG&E CAGR uses 2020-2023 baseline (post-bankruptcy)
</div>

<div class="text-xs opacity-60">
SCE/SDG&E CAGR uses 2018-2023 baseline
</div>

</div>

</div>

---
class: px-20 py-10
---

# Visualization Ex: Peer Comparison

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
In a real GRC, this would prompt questions about 
cost management practices.
</div>

---
class: px-20 py-10
---

### Modeling Ex: Variance Decomposition

<div class="mt-4 grid grid-cols-2 gap-12">

<div>
```python
# PG&E GRC O&M change 2020-2023
grc_om_2020 = 5.49  # $B
grc_om_2023 = 6.88  # $B
total_change = 1.40  # $B

# Rate Base growth
rb_change = 6.61  # $B ($40.8B → $47.4B)

# Regression: GRC O&M ~ Rate Base
# slope = 0.158 (R² = 0.68)
explained = 0.158 * rb_change  # $1.05B
unexplained = total_change - explained

pct_explained = explained / total_change
# Result: 75%
```

<div class="mt-4 bg-white/10 rounded-lg p-4 text-sm">
```
GRC O&M Change:    $1.40B
Explained (R²=68%): $1.05B (75%)
Unexplained:        $0.35B (25%)
```

</div>

</div>

<div>

<div class="font-bold mb-3">What This Shows</div>

<div class="text-sm mb-4">
Perform regressions on PG&E's GRC O&M growth through rate base expansion. Find remaining $Amount unexplained by model. (more data > better modeling)
</div>

<div class="font-bold mb-3">Why This Matters</div>

<div class="text-sm mb-4">
In data analysis, unexplained variance prompts questions. It could reflect:
</div>

<div class="text-sm space-y-1 opacity-80">

- Legitimate costs not in the model 
- Inefficiency or cost overruns
- Data limitations in public FERC filings

</div>

<div class="text-sm mt-4 opacity-60">

</div>

</div>

</div>

---
class: px-20 py-10
---

# Questions This Raises


<div class="mt-3" />

| Observation | What I Would Want to Understand |
|-------------|--------------------------------|
| PG&E O&M growth rate vs peer | Is this driven by specific mandates (wildfire, safety) or general cost increases? |
| PG&E cost per customer above peers | Are there service territory factors (geography, density) that justify this? |
| % unexplained in regression models | What specific cost categories are driving this? |
| SDG&E highest bills? | Is the rate design allocating fixed costs fairly? |

<div class="mt-8 text-sm opacity-60">
I do not know if CPUC staff has access to the data needed to answer these questions, but these are the inquiries this analysis suggests.
</div>

---
class: px-20 py-10
---

# Notes + Project Specs -- Thank you

<div class="mt-4 grid grid-cols-2 gap-10">

<div>

<div class="font-bold mb-2">Data Sources</div>

<div class="text-sm space-y-1">

- FERC Form 1 via PUDL (Schedules 320, 200, 114)
- EIA-861 Sales & Revenue data
- 6 years (2018-2023), 3 CA IOUs
- Cross-source join via utility ID mapping

</div>

<div class="font-bold mb-2 mt-4">Methods</div>

<div class="text-sm space-y-1">

- OLS regression (cost drivers)
- CAGR and YoY trend analysis
- Peer benchmarking with z-scores
- GRC-comparable scope (matches PG&E filing)

</div>

</div>

<div>

<div class="font-bold mb-2">Assumptions</div>

<div class="text-sm space-y-1">

- Depreciation: 3.5% of rate base
- WACC: 7.5% (approximate)
- A&G allocation: 70% electric
- Avg Residential usage: 500 kWh/month

</div>

<div class="font-bold mb-2 mt-4">Built With</div>

<div class="text-sm space-y-1">

- Python (pandas, numpy, matplotlib, seaborn)
- Modular ETL pipeline (~3,900 lines, 9 modules, fully replicatable on financial sheets)
- Parquet + Excel data processing
- Slidev for presentation

</div>

</div>

</div>

<div class="mt-6 text-center text-sm opacity-70">
18 utility-years × 43 derived metrics | programmed 6 automated visualizations
</div>

<div class="mt-2 text-center opacity-60">
github.com/AdrianNie123/utilities-data-practice-rate-case
</div>
