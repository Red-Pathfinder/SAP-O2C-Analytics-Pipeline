import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ─────────────────────────────────────────────
# SECTION 1: DATA GENERATION
# Simulating SAP table extracts
# ─────────────────────────────────────────────

N_ORDERS = 300

# --- VBAK: Sales Document Header ---
vbak = pd.DataFrame({
    'VBELN': [f'SO{str(i).zfill(6)}' for i in range(1, N_ORDERS + 1)],
    'AUDAT': pd.to_datetime('2024-01-01') + pd.to_timedelta(
        np.random.randint(0, 365, N_ORDERS), unit='d'
    ),
    'KUNNR': np.random.choice([f'CUST{str(i).zfill(4)}' for i in range(1, 51)], N_ORDERS),
    'VKORG': np.random.choice(['1000', '2000', '3000'], N_ORDERS),   # Sales Org
    'VTWEG': np.random.choice(['10', '20'], N_ORDERS),                # Distribution Channel
    'NETWR': np.random.uniform(1000, 150000, N_ORDERS).round(2),      # Net order value
    'WAERK': 'INR',                                                    # Currency
    'VBTYP': 'C',                                                      # Doc category: Sales Order
})

# --- VBAP: Sales Document Item ---
MATERIALS = {
    'MAT-LAPTOP': ('Electronics', 45000),
    'MAT-MONITOR': ('Electronics', 18000),
    'MAT-KEYBOARD': ('Electronics', 2500),
    'MAT-CHAIR': ('Furniture', 12000),
    'MAT-DESK': ('Furniture', 25000),
    'MAT-HEADSET': ('Electronics', 5500),
    'MAT-WEBCAM': ('Electronics', 3200),
    'MAT-CABINET': ('Furniture', 8000),
}

vbap_rows = []
for _, order in vbak.iterrows():
    n_items = np.random.randint(1, 5)
    selected_mats = np.random.choice(list(MATERIALS.keys()), n_items, replace=False)
    for pos_idx, mat in enumerate(selected_mats, start=10):
        base_price = MATERIALS[mat][1]
        qty = np.random.randint(1, 20)
        vbap_rows.append({
            'VBELN': order['VBELN'],
            'POSNR': f'{pos_idx:04d}',           # Item position number
            'MATNR': mat,                          # Material number
            'MATKL': MATERIALS[mat][0],            # Material group
            'KWMENG': qty,                         # Order quantity
            'NETPR': round(base_price * np.random.uniform(0.9, 1.15), 2),  # Net price
            'NETWR': 0,                            # Will compute below
        })

vbap = pd.DataFrame(vbap_rows)
vbap['NETWR'] = (vbap['KWMENG'] * vbap['NETPR']).round(2)

# --- LIKP: Delivery Header ---
delivered_orders = vbak.sample(frac=0.85, random_state=7)
likp = pd.DataFrame({
    'VBELN': [f'DL{str(i).zfill(6)}' for i in range(1, len(delivered_orders) + 1)],
    'VGBEL': delivered_orders['VBELN'].values,    # Reference to sales order
    'LFDAT': delivered_orders['AUDAT'].values + pd.to_timedelta(
        np.random.randint(1, 21, len(delivered_orders)), unit='d'
    ),                                             # Planned delivery date
    'WADAT_IST': delivered_orders['AUDAT'].values + pd.to_timedelta(
        np.random.randint(2, 28, len(delivered_orders)), unit='d'
    ),                                             # Actual goods issue date
    'LFART': np.random.choice(['LF', 'LFRE'], len(delivered_orders)),  # Delivery type
})

