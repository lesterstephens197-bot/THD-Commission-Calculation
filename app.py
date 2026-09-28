import streamlit as st
import pandas as pd

st.set_page_config(page_title="THD 提成测算看板", layout="wide")

# ----------------- 提点规则定义 -----------------
def get_senior_op_rate(x):
    """Valerie（高级运营）全额提点率 (X: 万美金)"""
    if x <= 0:
        return 0.0
    elif x <= 10:
        return 0.0
    elif x <= 40:
        return 0.003
    elif x <= 60:
        return 0.0035
    elif x <= 80:
        return 0.004
    elif x <= 150:
        return 0.005
    else:
        return 0.008

def get_junior_op_rate(x):
    """June & Zoey（初级运营）全额提点率 (X: 万美金)"""
    if x <= 0:
        return 0.0
    elif x <= 8:
        return 0.0
    elif x <= 20:
        return 0.001
    elif x <= 30:
        return 0.0015
    else:
        return 0.0015

# ----------------- 侧边栏设置 -----------------
st.sidebar.header("⚙️ 参数配置")

uploaded_file = st.sidebar.file_uploader("上传数据表 (Excel 或 CSV)", type=["xlsx", "xls", "csv"])

st.sidebar.subheader("SKU 占比设置 (%)")
valerie_share = st.sidebar.number_input("Valerie 的 SKU 占比", value=60.0, step=1.0) / 100.0
june_share = st.sidebar.number_input("June 的 SKU 占比", value=28.0, step=1.0) / 100.0
zoey_share = st.sidebar.number_input("Zoey 的 SKU 占比", value=12.0, step=1.0) / 100.0

st.sidebar.subheader("汇率设置")
exchange_rate = st.sidebar.number_input("美元兑人民币汇率", value=6.70, step=0.01)

# ----------------- 主界面看板 -----------------
st.title("📊 HomeDepot (THD) 平台运营提成看板")

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_input = pd.read_csv(uploaded_file)
        else:
            df_input = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"文件读取失败，请检查文件格式或依赖环境: {e}")[cite: 2]
        st.stop()
        
    required_cols = ["年月", "销售额", "回款金额", "回款占比"]
    if not all(col in df_input.columns for col in required_cols):
        st.error(f"上传表头缺失！需包含以下字段：{required_cols}")
        st.stop()

    # 计算核心逻辑
    total_records = []
    valerie_records = []
    junior_records = []
    
    for _, row in df_input.iterrows():
        ym = str(row["年月"])
        raw_sales = float(row["销售额"])
        
        # 自动识别销售额单位
        if raw_sales > 10000:
            total_sales_usd = raw_sales
            total_sales_wan = raw_sales / 10000.0
        else:
            total_sales_wan = raw_sales
            total_sales_usd = raw_sales * 10000.0

        # 回款金额固定按销售额的 80% 计算
        total_usd = total_sales_usd * 0.80
        total_x = total_sales_wan * 0.80
        payback_rate = 0.80
        
        # 各自回款（万美金与美金）
        valerie_x = total_x * valerie_share
        valerie_usd = total_usd * valerie_share
        
        june_x = total_x * june_share
        june_usd = total_usd * june_share
        
        zoey_x = total_x * zoey_share
        zoey_usd = total_usd * zoey_share
        
        # 提点率获取
        orig_rate = get_senior_op_rate(total_x)
        valerie_rate = get_senior_op_rate(valerie_x)
        june_rate = get_junior_op_rate(june_x)
        zoey_rate = get_junior_op_rate(zoey_x)
        
        # 提成计算（美金转人民币，并四舍五入取整）
        orig_comm_rmb = round(total_usd * orig_rate * exchange_rate)
        valerie_comm_rmb = round(valerie_usd * valerie_rate * exchange_rate)
        june_comm_rmb = round(june_usd * june_rate * exchange_rate)
        zoey_comm_rmb = round(zoey_usd * zoey_rate * exchange_rate)
        
        diff_rmb = valerie_comm_rmb - orig_comm_rmb
        
        # 1. 平台总数据看板记录（整数）
        total_records.append({
            "年月": ym,
            "平台总销售额(万美金)": round(total_sales_wan),
            "平台总回款(万美金)": round(total_x),
            "回款占比": f"{round(payback_rate*100)}%"
        })
        
        # 2. Valerie (高级运营) 看板记录（整数人民币）
        valerie_records.append({
            "年月": ym,
            "平台总回款(万美金)": round(total_x),
            "原模式提点": f"{orig_rate*100:.2f}%",
            "原模式提成(￥)": orig_comm_rmb,
            "Valerie回款(万美金)": round(valerie_x),
            "Valerie提点": f"{valerie_rate*100:.2f}%",
            "Valerie提成(￥)": valerie_comm_rmb,
            "差额损益(￥)": diff_rmb
        })
        
        # 3. June & Zoey (初级运营) 看板记录（整数人民币）
        junior_records.append({
            "年月": ym,
            "June回款(万美金)": round(june_x),
            "June提点": f"{june_rate*100:.2f}%",
            "June提成(￥)": june_comm_rmb,
            "Zoey回款(万美金)": round(zoey_x),
            "Zoey提点": f"{zoey_rate*100:.2f}%",
            "Zoey提成(￥)": zoey_comm_rmb
        })
        
    df_total = pd.DataFrame(total_records)
    df_valerie = pd.DataFrame(valerie_records)
    df_junior = pd.DataFrame(junior_records)
    
    # ----------------- 看板 1: 平台总体基础数据 -----------------
    st.subheader("🌐 1. 平台总体基础数据")
    st.dataframe(
        df_total.style.format({
            "平台总销售额(万美金)": "{:,.0f}",
            "平台总回款(万美金)": "{:,.0f}"
        }),
        use_container_width=True
    )

    st.markdown("---")

    # ----------------- 看板 2: Valerie (高级运营) -----------------
    st.subheader("📌 2. Valerie (高级运营) 提成对比明细表")
    valerie_rmb_cols = ["原模式提成(￥)", "Valerie提成(￥)", "差额损益(￥)"]
    
    st.dataframe(
        df_valerie.style.format({
            "平台总回款(万美金)": "{:,.0f}",
            "Valerie回款(万美金)": "{:,.0f}",
            **{col: "￥{:,.0f}" for col in valerie_rmb_cols}
        }).map(
            lambda v: 'color: red; font-weight: bold;' if isinstance(v, (int, float)) and v < 0 else '',
            subset=["差额损益(￥)"]
        ),
        use_container_width=True
    )

    st.markdown("---")

    # ----------------- 看板 3: June & Zoey (初级运营) -----------------
    st.subheader("📌 3. June & Zoey (初级运营) 提成明细表")
    junior_rmb_cols = ["June提成(￥)", "Zoey提成(￥)"]
    
    st.dataframe(
        df_junior.style.format({
            "June回款(万美金)": "{:,.0f}",
            "Zoey回款(万美金)": "{:,.0f}",
            **{col: "￥{:,.0f}" for col in junior_rmb_cols}
        }),
        use_container_width=True
    )

else:
    st.info("👈 请在左侧侧边栏上传数据表（Excel 或 CSV）。")
