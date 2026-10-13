"""Builds reports/Olist_WBR_Report_SattarGnanaSaiRam.pdf from the query results and figures.

Layout follows a plain Word-style report: Times (Liberation Serif) body text, black numbered
headings, grid tables with captions above, figure captions below.
"""
import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
RES = HERE / "query_results"
OUT = HERE / "Olist_WBR_Report_SattarGnanaSaiRam.pdf"
REPO_URL = ""  # put the GitHub link here and rebuild, e.g. "https://github.com/user/olist-wbr"

# Liberation Serif = metric-compatible Times New Roman; fall back to reportlab's built-in Times
LIB = Path("/usr/share/fonts/truetype/liberation")
if (LIB / "LiberationSerif-Regular.ttf").exists():
    for name, f in [("TNR", "Regular"), ("TNR-B", "Bold"), ("TNR-I", "Italic"), ("TNR-BI", "BoldItalic")]:
        pdfmetrics.registerFont(TTFont(name, str(LIB / f"LiberationSerif-{f}.ttf")))
    registerFontFamily("TNR", normal="TNR", bold="TNR-B", italic="TNR-I", boldItalic="TNR-BI")
    F, FB, FI = "TNR", "TNR-B", "TNR-I"
else:
    F, FB, FI = "Times-Roman", "Times-Bold", "Times-Italic"

BLACK = colors.black
body = ParagraphStyle("body", fontName=F, fontSize=10, leading=12.3, alignment=TA_JUSTIFY, spaceAfter=4)
h1 = ParagraphStyle("h1", fontName=FB, fontSize=12, leading=14.5, spaceBefore=6, spaceAfter=3, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName=FB, fontSize=10.5, leading=13, spaceBefore=4, spaceAfter=2, keepWithNext=1)
cap = ParagraphStyle("cap", fontName=FI, fontSize=9.5, leading=11.5, alignment=TA_CENTER, spaceBefore=2, spaceAfter=7)
tcap = ParagraphStyle("tcap", parent=cap, spaceBefore=3, spaceAfter=3)
cell = ParagraphStyle("cell", fontName=F, fontSize=8.8, leading=10.2)
cellb = ParagraphStyle("cellb", parent=cell, fontName=FB)
note = ParagraphStyle("note", parent=body, fontSize=9.5, leading=12)
bul = ParagraphStyle("bul", parent=body, leftIndent=14, bulletIndent=4, spaceAfter=2.5, bulletFontName=F)


def P(t, s=body):
    return Paragraph(t, s)


def B(t, style=bul):
    return Paragraph(t, style, bulletText="•")