# --- VBRK: Billing Document Header ---
billed_deliveries = likp.sample(frac=0.80, random_state=13)
vbrk = pd.DataFrame({
    'VBELN': [f'BI{str(i).zfill(6)}' for i in range(1, len(billed_deliveries) + 1)],
    'ZUONR': billed_deliveries['VGBEL'].values,   # Assignment = original sales order
    'FKDAT': billed_deliveries['WADAT_IST'].values + pd.to_timedelta(
        np.random.randint(1, 10, len(billed_deliveries)), unit='d'
    ),                                             # Billing date
    'NETWR': billed_deliveries['VGBEL'].map(
        vbak.set_index('VBELN')['NETWR']
    ).values * np.random.uniform(0.95, 1.0, len(billed_deliveries)),
    'FKART': np.random.choice(['F2', 'F1'], len(billed_deliveries)),   # Billing type
    'WAERK': 'INR',
})

print("✓ SAP Table Simulation Complete")
print(f"  VBAK (Sales Orders):      {len(vbak):>4} rows")
print(f"  VBAP (Sales Items):       {len(vbap):>4} rows")
print(f"  LIKP (Deliveries):        {len(likp):>4} rows")
print(f"  VBRK (Billing Docs):      {len(vbrk):>4} rows")


# ─────────────────────────────────────────────
# SECTION 2: DATA PROCESSING (THE PIPELINE)
# ─────────────────────────────────────────────

# Step 1: Header + Items (the core SD document)
df = vbak.merge(vbap, on='VBELN', how='inner', suffixes=('_HDR', '_ITM'))

# Step 2: Attach delivery info
df = df.merge(
    likp[['VGBEL', 'LFDAT', 'WADAT_IST', 'LFART']],
    left_on='VBELN', right_on='VGBEL',
    how='left'
)

# Step 3: Attach billing info
df = df.merge(
    vbrk[['ZUONR', 'FKDAT', 'NETWR', 'FKART']],
    left_on='VBELN', right_on='ZUONR',
    how='left',
    suffixes=('', '_BILL')
)

# Derived fields
df['ORDER_MONTH'] = df['AUDAT'].dt.to_period('M')
df['LEAD_TIME_DAYS'] = (df['WADAT_IST'] - df['AUDAT']).dt.days
df['IS_DELIVERED'] = df['WADAT_IST'].notna()
df['IS_BILLED'] = df['FKDAT'].notna()
df['ITEM_REVENUE'] = df['NETWR_ITM']

print("\n✓ Data Pipeline Complete")
print(f"  Merged dataset shape: {df.shape}")
print(f"  Delivery rate: {df['IS_DELIVERED'].mean():.1%}")
print(f"  Billing rate:  {df['IS_BILLED'].mean():.1%}")


# ─────────────────────────────────────────────
# SECTION 3: ANALYTICS & VISUALIZATIONS
# ─────────────────────────────────────────────

fig = plt.figure(figsize=(20, 18), dpi=100, facecolor='#0D1117')

# Using tight_layout rect instead of manual GridSpec margins — this is
# DPI-stable across Windows/macOS/Linux because tight_layout measures
# actual rendered text bounding boxes, not assumed fractions.
# rect=[left, bottom, right, top] reserves the top 8% for the suptitle.
gs = gridspec.GridSpec(2, 2, figure=fig,
                        hspace=0.52, wspace=0.35,
                        height_ratios=[1, 1.15])

fig.suptitle(
    'SAP SD — Order-to-Cash Analytics Dashboard',
    fontsize=22, fontweight='bold', color='#E6EDF3',
    fontfamily='monospace'
    # No manual y= here — tight_layout will position it correctly
)

AX_COLOR = '#161B22'
GRID_COLOR = '#21262D'
TEXT_COLOR = '#C9D1D9'
ACCENT = '#58A6FF'
ACCENT2 = '#3FB950'
MUTED = '#8B949E'

PALETTE = ['#58A6FF', '#3FB950', '#D29922', '#F78166', '#BC8CFF',
           '#39D353', '#FF7B72', '#79C0FF', '#FFA657']

# ── VIZ 1: Revenue by Material ──────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(AX_COLOR)

rev_by_mat = (df.groupby('MATNR')['ITEM_REVENUE']
               .sum()
               .sort_values(ascending=True)
               .tail(8))

