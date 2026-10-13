"""
Builds the 4 report charts from the database into reports/figures/.

    python -m analysis.make_charts

Every number on a chart comes from the mart / the Part C query files, so if the
pipeline is re-run the charts update with it.
"""
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "olist.db"
SQL = ROOT / "sql" / "analysis"
FIG = ROOT / "reports" / "figures"

BLUE, ORANGE, GREY = "#4f81bd", "#c0504d", "#a6a6a6"
INK, INK2 = "#000000", "#333333"

plt.rcParams.update({
    # serif font so the charts match the Times-style report text
    "font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "font.size": 9.5, "axes.edgecolor": "#000000", "axes.linewidth": 0.7,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.6, "grid.linestyle": "--",
    "axes.axisbelow": True,
    "figure.dpi": 200, "savefig.bbox": "tight",
})


def q(conn, sql):
    return pd.read_sql(sql, conn)


def fig1_rolling_orders(conn):
    df = q(conn, (SQL / "q3_rolling_7day_orders.sql").read_text())
    df["day"] = pd.to_datetime(df["day"])
    df = df[(df.day >= "2017-01-01") & (df.day <= "2018-08-31")]
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    ax.bar(df.day, df.orders, width=1.0, color=GREY, alpha=0.55, label="Daily orders", linewidth=0)
    ax.plot(df.day, df.rolling_7d_avg, color=BLUE, lw=2, label="7-day rolling average")
    bf = df.loc[df.orders.idxmax()]
    ax.annotate(f"Black Friday\n{bf.day:%d %b %Y}: {int(bf.orders):,} orders",
                xy=(bf.day, bf.orders), xytext=(bf.day + pd.Timedelta(days=25), bf.orders - 150),
                fontsize=8, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.set_ylabel("Orders per day")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    fig.savefig(FIG / "fig1_rolling_orders.png")
    plt.close(fig)


def fig2_review_by_delay(conn):
    df = q(conn, (SQL / "q5_delivery_delay_vs_review.sql").read_text())
    df = df[df.delay_bucket != "ALL delivered"].copy()
    df["label"] = [f"{b[3:].replace(' days ', ' days\n').replace('on the day', 'on the\nday')}\n({int(n):,})"
                   for b, n in zip(df.delay_bucket, df.orders)]
    colors = [ORANGE if "late" in b else BLUE for b in df.delay_bucket]
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    bars = ax.bar(df.label, df.avg_review, color=colors, width=0.7)
    for b, (_, r) in zip(bars, df.iterrows()):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.07,
                f"{r.avg_review:.2f}", ha="center", fontsize=8.5, color=INK, fontweight="bold")
        ax.text(b.get_x() + b.get_width() / 2, 0.2,
                f"{r.pct_1_2_star:.0f}%\n1-2 star",
                ha="center", fontsize=7, color="white")
    ax.set_ylim(0, 5)
    ax.set_ylabel("Average review score (1-5)")
    ax.set_xlabel("Delivery vs promised date  (number of reviewed orders)", fontsize=8)
    ax.tick_params(axis="x", labelsize=7.3)
    ax.grid(axis="x", visible=False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="On time / early"), Patch(color=ORANGE, label="Late")],
              frameon=False, loc="upper right", fontsize=8)
    fig.savefig(FIG / "fig2_review_by_delay.png")
    plt.close(fig)


def fig3_monthly_late_and_review(conn):
    df = q(conn, """
        SELECT purchase_month,
               ROUND(100.0 * AVG(is_late), 1)      AS late_pct,
               ROUND(AVG(review_score), 2)         AS avg_review
        FROM mart_orders
        WHERE order_status = 'delivered' AND delivered_ts IS NOT NULL
          AND purchase_month BETWEEN '2017-01' AND '2018-08'
        GROUP BY purchase_month ORDER BY purchase_month""")
    x = pd.to_datetime(df.purchase_month + "-01")
    # two panels, one y-axis each (no dual axis)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 3.3), sharex=True,
                                 gridspec_kw={"height_ratios": [1, 1], "hspace": 0.18})
    hi = df.late_pct >= 10
    a1.bar(x, df.late_pct, width=22, color=[ORANGE if h else GREY for h in hi])
    for xi, v, h in zip(x, df.late_pct, hi):
        if h:
            a1.text(xi, v + 0.6, f"{v:.0f}%", ha="center", fontsize=7.5, color=INK)
    a1.set_ylabel("% delivered late")
    a1.set_ylim(0, 23)
    a2.plot(x, df.avg_review, color=BLUE, lw=2, marker="o", ms=4)
    a2.set_ylabel("Avg review")
    a2.set_ylim(3.7, 4.4)
    lo = df.avg_review.idxmin()
    a2.annotate(f"{df.avg_review[lo]:.2f} ({x[lo]:%b %y})", xy=(x[lo], df.avg_review[lo]),
                xytext=(x[lo] + pd.Timedelta(days=35), df.avg_review[lo] - 0.02),
                fontsize=7.5, color=INK2)
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    fig.savefig(FIG / "fig3_monthly_late_and_review.png")
    plt.close(fig)


def fig4_late_by_state(conn):
    df = q(conn, """
        SELECT customer_state, COUNT(*) AS n,
               ROUND(100.0 * AVG(is_late), 1) AS late_pct
        FROM mart_orders
        WHERE order_status = 'delivered' AND delivered_ts IS NOT NULL
        GROUP BY customer_state HAVING COUNT(*) >= 300
        ORDER BY late_pct""")
    overall = conn.execute("""SELECT 100.0 * AVG(is_late) FROM mart_orders
                              WHERE order_status='delivered' AND delivered_ts IS NOT NULL""").fetchone()[0]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    colors = [ORANGE if v > 11 else BLUE for v in df.late_pct]
    bars = ax.barh(df.customer_state, df.late_pct, color=colors, height=0.68)
    for b, (_, r) in zip(bars, df.iterrows()):
        ax.text(b.get_width() + 0.25, b.get_y() + b.get_height() / 2,
                f"{r.late_pct:.1f}%  (n={int(r.n):,})", va="center", fontsize=7, color=INK2,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.6), zorder=3)
    ax.axvline(overall, color=INK2, lw=1, ls="--", zorder=1)
    ax.text(overall + 0.2, -0.9, f"all Brazil {overall:.1f}%", fontsize=7.5, color=INK2)
    ax.set_xlim(0, 27)
    ax.set_xlabel("% of delivered orders that arrived after the promised date")
    ax.tick_params(axis="y", labelsize=7.5)
    ax.grid(axis="y", visible=False)
    fig.savefig(FIG / "fig4_late_by_state.png")
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    fig1_rolling_orders(conn)
    fig2_review_by_delay(conn)
    fig3_monthly_late_and_review(conn)
    fig4_late_by_state(conn)
    print("Charts written to", FIG)


if __name__ == "__main__":
    main()