def grid_table(rows, widths, right_cols=()):
    data = [[Paragraph(c, cellb if i == 0 else cell) if isinstance(c, str) else c for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="CENTER", repeatRows=1)
    st = [("FONT", (0, 0), (-1, -1), F, 8.8), ("GRID", (0, 0), (-1, -1), 0.5, BLACK),
          ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7e6e6")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    t.setStyle(TableStyle(st))
    return t


def fig(name, width_mm, caption):
    im = Image(str(FIG / name))
    r = im.imageHeight / im.imageWidth
    im.drawWidth, im.drawHeight = width_mm * mm, width_mm * mm * r
    return KeepTogether([im, P(caption, cap)])


def read(name):
    with open(RES / f"{name}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont(F, 9.5)
    canvas.drawCentredString(A4[0] / 2, 11 * mm, str(doc.page))
    canvas.restoreState()


def build():
    s = []
    W = A4[0] - 40 * mm

    # ---------------- student details ----------------
    det = Table([
        [P("<b>Name</b>", body), P(": Sattar Gnana Sai Ram", body)],
        [P("<b>Roll No</b>", body), P(": 48", body)],
        [P("<b>Reg No</b>", body), P(": 127003233", body)],
        [P("<b>Section</b>", body), P(": D", body)],
    ], colWidths=[22 * mm, 100 * mm], hAlign="LEFT")
    det.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), -1.5)]))
    s += [det, Spacer(1, 4), HRFlowable(width="100%", thickness=0.8, color=BLACK, spaceAfter=8)]
    s.append(P("Big Data in Industry: Take-Home Assignment 1",
               ParagraphStyle("t0", fontName=F, fontSize=11, leading=14, alignment=TA_CENTER)))
    s.append(P("Weekly Business Review for an E-commerce Marketplace (Olist)",
               ParagraphStyle("t1", fontName=FB, fontSize=14.5, leading=18, alignment=TA_CENTER, spaceAfter=2)))
    if REPO_URL:
        s.append(P(f"GitHub repository: {REPO_URL}",
                   ParagraphStyle("t2", fontName=FI, fontSize=10, leading=13, alignment=TA_CENTER, spaceAfter=6)))
    else:
        s.append(Spacer(1, 6))

    # ---------------- 1 ----------------
    s.append(P("1. Introduction", h1))
    s.append(P(
        "For this assignment I used the Olist Brazilian E-Commerce dataset, which has 99,441 real orders placed between "
        "September 2016 and October 2018. I loaded it into a SQLite database and built a pipeline with three layers: "
        "<b>raw</b> tables that are an exact copy of the CSV files, <b>staging</b> tables where data types are fixed and bad rows "
        "are handled, and a final table called <b>mart_orders</b> that has one row per order with the order value, delivery "
        "dates, delay and review score. I chose SQLite because it does not need a server, so the whole project can be run from "
        "the README in about 15 seconds. The SQL only uses CTEs and window functions, so it could be moved to Postgres or "
        "BigQuery later without much change."))

    # ---------------- 2 ----------------
    s.append(P("2. Part A: Ingestion Pipeline", h1))
    s.append(P("The pipeline is started with <i>python -m pipeline.run_pipeline</i> and runs the following steps in order:"))
    for t in [
        "<b>Validate:</b> before anything is written, the script checks that all 9 CSV files exist and that each one has the "
        "columns listed in <i>pipeline/config.py</i>.",
        "<b>Load raw:</b> every CSV is read as text and written to a <i>raw_</i> table. Each load also adds a row to "
        "<i>etl_load_audit</i> with the file name, MD5 hash, row count and time.",
        "<b>Staging:</b> seven SQL files cast the types, clean text, remove duplicates and apply the fixes described in Part B.",
        "<b>Quality gate and mart:</b> checks 01 to 07 run on the staging tables. Only if they pass is <i>mart_orders</i> built, "
        "and check 08 then confirms the mart still has exactly one row per order.",
    ]:
        s.append(B(t))
    s.append(P(
        "<b>Idempotency.</b> Each raw table is first loaded into a temporary table and then swapped in with DROP and RENAME "
        "inside one transaction. Every staging and mart script also begins with DROP TABLE IF EXISTS. To test this I ran the "
        "pipeline twice in a row: raw_orders stayed at 99,441 rows, mart_orders at 99,441, mart_order_items at 112,650, and "
        "the total order value was R$ 15,848,243.14 both times. Only the audit table grows, by 9 rows per run."))
    s.append(P(
        "<b>Logging and failure handling.</b> Each step writes its row count and time to the console and to a log file in "
        "<i>logs/</i>. I tested three failures on purpose. Removing the payments CSV stopped the run with the message "
        "\"missing file: data/raw/olist_order_payments_dataset.csv\". Deleting the estimated delivery date column stopped it "
        "with \"expected column(s) not found\". Changing one delivery date to 2010 made check 02 fail, which raised the "
        "data-quality alarm and the mart was not rebuilt."))
    s.append(P(
        "<b>Bonus (Airflow).</b> The file <i>dags/olist_daily_dag.py</i> runs the same steps as four tasks scheduled "
        "<i>@daily</i>. I tested it on Airflow 3.1.8 with <i>airflow dags test</i> and all four tasks finished successfully."))

    # ---------------- 3 ----------------
    s.append(P("3. Part B: Data Quality Checks", h1))
    s.append(P(
        "Each check is a separate SQL file that returns the number of failing rows. I first ran the same logic on the raw "
        "tables to see how big each problem was, and then ran the checks again on the cleaned tables with a limit. A limit of "
        "0% means the problem must be completely fixed. A small limit is only used for known issues that I chose to flag, so "
        "the alarm will still go off if they suddenly increase."))
    rows = [["Check", "Failing rows (raw)", "After cleaning (limit)", "How it was handled and why"],
            ["01. Null or duplicate order_id", "0", "0 (0%)", "No problem found. Kept as a blocking check because a duplicate order would double the revenue."],
            ["02. Delivered date before purchase date", "0", "0 (0%)", "No problem found. Blocking check."],
            ["03. Payment total not equal to price + freight (more than 1 cent)", "432 orders", "432 (1%)",
             "<b>Flagged.</b> 291 of these orders paid more than the item total and 261 of them were paid in instalments "
             "(average 5.9 vs 2.9 normally), so the difference looks like instalment interest rather than an error. "
             "Revenue is calculated from items, so it is not affected."],
            ["04. Order with no matching customer", "0", "0 (0%)", "No problem found. Blocking, since an order without a customer cannot be linked to a state."],
            ["05. More than one review per order (own)", "547 orders", "0 (0%)",
             "<b>Fixed.</b> Kept only the latest review, since that is the customer's final opinion. Otherwise these orders would be counted twice in average ratings."],
            ["06. Carrier date outside the purchase-to-delivery window (own)", "189 orders", "0 (0%)",
             "<b>Fixed.</b> Set the carrier date to NULL (166 before purchase, 23 after delivery). The scan is clearly wrong but the rest of the order is valid, so the order was kept."],
            ["07. Status is delivered but no delivery date (own)", "8 orders", "8 (0.1%)",
             "<b>Flagged</b> and excluded from delivery-time calculations."],
            ["08. mart_orders has exactly one row per order (own)", "n/a", "0 (0%)",
             "Protects against duplicate rows from joins. Items, payments and reviews are grouped to order level before joining."]]
    s.append(P("Table 1: Data quality checks and results", tcap))
    s.append(grid_table(rows, [W * 0.27, W * 0.13, W * 0.13, W * 0.47]))
    s.append(Spacer(1, 5))
    s.append(P("I also noticed 775 orders with no items (almost all cancelled or unavailable, so they are left out of revenue), "
               "610 products with no category (labelled 'unknown' so their sales are still counted) and 768 orders with no review."))

    # ---------------- 4 ----------------
    s.append(P("4. Part C: SQL Analysis", h1))
    s.append(P("All five queries are saved in <i>sql/analysis/</i>. In all of them, revenue means item price plus freight for "
               "orders that were not cancelled or unavailable."))

    s.append(P("4.1 Month-over-month revenue and growth", h2))
    q1 = [r for r in read("q1_mom_revenue_growth") if "2017-01" <= r["purchase_month"] <= "2018-08"]

    def fmt(r):
        g = r["mom_growth_pct"]
        return [r["purchase_month"], f'{int(r["orders"]):,}', f'{float(r["revenue"]):,.0f}',
                "-" if g == "" else f'{float(g):+.1f}%']
    hdr = ["Month", "Orders", "Revenue (R$)", "Growth"]
    combo = [hdr + hdr] + [fmt(a) + fmt(b) for a, b in zip(q1[:10], q1[10:])]
    cw = [W * 0.115, W * 0.095, W * 0.15, W * 0.14]
    t = grid_table(combo, cw + cw)
    t.setStyle(TableStyle([("LINEAFTER", (3, 0), (3, -1), 1.5, BLACK)]))
    s.append(P("Table 2: Monthly revenue, January 2017 to August 2018", tcap))
    s.append(t)
    s.append(Spacer(1, 5))
    s.append(P(
        "Revenue grew from R$ 137k in January 2017 to between R$ 0.98M and R$ 1.16M per month in 2018. The largest jump was "
        "November 2017 (+53.4%) because of Black Friday, followed by a 26.5% drop in December. From March 2018 onwards revenue "
        "stays almost flat, which is the same period when delivery problems were at their worst (Section 5). I did not show "
        "growth for September and December 2016 or September 2018 because those months only have one or two orders, and the "
        "LAG result for January 2017 came out as +697,879%, which is meaningless."))

    s.append(P("4.2 Top 3 product categories per state", h2))
    q2 = read("q2_top3_categories_per_state")
    r2 = [["State", "Rank 1", "Rank 2", "Rank 3"]]
    for st in ["SP", "RJ", "MG", "RS", "PR", "BA"]:
        cats = [x for x in q2 if x["customer_state"] == st][:3]
        r2.append([st] + [f'{c["category"]} ({float(c["revenue"])/1000:,.0f}k)' for c in cats])
    s.append(P("Table 3: Top 3 categories by revenue in the six largest states (R$)", tcap))
    s.append(grid_table(r2, [W * 0.1, W * 0.3, W * 0.3, W * 0.3]))
    s.append(Spacer(1, 5))
    s.append(P("The query uses DENSE_RANK so that categories with equal revenue share a rank. The full result has 81 rows "
               "(27 states x 3). health_beauty is in the top 3 in 25 of the 27 states and is first in 15 of them, while "
               "watches_gifts appears in 20 states. The southern states are slightly different: in RS furniture_decor is "
               "second, and in PR sports_leisure is first."))

    s.append(P("4.3 7-day rolling average of daily orders", h2))
    s.append(P(
        "I first created a full calendar with a recursive CTE so that days with zero orders are still included, and then "
        "used AVG() OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW). The rolling average rises from about 57 orders per day "
        "at the end of January 2017 to about 219 at the end of January 2018. The highest value is 494 on 29 November 2017, in "
        "the Black Friday week, and 24 November alone had 1,176 orders. There is also a clear dip to about 124 at the end of "
        "May 2018, which matches the truckers' strike in Brazil that month."))
    s.append(fig("fig1_rolling_orders.png", 128, "Figure 1: Daily orders and 7-day rolling average, January 2017 to August 2018"))

    s.append(P("4.4 Repeat-purchase rate", h2))
    s.append(P(
        "The dataset documentation explains that <i>customer_id</i> is created new for every order, so if it is used to identify "
        "customers the repeat rate comes out as 0.00%. The column that identifies the same person across orders is "
        "<i>customer_unique_id</i>. Using it, <b>2,887 out of 94,983 customers (3.04%)</b> placed more than one successful order, "
        "and the highest number of orders by one customer is 16. This means almost all customers only buy once, so their first "
        "order is very important."))

    s.append(P("4.5 Delivery delay and review score", h2))
    q5 = read("q5_delivery_delay_vs_review")
    r5 = [["Delivered compared to promised date", "Orders", "Share", "Avg delay (days)", "Avg review", "1-2 star reviews"]]
    for r in q5:
        lab = "<b>All delivered orders</b>" if r["delay_bucket"].startswith("ALL") else r["delay_bucket"][3:].capitalize()
        r5.append([lab, f'{int(r["orders"]):,}', f'{float(r["pct_of_orders"]):.1f}%', f'{float(r["avg_delay_days"]):+.1f}',
                   f'{float(r["avg_review"]):.2f}', f'{float(r["pct_1_2_star"]):.1f}%'])
    s.append(P("Table 4: Review score by delivery delay", tcap))
    s.append(grid_table(r5, [W * 0.3, W * 0.12, W * 0.12, W * 0.15, W * 0.13, W * 0.18]))
    s.append(Spacer(1, 5))
    s.append(P(
        "On average orders arrive <b>11.9 days before</b> the estimated date, so Olist's estimates are quite generous. The small "
        "group of late orders behaves very differently though. Being only 1 to 3 days late already brings the average rating "
        "down from above 4.0 to 3.29, and when an order is more than a week late about 4 out of 5 customers give 1 or 2 stars. "
        "The drop is sudden rather than gradual, which suggests customers mainly judge whether the promised date was kept."))

    # ---------------- 5 ----------------
    s.append(P("5. Part D: Metrics and Findings", h1))
    s.append(P("All metrics are calculated weekly from mart_orders using <i>sql/metrics/weekly_kpis.sql</i>. Table 5 shows the "
               "values for January 2017 to August 2018, and for March 2018 (the worst month) for comparison."))
    m = [["Metric", "Formula", "Why it matters", "Jan 2017 to Aug 2018", "Mar 2018"],
         ["<b>North Star:</b> Happy delivered orders per week",
          "Count of orders where status = delivered, delivered date &lt;= estimated date and review score &gt;= 4",
          "It only increases if we sell more and also keep customers happy, so it combines growth and satisfaction.",
          "73,734 (74.4% of orders)", "63.2% of orders"],
         ["GMV (supporting)", "Sum of price + freight for orders that are not cancelled or unavailable",
          "Total value sold on the marketplace. Olist's commission is a share of this.", "R$ 15.69M", "R$ 1.15M"],
         ["On-time delivery rate (supporting)", "Orders delivered on or before the estimated date / delivered orders",
          "The biggest driver of review scores found in Part C.", "93.2%", "81.0%"],
         ["1-2 star review rate (guardrail)", "Reviews with score &lt;= 2 / all reviews",
          "Warns us if growth is coming at the cost of bad customer experiences.", "14.6%", "22.8%"],
         ["Cancellation rate (guardrail)", "Cancelled or unavailable orders / all orders",
          "Shows sellers listing stock they do not have. A cancelled order is usually a lost customer.", "1.19%", "0.60%"]]
    s.append(P("Table 5: North Star and supporting metrics", tcap))
    s.append(grid_table(m, [W * 0.18, W * 0.27, W * 0.29, W * 0.14, W * 0.12]))
    s.append(Spacer(1, 5))
    s.append(P("The repeat-purchase rate (3.04%) is tracked monthly instead of weekly because it changes slowly. One limitation "
               "is that reviews usually come in one to two weeks after delivery, so the last two weeks of the North Star "
               "will always be incomplete in the weekly review."))
    s.append(fig("fig2_review_by_delay.png", 120, "Figure 2: Average review score by how early or late the order was delivered"))
    s.append(fig("fig3_monthly_late_and_review.png", 128,
                 "Figure 3: Monthly share of late deliveries (top) and average review score (bottom)"))
    s.append(fig("fig4_late_by_state.png", 122,
                 "Figure 4: Late-delivery rate by customer state (states with at least 300 delivered orders)"))
    s.append(P(
        "Figure 3 shows the pattern most clearly. Late deliveries rose to 12% in November 2017 and to 14% and 19% in February and "
        "March 2018, and the average rating fell in exactly the same months, reaching 3.81. Once deliveries were back on time in "
        "April, the rating recovered. Figure 4 shows that the problem is concentrated in a few states: AL, MA, SE, PI, CE, BA, "
        "RJ and PA all have late rates above 11%."))

    # ---------------- 6: memo ----------------
    s.append(PageBreak())
    s.append(P("6. Memo to the Vice President", h1))
    s.append(Spacer(1, 2))
    s.append(P("MEMORANDUM", ParagraphStyle("mt", fontName=FB, fontSize=13, leading=16, spaceAfter=6)))
    mh = Table([
        [P("<b>To:</b>"), P("Vice President, Marketplace Operations")],
        [P("<b>From:</b>"), P("Sattar Gnana Sai Ram, Data Analyst")],
        [P("<b>Date:</b>"), P("12 October 2026")],
        [P("<b>Subject:</b>"), P("Late deliveries are the main cause of bad reviews")],
    ], colWidths=[22 * mm, W - 22 * mm], hAlign="LEFT")
    mh.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), -3)]))
    s += [mh, Spacer(1, 3), HRFlowable(width="100%", thickness=0.8, color=BLACK, spaceAfter=8)]

    s.append(P("<b>Key finding</b>", h2))
    s.append(P(
        "Most customer dissatisfaction on Olist comes from delivery, not from the products. Orders that arrived after the "
        "promised date, or never arrived at all, make up only <b>9.3% of reviewed orders but 43% of all 1-2 star reviews</b> "
        "(6,204 out of 14,494). A late order gets an average rating of <b>2.27</b>, compared with <b>4.29</b> for an order that "
        "arrives on time, and 62% of late orders receive a 1 or 2 star review."))
    s.append(P("<b>Evidence</b>", h2))
    for t in [
        "<b>The problem comes in bursts.</b> In a normal month 3-7% of orders arrive late. This rose to 12% during Black Friday "
        "2017 and to 14-19% in February and March 2018. In the worst week (starting 26 February 2018) the share of 1-2 star "
        "reviews reached 28.5%, about double the usual level. When deliveries improved in April, ratings went back up (Figure 3).",
        "<b>It is concentrated in 8 states.</b> AL, MA, SE, PI, CE, BA, RJ and PA receive 20% of our deliveries but account for "
        "38% of late ones. In the peak months their late rate was <b>28.1%</b>, compared with 9.7% in the rest of Brazil (Figure 4).",
        "<b>Most of the delay happens in transit.</b> Late orders spent 27.9 days with the carrier on average, compared with "
        "8.0 days for on-time orders. Sellers were also slower to hand over late orders (6.1 days vs 3.0), and 28% of them "
        "missed the shipping deadline compared with 8% of on-time orders.",
        "<b>Customers rarely return.</b> Only 3% of customers ever buy a second time, so for most people the first order is "
        "their whole experience of Olist.",
    ]:
        s.append(B(t))
    s.append(P("<b>Recommendation</b>", h2))
    s.append(P(
        "Before the next Black Friday, set up an <b>automatic delivery-risk alert for the 8 high-risk states</b>, using the daily "
        "pipeline that is now in place. When the 7-day late rate for one of these states goes above 10%, two things should "
        "happen automatically for that state. First, the delivery date shown at checkout is extended by 5 days for new orders, "
        "so we stop making promises we cannot keep. Second, customers whose orders are already on the way receive a message "
        "with the updated date. A longer promise should not hurt much, because we currently deliver almost 12 days early on "
        "average, and Figure 2 shows customers are satisfied as long as the date is met."))
    s.append(P("<b>Expected impact and how to measure it</b>", h2))
    s.append(P(
        "If the late rate in these 8 states had been kept at 10% instead of 28% during the four peak months, about 990 fewer "
        "orders would have been late and roughly 525 fewer 1-2 star reviews would have been written. I suggest testing the "
        "customer message as an A/B test, with half of the at-risk orders receiving it, so its effect can be measured separately "
        "from the longer delivery promise. The target for Black Friday 2018 would be an on-time rate above 90% in these states "
        "and a 1-2 star rate below 15%, without a drop in checkout conversion. It would also be worth asking the logistics team "
        "what happened in February and March 2018, because the dataset does not include the carrier name, so I can see that "
        "the transit stage broke down but not why."))

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=16 * mm, bottomMargin=17 * mm,
                            title="Big Data in Industry - Take-Home Assignment 1", author="Sattar Gnana Sai Ram")
    doc.build(s, onFirstPage=page_number, onLaterPages=page_number)
    print("written", OUT)


if __name__ == "__main__":
    build()