bars = ax1.barh(
    rev_by_mat.index.str.replace('MAT-', ''),
    rev_by_mat.values / 1e6,
    color=PALETTE[:len(rev_by_mat)],
    edgecolor='none', height=0.65
)

for bar, val in zip(bars, rev_by_mat.values):
    ax1.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
             f'₹{val/1e6:.2f}M', va='center', fontsize=9,
             color=TEXT_COLOR, fontfamily='monospace')

ax1.set_xlabel('Revenue (₹ Millions)', color=MUTED, fontsize=9)
ax1.set_title('Revenue by Material (VBAP.NETWR)', color='#E6EDF3',
              fontsize=12, fontweight='bold', pad=12)
ax1.tick_params(colors=TEXT_COLOR, labelsize=9)
ax1.spines[:].set_color(GRID_COLOR)
ax1.set_xlim(0, rev_by_mat.max() / 1e6 * 1.25)
ax1.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'₹{x:.0f}M'))
ax1.grid(axis='x', color=GRID_COLOR, linewidth=0.8, alpha=0.7)
ax1.set_axisbelow(True)

# ── VIZ 2: Order-to-Delivery Lead Time Distribution ─────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(AX_COLOR)

lead_times = df[df['LEAD_TIME_DAYS'].notna()]['LEAD_TIME_DAYS']

n, bins, patches = ax2.hist(lead_times, bins=25, color=ACCENT,
                             edgecolor='#0D1117', linewidth=0.5, alpha=0.85)

for patch, left_edge in zip(patches, bins[:-1]):
    if left_edge <= 7:
        patch.set_facecolor('#3FB950')
    elif left_edge <= 14:
        patch.set_facecolor('#D29922')
    else:
        patch.set_facecolor('#F78166')

ax2.axvline(lead_times.mean(), color='#E6EDF3', linestyle='--',
            linewidth=1.5, label=f'Mean: {lead_times.mean():.1f}d')
ax2.axvline(7, color='#3FB950', linestyle=':', linewidth=1.2, alpha=0.8, label='SLA: 7d')
ax2.axvline(14, color='#D29922', linestyle=':', linewidth=1.2, alpha=0.8, label='Warning: 14d')

ax2.legend(fontsize=8.5, framealpha=0.2, labelcolor=TEXT_COLOR, facecolor='#21262D', edgecolor=GRID_COLOR)
ax2.set_xlabel('Lead Time (Days from Order to Goods Issue)', color=MUTED, fontsize=9)
ax2.set_ylabel('Number of Orders', color=MUTED, fontsize=9)
ax2.set_title('Order-to-Delivery Lead Time\n(AUDAT → WADAT_IST)', color='#E6EDF3',
              fontsize=12, fontweight='bold', pad=12)
ax2.tick_params(colors=TEXT_COLOR, labelsize=9)
ax2.spines[:].set_color(GRID_COLOR)
ax2.grid(axis='y', color=GRID_COLOR, linewidth=0.8, alpha=0.7)
ax2.set_axisbelow(True)

on_time_pct = (lead_times <= 7).mean()
ax2.text(0.97, 0.95, f'On-time: {on_time_pct:.0%}',
         transform=ax2.transAxes, ha='right', va='top',
         fontsize=10, color='#3FB950', fontfamily='monospace', fontweight='bold')

# ── VIZ 3: Monthly Sales Trend ──────────────────────────────────────────────
ax3 = fig.add_subplot(gs[1, :])
ax3.set_facecolor(AX_COLOR)

monthly = (df.groupby('ORDER_MONTH')
             .agg(
                 REVENUE=('ITEM_REVENUE', 'sum'),
                 ORDER_COUNT=('VBELN', 'nunique'),
                 BILLED=('IS_BILLED', 'sum')
             )
             .reset_index())
monthly['ORDER_MONTH_STR'] = monthly['ORDER_MONTH'].astype(str)
monthly['REVENUE_M'] = monthly['REVENUE'] / 1e6

x = range(len(monthly))

