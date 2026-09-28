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
    """June & Zoey（普通运营）全额提点率 (X: 万美金)"""
    if x <= 0:
        return 0.0
    elif x <= 8:
        return 0.0
    elif x <= 20:
        return 0.001
    elif x <= 30:
        return 0.0015
    else:
        # X > 30 万美金可申请转高级运营，目前按最高阶 0.15% 计算
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

# ----------------- 主界面 -----------------
st.title("📊 HomeDepot (THD) 平台提成独立数据看板")

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

    # 数据解析与计算
    records_valerie = []
    records_june = []
    records_zoey = []
    
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

        # 固定回款为销售额的 80%
        total_usd = total_sales_usd * 0.80        # 实际回款美金
        total_x = total_sales_wan * 0.80          # 回款万美金
        
        # 拆分各自回款
        valerie_x = total_x * valerie_share
        valerie_usd = total_usd * valerie_share
        
        june_x = total_x * june_share
        june_usd = total_usd * june_share
        
        zoey_x = total_x * zoey_share
        zoey_usd = total_usd * zoey_share
        
        # 获取提点率
        orig_rate = get_senior_op_rate(total_x)
        valerie_rate = get_senior_op_rate(valerie_x)
        june_rate = get_junior_op_rate(june_x)
        zoey_rate = get_junior_op_rate(zoey_x)
        
        # 计算提成
        orig_comm = total_usd * orig_rate
        valerie_comm = valerie_usd * valerie_rate
        june_comm = june_usd * june_rate
        zoey_comm = zoey_usd * zoey_rate
        
        # 差额计算（Valerie）
        diff_usd = valerie_comm - orig_comm
        diff_rmb = diff_usd * exchange_rate
        
        # 1. Valerie 记录
        records_valerie.append({
            "年月": ym,
            "平台总销售额(万美金)": total_sales_wan,
            "平台总回款(80%)(万美金)": total_x,
            "原模式提点": f"{orig_rate*100:.2f}%",
            "原模式提成($)": orig_comm,
            "拆分后回款(万美金)": valerie_x,
            "拆分后提点": f"{valerie_rate*100:.2f}%",
            "拆分后提成($)": valerie_comm,
            "差额损益($)": diff_usd,
            "差额损益(￥)": diff_rmb
        })
        
        # 2. June 记录
        records_june.append({
            "年月": ym,
            "June回款(万美金)": june_x,
            "June回款($)": june_usd,
            "提点": f"{june_rate*100:.2f}%",
            "提成($)": june_comm,
            "提成(￥)": june_comm * exchange_rate
        })
        
        # 3. Zoey 记录
        records_zoey.append({
            "年月": ym,
            "Zoey回款(万美金)": zoey_x,
            "Zoey回款($)": zoey_usd,
            "提点": f"{zoey_rate*100:.2f}%",
            "提成($)": zoey_comm,
            "提成(￥)": zoey_comm * exchange_rate
        })

    df_valerie = pd.DataFrame(records_valerie)
    df_june = pd.DataFrame(records_june)
    df_zoey = pd.DataFrame(records_zoey)

    # ----------------- Tab 选项卡分开展示看板 -----------------
    tab_v, tab_j, tab_z = st.tabs(["👤 Valerie 提成对比看板", "👤 June 提成看板", "👤 Zoey 提成看板"])

    # Valerie 独立看板
    with tab_v:
        st.subheader("Valerie (高级运营) 拆分前后提成损益明细表")
        st.dataframe(
            df_valerie.style.format({
                "平台总销售额(万美金)": "{:.2f}",
                "平台总回款(80%)(万美金)": "{:.2f}",
                "拆分后回款(万美金)": "{:.2f}",
                "原模式提成(\()": "\){:,.2f}",
                "拆分后提成(\()": "\){:,.2f}",
                "差额损益(\()": "\){:,.2f}",
                "差额损益(￥)": "￥{:,.2f}"
            }).map(
                lambda v: 'color: red; font-weight: bold;' if isinstance(v, (int, float)) and v < 0 else '',
                subset=["差额损益($)", "差额损益(￥)"]
            ),
            use_container_width=True
        )

    # June 独立看板
    with tab_j:
        st.subheader("June (普通运营) 提成明细表")
        st.dataframe(
            df_june.style.format({
                "June回款(万美金)": "{:.2f}",
                "June回款(\()": "\){:,.2f}",
                "提成(\()": "\){:,.2f}",
                "提成(￥)": "￥{:,.2f}"
            }),
            use_container_width=True
        )

    # Zoey 独立看板
    with tab_z:
        st.subheader("Zoey (普通运营) 提成明细表")
        st.dataframe(
            df_zoey.style.format({
                "Zoey回款(万美金)": "{:.2f}",
                "Zoey回款(\()": "\){:,.2f}",
                "提成(\()": "\){:,.2f}",
                "提成(￥)": "￥{:,.2f}"
            }),
            use_container_width=True
        )

else:
    st.info("👈 请在左侧侧边栏上传数据表（Excel 或 CSV）。")
