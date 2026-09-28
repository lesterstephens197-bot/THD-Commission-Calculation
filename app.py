import streamlit as st
import pandas as pd

st.set_page_config(page_title="THD 提成测算看板", layout="wide")

# ----------------- 提点规则定义 -----------------
def get_senior_op_rate(x):
    """高级运营全额提点率 (X: 万美金)"""
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
st.title("📊 HomeDepot (THD) 平台提成对比明细表")

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_input = pd.read_csv(uploaded_file)
        else:
            df_input = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"文件读取失败，请检查文件格式或依赖环境: {e}")
        st.stop()
        
    required_cols = ["年月", "销售额", "回款金额", "回款占比"]
    if not all(col in df_input.columns for col in required_cols):
        st.error(f"上传表头缺失！需包含以下字段：{required_cols}")
        st.stop()

    # 计算核心逻辑
    records = []
    for _, row in df_input.iterrows():
        ym = str(row["年月"])
        raw_sales = float(row["销售额"])
        
        # 自动识别销售额单位（美金 vs 万美金）
        if raw_sales > 10000:
            total_sales_usd = raw_sales           # 实际美金
            total_sales_wan = raw_sales / 10000.0 # 万美金
        else:
            total_sales_wan = raw_sales           # 万美金
            total_sales_usd = raw_sales * 10000.0 # 实际美金

        # 回款金额固定按销售额的 80% 计算
        total_usd = total_sales_usd * 0.80        # 实际回款美金
        total_x = total_sales_wan * 0.80          # 回款万美金
        
        # 拆分个人回款 (Valerie)
        valerie_x = total_x * valerie_share       # 个人回款万美金
        valerie_usd = total_usd * valerie_share   # 个人回款美金
        
        # 获取对应阶梯提点率
        orig_rate = get_senior_op_rate(total_x)
        plan_a_rate = get_senior_op_rate(valerie_x)
        
        # 计算实际提成（美金）
        orig_comm = total_usd * orig_rate
        plan_a_comm = valerie_usd * plan_a_rate
        
        diff_usd = plan_a_comm - orig_comm
        diff_rmb = diff_usd * exchange_rate       # 换算成人民币 (RMB)
        
        records.append({
            "年月": ym,
            "平台总销售额(万美金)": total_sales_wan,
            "平台总回款(80%)(万美金)": total_x,
            "原模式提点": f"{orig_rate*100:.2f}%",
            "原模式提成($)": orig_comm,
            "拆分后Valerie回款(万美金)": valerie_x,
            "拆分后Valerie提点": f"{plan_a_rate*100:.2f}%",
            "拆分后Valerie提成($)": plan_a_comm,
            "差额损益($)": diff_usd,
            "差额损益(￥)": diff_rmb
        })
        
    df_res = pd.DataFrame(records)
    
    # 明细数据表格
    currency_usd_cols = ["原模式提成(\()", "拆分后Valerie提成(\))", "差额损益($)"]
    
    st.dataframe(
        df_res.style.format({
            "平台总销售额(万美金)": "{:.2f}",
            "平台总回款(80%)(万美金)": "{:.2f}",
            "拆分后Valerie回款(万美金)": "{:.2f}",
            **{col: "${:,.2f}" for col in currency_usd_cols},
            "差额损益(￥)": "￥{:,.2f}"
        }).map(
            lambda v: 'color: red; font-weight: bold;' if isinstance(v, (int, float)) and v < 0 else '',
            subset=["差额损益($)", "差额损益(￥)"]
        ),
        use_container_width=True
    )

else:
    st.info("👈 请在左侧侧边栏上传数据表（Excel 或 CSV）。")
