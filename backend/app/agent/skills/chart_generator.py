import json
import os
import base64
import io
import uuid
from langchain_core.tools import tool

# Set matplotlib backend before importing pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

# Module-level chart store: chart_id → base64 PNG
# The SSE handler reads from here so the LLM never sees the raw image data
chart_store: dict[str, str] = {}

# Configure Seaborn style for dark theme
sns.set_theme(style="darkgrid")
plt.rcParams.update({
    'figure.facecolor': '#111827',
    'axes.facecolor': '#1a2236',
    'axes.edgecolor': '#374151',
    'axes.labelcolor': '#e2e8f0',
    'text.color': '#e2e8f0',
    'xtick.color': '#94a3b8',
    'ytick.color': '#94a3b8',
    'grid.color': '#1e293b',
    'figure.figsize': (10, 6),
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
})

COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#22c55e', '#f59e0b',
          '#ef4444', '#ec4899', '#14b8a6', '#f97316', '#a78bfa']


def _fig_to_base64(fig) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def _load_json(filename: str):
    with open(os.path.join(DATA_DIR, filename), "r") as f:
        return json.load(f)


def _store_chart(img_b64: str, chart_type: str, summary: str) -> str:
    """Store chart image in module-level dict and return summary-only JSON for the LLM."""
    chart_id = str(uuid.uuid4())
    chart_store[chart_id] = img_b64
    return json.dumps({
        "chart_generated": True,
        "chart_id": chart_id,
        "chart_type": chart_type,
        "summary": summary,
        "note": "The chart has been rendered and displayed to the user."
    }, indent=2)


@tool
def generate_chart(chart_type: str, subject: str) -> str:
    """Generate a performance chart or comparison visualization.
    Use this tool when the user asks for charts, graphs, comparisons, or visual data.

    chart_type options:
    - 'material_comparison': Compare material properties (tensile strength, hardness, cost, density)
    - 'work_order_performance': Show OEE, scrap rate, cycle time across work orders
    - 'equipment_utilization': Show machine utilization and OEE comparison
    - 'equipment_oee_trend': Show daily OEE trend for a specific machine
    - 'defect_analysis': Show defect rates across work orders

    subject: Additional context (e.g., 'titanium vs stainless steel', 'CNC-001', 'all')
    """
    try:
        if chart_type == "material_comparison":
            return _material_comparison_chart(subject)
        elif chart_type == "work_order_performance":
            return _work_order_performance_chart(subject)
        elif chart_type == "equipment_utilization":
            return _equipment_utilization_chart(subject)
        elif chart_type == "equipment_oee_trend":
            return _equipment_oee_trend_chart(subject)
        elif chart_type == "defect_analysis":
            return _defect_analysis_chart(subject)
        else:
            return json.dumps({"error": f"Unknown chart type: {chart_type}. Available: material_comparison, work_order_performance, equipment_utilization, equipment_oee_trend, defect_analysis"})
    except Exception as e:
        return json.dumps({"error": f"Chart generation failed: {str(e)}"})


def _material_comparison_chart(subject: str) -> str:
    materials = _load_json("materials.json")

    subject_lower = subject.lower()
    if subject_lower not in ("all", ""):
        keywords = [w.strip() for w in subject_lower.replace(" vs ", ",").replace(" and ", ",").replace("versus", ",").split(",")]
        filtered = [m for m in materials if any(kw in m["name"].lower() or kw in m["category"].lower() for kw in keywords)]
        if filtered:
            materials = filtered

    short_names = [m["name"].split(" ")[0] for m in materials]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Material Properties Comparison", fontsize=16, fontweight='bold', color='#a78bfa')

    values = [m["properties"]["tensile_strength_mpa"] for m in materials]
    bars = axes[0, 0].barh(short_names, values, color=COLORS[:len(materials)], edgecolor='none')
    axes[0, 0].set_xlabel("MPa")
    axes[0, 0].set_title("Tensile Strength")
    for bar, val in zip(bars, values):
        axes[0, 0].text(bar.get_width() + 20, bar.get_y() + bar.get_height()/2, f'{val}', va='center', fontsize=9, color='#94a3b8')

    values = [m["properties"]["hardness_hrc"] or 0 for m in materials]
    bars = axes[0, 1].barh(short_names, values, color=COLORS[:len(materials)], edgecolor='none')
    axes[0, 1].set_xlabel("HRC")
    axes[0, 1].set_title("Hardness")
    for bar, val in zip(bars, values):
        axes[0, 1].text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f'{val}', va='center', fontsize=9, color='#94a3b8')

    values = [m["properties"]["cost_per_kg_usd"] for m in materials]
    bars = axes[1, 0].barh(short_names, values, color=COLORS[:len(materials)], edgecolor='none')
    axes[1, 0].set_xlabel("USD/kg")
    axes[1, 0].set_title("Cost per Kilogram")
    for bar, val in zip(bars, values):
        axes[1, 0].text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f'${val}', va='center', fontsize=9, color='#94a3b8')

    values = [m["properties"]["machinability_rating"] for m in materials]
    bars = axes[1, 1].barh(short_names, values, color=COLORS[:len(materials)], edgecolor='none')
    axes[1, 1].set_xlabel("Rating (0-100)")
    axes[1, 1].set_title("Machinability Rating")
    for bar, val in zip(bars, values):
        axes[1, 1].text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f'{val}', va='center', fontsize=9, color='#94a3b8')

    fig.tight_layout()
    img_b64 = _fig_to_base64(fig)
    summary = f"Generated material comparison chart for {len(materials)} materials showing tensile strength, hardness, cost, and machinability."
    return _store_chart(img_b64, "material_comparison", summary)


