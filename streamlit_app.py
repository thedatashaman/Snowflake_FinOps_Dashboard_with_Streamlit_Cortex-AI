import streamlit as st
import pandas as pd
from datetime import date, timedelta
from snowflake.snowpark.context import get_active_session

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Snowflake Usage & Cost Dashboard",
    layout="wide"
)

session = get_active_session()

APP_DB = "FINOPS"
APP_SCHEMA = "SNOWFLAKE_USAGE"
DEFAULT_DAYS = 30

# =====================================================
# HELPERS
# =====================================================
def run_df(sql: str) -> pd.DataFrame:
    return session.sql(sql).to_pandas()

def where_date(col: str, start: date, end: date) -> str:
    return f"{col} BETWEEN '{start}' AND '{end}'"

def dim_filter(col: str, value: str) -> str:
    if value == "(All)":
        return "1=1"
    safe_val = value.replace("'", "''")
    return f"{col} = '{safe_val}'"

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("Filters")

today = date.today()
start_date, end_date = st.sidebar.date_input(
    "Date Range",
    value=(today - timedelta(days=DEFAULT_DAYS), today)
)

credit_price = st.sidebar.number_input(
    "Cost per Credit ($)",
    value=3.00,
    step=0.25
)

discount_pct = st.sidebar.slider("Discount %", 0, 100, 0)
discount_mult = 1 - (discount_pct / 100)

warehouse_df = run_df(f"""
    SELECT DISTINCT WAREHOUSE_NAME
    FROM {APP_DB}.{APP_SCHEMA}.DAILY_WAREHOUSE_METERING
    ORDER BY 1
""")

warehouse_list = ["(All)"] + warehouse_df["WAREHOUSE_NAME"].dropna().tolist()
warehouse = st.sidebar.selectbox("Warehouse", warehouse_list)

# =====================================================
# HEADER
# =====================================================
st.title("Snowflake Usage & Cost Dashboard")
st.caption("Snowflake ACCOUNT_USAGE FinOps dashboard (Streamlit + Cortex AI)")

tabs = st.tabs([
    "Summary",
    "Warehouse Usage",
    "Query Performance",
    "Storage",
    "AI Insights",
    "Cortex Chat"
])

# =====================================================
# SUMMARY TAB
# =====================================================
with tabs[0]:
    st.subheader("Summary")

    sql_summary = f"""
        SELECT
            USAGE_DATE,
            SUM(CREDITS_USED_TOTAL) AS TOTAL_CREDITS
        FROM {APP_DB}.{APP_SCHEMA}.DAILY_WAREHOUSE_METERING
        WHERE {where_date("USAGE_DATE", start_date, end_date)}
          AND {dim_filter("WAREHOUSE_NAME", warehouse)}
        GROUP BY USAGE_DATE
        ORDER BY USAGE_DATE
    """

    df = run_df(sql_summary)

    if df.empty:
        st.warning("No data available.")
    else:
        df["DAILY_COST"] = df["TOTAL_CREDITS"] * credit_price
        df["CUM_COST"] = df["DAILY_COST"].cumsum()
        df = df.set_index("USAGE_DATE")

        total_credits = df["TOTAL_CREDITS"].sum()
        total_cost = total_credits * credit_price

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Credits Used", f"{total_credits:,.2f}")
        c2.metric("Total Cost ($)", f"{total_cost:,.2f}")
        c3.metric("Discounted Cost ($)", f"{total_cost * discount_mult:,.2f}")
        c4.metric("Days", len(df))

        st.divider()
        st.write("### Daily Cost ($)")
        st.bar_chart(df[["DAILY_COST"]])

        st.write("### Cumulative Cost ($)")
        st.line_chart(df[["CUM_COST"]])

# =====================================================
# WAREHOUSE USAGE TAB
# =====================================================
with tabs[1]:
    st.subheader("Warehouse Usage")

    sql_wh = f"""
        SELECT
            WAREHOUSE_NAME,
            SUM(CREDITS_USED_TOTAL) AS CREDITS
        FROM {APP_DB}.{APP_SCHEMA}.DAILY_WAREHOUSE_METERING
        WHERE {where_date("USAGE_DATE", start_date, end_date)}
        GROUP BY WAREHOUSE_NAME
        ORDER BY CREDITS DESC
    """

    wh = run_df(sql_wh)

    if not wh.empty:
        wh["EST_COST"] = wh["CREDITS"] * credit_price
        wh = wh.set_index("WAREHOUSE_NAME")

        st.write("### Cost by Warehouse")
        st.bar_chart(wh[["EST_COST"]])

        st.write("### Warehouse Cost Table")
        st.dataframe(wh, use_container_width=True)