ax3.fill_between(x, monthly['REVENUE_M'], alpha=0.15, color=ACCENT, zorder=1)
line1, = ax3.plot(x, monthly['REVENUE_M'], color=ACCENT, linewidth=2.5, zorder=3, marker='o', markersize=5, label='Revenue (₹M)')

ax3b = ax3.twinx()
ax3b.set_facecolor('none')
bars2 = ax3b.bar(x, monthly['ORDER_COUNT'], color=ACCENT2, alpha=0.35, width=0.6, zorder=2, label='Order Volume')
ax3b.tick_params(colors=ACCENT2, labelsize=8.5)
ax3b.set_ylabel('Order Count', color=ACCENT2, fontsize=9)
ax3b.spines[:].set_color(GRID_COLOR)

rolling_rev = monthly['REVENUE_M'].rolling(3, min_periods=1).mean()
ax3.plot(x, rolling_rev, color='#F78166', linewidth=2, linestyle='--', zorder=4, label='3M Rolling Avg')

ax3.set_xticks(list(x))
ax3.set_xticklabels(monthly['ORDER_MONTH_STR'], rotation=45, ha='right', fontsize=8.5, color=TEXT_COLOR)
ax3.set_ylabel('Revenue (₹ Millions)', color=ACCENT, fontsize=9)
ax3.set_title('Monthly Sales Trend — Revenue & Order Volume (2024)\nSource: VBAK.AUDAT + VBAP.NETWR', color='#E6EDF3', fontsize=12, fontweight='bold', pad=12)
ax3.tick_params(colors=TEXT_COLOR, labelsize=9)
ax3.spines[:].set_color(GRID_COLOR)
ax3.grid(axis='y', color=GRID_COLOR, linewidth=0.8, alpha=0.7)
ax3.set_axisbelow(True)
ax3.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'₹{y:.1f}M'))

handles = [line1, plt.Line2D([0], [0], color='#F78166', linestyle='--', linewidth=2, label='3M Rolling Avg'), mpatches.Patch(color=ACCENT2, alpha=0.5, label='Order Volume')]
ax3.legend(handles=handles, fontsize=9, framealpha=0.2, labelcolor=TEXT_COLOR, facecolor='#21262D', edgecolor=GRID_COLOR, loc='upper left')

# Footer
fig.text(0.5, 0.01, 'Simulated SAP SD Tables: VBAK · VBAP · LIKP · VBRK  |  O2C Pipeline Simulation  |  All values in INR', ha='center', color=MUTED, fontsize=8, fontfamily='monospace')

# DIRECTORY PATH FIX APPLIED HERE
fig.tight_layout(rect=[0.0, 0.02, 1.0, 0.95])
plt.savefig('sap_o2c_dashboard.png', dpi=150, bbox_inches='tight', facecolor='#0D1117')
print("\n✓ Dashboard saved → sap_o2c_dashboard.png")
plt.show()

# ─────────────────────────────────────────────
# SECTION 4: SUMMARY KPI REPORT
# ─────────────────────────────────────────────
total_revenue = df['ITEM_REVENUE'].sum()
billed_revenue = vbrk['NETWR'].sum()
unbilled = total_revenue - billed_revenue
avg_lead = lead_times.mean()
top_material = rev_by_mat.idxmax().replace('MAT-', '')

print("\n" + "="*55)
print("  SAP O2C SUMMARY KPIs")
print("="*55)
print(f"  Total Order Value (VBAP):    ₹{total_revenue/1e7:.2f} Cr")
print(f"  Billed Revenue (VBRK):       ₹{billed_revenue/1e7:.2f} Cr")
print(f"  Unbilled / Open (AR Risk):   ₹{unbilled/1e7:.2f} Cr")
print(f"  Avg Lead Time:               {avg_lead:.1f} days")
print(f"  On-Time Delivery Rate:       {on_time_pct:.1%}")
print(f"  Top Revenue Material:        {top_material}")
print(f"  Fulfillment Rate:            {df['IS_DELIVERED'].mean():.1%}")
print("="*55)