def _work_order_performance_chart(subject: str) -> str:
    work_orders = _load_json("work_orders.json")
    active_wos = [wo for wo in work_orders if wo["performance_metrics"]["oee_pct"] is not None]

    ids = [wo["work_order_id"] for wo in active_wos]
    oee = [wo["performance_metrics"]["oee_pct"] for wo in active_wos]
    scrap = [wo["performance_metrics"]["scrap_rate_pct"] for wo in active_wos]
    cycle_actual = [wo["performance_metrics"]["cycle_time_min"] for wo in active_wos]
    cycle_target = [wo["performance_metrics"]["target_cycle_time_min"] for wo in active_wos]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Work Order Performance Dashboard", fontsize=16, fontweight='bold', color='#a78bfa')

    bar_colors = ['#22c55e' if v >= 80 else '#f59e0b' if v >= 65 else '#ef4444' for v in oee]
    axes[0].bar(ids, oee, color=bar_colors, edgecolor='none')
    axes[0].axhline(y=85, color='#22c55e', linestyle='--', alpha=0.5, label='Target 85%')
    axes[0].set_ylabel("OEE %")
    axes[0].set_title("Overall Equipment Effectiveness")
    axes[0].legend(fontsize=9)
    axes[0].tick_params(axis='x', rotation=45)

    bar_colors = ['#22c55e' if v <= 2 else '#f59e0b' if v <= 5 else '#ef4444' for v in scrap]
    axes[1].bar(ids, scrap, color=bar_colors, edgecolor='none')
    axes[1].axhline(y=2.0, color='#22c55e', linestyle='--', alpha=0.5, label='Target ≤2%')
    axes[1].set_ylabel("Scrap Rate %")
    axes[1].set_title("Scrap Rate")
    axes[1].legend(fontsize=9)
    axes[1].tick_params(axis='x', rotation=45)

    x_pos = range(len(ids))
    axes[2].bar([p - 0.15 for p in x_pos], cycle_actual, 0.3, label='Actual', color='#6366f1')
    axes[2].bar([p + 0.15 for p in x_pos], cycle_target, 0.3, label='Target', color='#374151', alpha=0.7)
    axes[2].set_xticks(list(x_pos))
    axes[2].set_xticklabels(ids, rotation=45)
    axes[2].set_ylabel("Minutes")
    axes[2].set_title("Cycle Time vs Target")
    axes[2].legend(fontsize=9)

    fig.tight_layout()
    img_b64 = _fig_to_base64(fig)
    summary = f"Generated work order performance dashboard showing OEE, scrap rate, and cycle time for {len(active_wos)} work orders."
    return _store_chart(img_b64, "work_order_performance", summary)


def _equipment_utilization_chart(subject: str) -> str:
    equipment = _load_json("equipment.json")

    names = [e["machine_id"] for e in equipment]
    utilization = [e["utilization_pct"] for e in equipment]
    avg_oee = [sum(e["performance_history"]["daily_oee"]) / max(len(e["performance_history"]["daily_oee"]), 1) for e in equipment]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Equipment Performance Overview", fontsize=16, fontweight='bold', color='#a78bfa')

    bar_colors = ['#22c55e' if v >= 70 else '#f59e0b' if v >= 40 else '#ef4444' for v in utilization]
    bars = axes[0].bar(names, utilization, color=bar_colors, edgecolor='none')
    axes[0].set_ylabel("Utilization %")
    axes[0].set_title("Current Utilization")
    axes[0].set_ylim(0, 100)
    for bar, val in zip(bars, utilization):
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{val}%', ha='center', fontsize=10, color='#e2e8f0')

    bar_colors = ['#22c55e' if v >= 80 else '#f59e0b' if v >= 60 else '#ef4444' for v in avg_oee]
    bars = axes[1].bar(names, avg_oee, color=bar_colors, edgecolor='none')
    axes[1].axhline(y=85, color='#22c55e', linestyle='--', alpha=0.5, label='World-class 85%')
    axes[1].set_ylabel("Average OEE %")
    axes[1].set_title("7-Day Average OEE")
    axes[1].set_ylim(0, 100)
    axes[1].legend(fontsize=9)
    for bar, val in zip(bars, avg_oee):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{val:.1f}%', ha='center', fontsize=10, color='#e2e8f0')

    fig.tight_layout()
    img_b64 = _fig_to_base64(fig)
    summary = f"Generated equipment utilization dashboard for {len(equipment)} machines."
    return _store_chart(img_b64, "equipment_utilization", summary)