# =====================================================
# QUERY PERFORMANCE TAB
# =====================================================
with tabs[2]:
    st.subheader("Query Performance")

    sql_q = f"""
        SELECT
            USAGE_DATE,
            SUM(QUERY_COUNT) AS QUERIES,
            SUM(TOTAL_ELAPSED_MS) / 60000 AS ELAPSED_MIN
        FROM {APP_DB}.{APP_SCHEMA}.DAILY_QUERY_METRICS
        WHERE {where_date("USAGE_DATE", start_date, end_date)}
          AND {dim_filter("WAREHOUSE_NAME", warehouse)}
        GROUP BY USAGE_DATE
        ORDER BY USAGE_DATE
    """

    q = run_df(sql_q)

    if not q.empty:
        q = q.set_index("USAGE_DATE")

        total_queries = q["QUERIES"].sum()
        total_elapsed = q["ELAPSED_MIN"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Queries", f"{int(total_queries):,}")
        c2.metric("Elapsed Time (Min)", f"{total_elapsed:,.2f}")
        c3.metric(
            "Avg Query Time (Sec)",
            f"{(total_elapsed * 60 / total_queries):,.2f}" if total_queries else "0"
        )

        st.write("### Queries per Day")
        st.line_chart(q[["QUERIES"]])

        st.write("### Elapsed Time per Day (min)")
        st.line_chart(q[["ELAPSED_MIN"]])

# =====================================================
# STORAGE TAB
# =====================================================
with tabs[3]:
    st.subheader("Storage")

    sql_s = f"""
        SELECT
            USAGE_DATE,
            SUM(EST_STORAGE_GB) AS STORAGE_GB
        FROM {APP_DB}.{APP_SCHEMA}.DAILY_STORAGE
        WHERE {where_date("USAGE_DATE", start_date, end_date)}
        GROUP BY USAGE_DATE
        ORDER BY USAGE_DATE
    """

    s = run_df(sql_s)

    if not s.empty:
        s = s.set_index("USAGE_DATE")
        st.write("### Storage Growth (GB)")
        st.area_chart(s)

# =====================================================
# AI INSIGHTS TAB (EXECUTIVE SUMMARY)
# =====================================================
with tabs[4]:
    st.subheader("Cortex AI Insights")

    model = "mistral-large2"

    top_wh = run_df(f"""
        SELECT
            WAREHOUSE_NAME,
            SUM(CREDITS_USED_TOTAL) AS CREDITS
        FROM {APP_DB}.{APP_SCHEMA}.DAILY_WAREHOUSE_METERING
        WHERE {where_date("USAGE_DATE", start_date, end_date)}
        GROUP BY WAREHOUSE_NAME
        ORDER BY CREDITS DESC
        LIMIT 5
    """)

    prompt_text = (
        "You are a Snowflake FinOps expert advising engineering leadership.\n\n"
        f"Cost per credit: ${credit_price}\n"
        f"Date range: {start_date} to {end_date}\n\n"
        "Top warehouses by credit usage:\n"
        f"{top_wh.to_csv(index=False)}\n\n"
        "Provide:\n"
        "1. Executive summary\n"
        "2. Key cost drivers\n"
        "3. Any anomalies or spikes\n"
        "4. Optimization recommendations\n"
        "5. Concrete warehouse-level actions\n"
    )

    if st.button("Generate AI Insights"):
        with st.spinner("Cortex AI analyzing usage..."):
            safe_prompt = prompt_text.replace("'", "''")

            cortex_sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
              '{model}',
              '{safe_prompt}'
            ) AS RESPONSE
            """
            try:
                response = session.sql(cortex_sql).collect()[0]["RESPONSE"]
                st.markdown(response)
            except Exception as e:
                st.error(f"Cortex error: {e}")

# =====================================================
# CORTEX CHAT TAB (CHATGPT-LIKE UI)
# =====================================================
with tabs[5]:
    st.subheader("Cortex Chat – Ask Anything About Usage")

    model = "mistral-large2"

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # --- Chat history container (scrollable area) ---
    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # --- Chat input (MUST be last) ---
    user_question = st.chat_input(
        "Ask a question about Snowflake usage, cost, or optimization"
    )

    if user_question:
        # Show user message
        st.session_state.chat_history.append(
            {"role": "user", "content": user_question}
        )

        with chat_container:
            with st.chat_message("user"):
                st.write(user_question)

        # Context for Cortex
        top_wh = run_df(f"""
            SELECT
                WAREHOUSE_NAME,
                SUM(CREDITS_USED_TOTAL) AS CREDITS
            FROM {APP_DB}.{APP_SCHEMA}.DAILY_WAREHOUSE_METERING
            WHERE {where_date("USAGE_DATE", start_date, end_date)}
            GROUP BY WAREHOUSE_NAME
            ORDER BY CREDITS DESC
            LIMIT 5
        """)

        chat_prompt = (
            "You are a Snowflake FinOps expert helping an engineer.\n\n"
            f"Date range: {start_date} to {end_date}\n"
            f"Cost per credit: ${credit_price}\n"
            f"Selected warehouse: {warehouse}\n\n"
            "Top warehouses by credits:\n"
            f"{top_wh.to_csv(index=False)}\n\n"
            "User question:\n"
            f"{user_question}\n\n"
            "Respond clearly with actionable recommendations."
        )

        safe_prompt = chat_prompt.replace("'", "''")

        cortex_sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
          '{model}',
          '{safe_prompt}'
        ) AS RESPONSE
        """

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        answer = session.sql(cortex_sql).collect()[0]["RESPONSE"]
                        st.write(answer)

                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": answer}
                        )
                    except Exception as e:
                        st.error(f"Cortex error: {e}")