def _equipment_oee_trend_chart(subject: str) -> str:
    equipment = _load_json("equipment.json")

    machine = None
    for e in equipment:
        if subject.upper() in e["machine_id"].upper() or subject.lower() in e["name"].lower():
            machine = e
            break

    if not machine:
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle("Daily OEE Trend — All Machines", fontsize=16, fontweight='bold', color='#a78bfa')
        for i, e in enumerate(equipment):
            history = e["performance_history"]
            ax.plot(history["labels"], history["daily_oee"], marker='o', label=e["machine_id"],
                    color=COLORS[i], linewidth=2, markersize=6)
        ax.axhline(y=85, color='#22c55e', linestyle='--', alpha=0.4, label='Target 85%')
        ax.set_ylabel("OEE %")
        ax.set_ylim(0, 100)
        ax.legend(fontsize=9)
        fig.tight_layout()
        img_b64 = _fig_to_base64(fig)
        summary = f"Generated OEE trend chart for all {len(equipment)} machines."
        return _store_chart(img_b64, "equipment_oee_trend", summary)

    history = machine["performance_history"]
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle(f"{machine['machine_id']} — {machine['name']} Performance Trend", fontsize=14, fontweight='bold', color='#a78bfa')

    axes[0].plot(history["labels"], history["daily_oee"], marker='o', color='#6366f1', linewidth=2.5, markersize=8)
    axes[0].fill_between(history["labels"], history["daily_oee"], alpha=0.15, color='#6366f1')
    axes[0].axhline(y=85, color='#22c55e', linestyle='--', alpha=0.5, label='Target 85%')
    axes[0].set_ylabel("OEE %")
    axes[0].set_title("Daily OEE")
    axes[0].set_ylim(0, 100)
    axes[0].legend(fontsize=9)

    axes[1].bar(history["labels"], history["weekly_downtime_hours"], color='#ef4444', alpha=0.8, edgecolor='none')
    axes[1].set_ylabel("Downtime (hours)")
    axes[1].set_title("Daily Downtime")

    fig.tight_layout()
    img_b64 = _fig_to_base64(fig)
    summary = f"Generated OEE trend and downtime chart for {machine['machine_id']}."
    return _store_chart(img_b64, "equipment_oee_trend", summary)


def _defect_analysis_chart(subject: str) -> str:
    work_orders = _load_json("work_orders.json")
    active_wos = [wo for wo in work_orders if wo["performance_metrics"]["oee_pct"] is not None]

    ids = [wo["work_order_id"] for wo in active_wos]
    defects = [wo["defects_found"] for wo in active_wos]
    scrap = [wo["performance_metrics"]["scrap_rate_pct"] for wo in active_wos]
    quality = [wo["performance_metrics"]["quality_pct"] for wo in active_wos]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Quality & Defect Analysis", fontsize=16, fontweight='bold', color='#a78bfa')

    bar_colors = ['#22c55e' if v <= 1 else '#f59e0b' if v <= 3 else '#ef4444' for v in defects]
    axes[0].bar(ids, defects, color=bar_colors, edgecolor='none')
    axes[0].set_ylabel("Defects Found")
    axes[0].set_title("Defects per Work Order")
    axes[0].tick_params(axis='x', rotation=45)

    bar_colors = ['#22c55e' if v >= 98 else '#f59e0b' if v >= 95 else '#ef4444' for v in quality]
    axes[1].bar(ids, quality, color=bar_colors, edgecolor='none')
    axes[1].axhline(y=99, color='#22c55e', linestyle='--', alpha=0.5, label='Target 99%')
    axes[1].set_ylabel("Quality %")
    axes[1].set_title("Quality Rate")
    axes[1].set_ylim(90, 101)
    axes[1].legend(fontsize=9)
    axes[1].tick_params(axis='x', rotation=45)

    axes[2].scatter(scrap, quality, c=COLORS[:len(active_wos)], s=120, edgecolors='white', linewidth=1, zorder=5)
    for i, wo_id in enumerate(ids):
        axes[2].annotate(wo_id, (scrap[i], quality[i]), fontsize=8, color='#94a3b8',
                         textcoords="offset points", xytext=(5, 5))
    axes[2].set_xlabel("Scrap Rate %")
    axes[2].set_ylabel("Quality %")
    axes[2].set_title("Scrap Rate vs Quality")

    fig.tight_layout()
    img_b64 = _fig_to_base64(fig)
    summary = f"Generated defect analysis dashboard showing defects, quality rate, and scrap vs quality for {len(active_wos)} work orders."
    return _store_chart(img_b64, "defect_analysis", summary)
