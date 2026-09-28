import streamlit as st
import pandas as pd

st.set_page_config(page_title="THD 提成测算看板", layout="wide")

# ----------------- 提点规则定义 -----------------
def get_senior_op_rate(x):
    """高级运营全额提点率 (X: 万美金)"""
    if x <= 10:
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

def get_leader_rate(x):
    """组长全额提点率 (X: 万美金)"""
    if x <= 15:
        return 0.0
    elif x <= 50:
        return 0.004
    elif x <= 75:
        return 0.005
    elif x <= 100:
        return 0.006
    elif x <= 150:
        return 0.007
    else:
        return 0.008

# ----------------- 侧边栏设置 -----------------
st.sidebar.header("⚙️ 参数配置")

uploaded_file = st.sidebar.file_uploader("上传数据表 (Excel 或 CSV)", type=["xlsx", "xls", "csv"])

st.sidebar.subheader("SKU 占比设置 (%)")
my_share = st.sidebar.number_input("我的 SKU 占比", value=60.0, step=1.0) / 100.0
june_share = st.sidebar.number_input("June 的 SKU 占比", value=28.0, step=1.0) / 100.0
zoey_share = st.sidebar.number_input("Zoey 的 SKU 占比", value=12.0, step=1.0) / 100.0

st.sidebar.subheader("方案 C 参数")
override_rate = st.sidebar.number_input("团队管理提点 (%)", value=0.10, step=0.01) / 100.0

# ----------------- 主界面看板 -----------------
st.title("📊 HomeDepot (THD) 平台提成多维度数据看板")

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_input = pd.read_csv(uploaded_file)
        else:
            df_input = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"文件读取失败，请检查文件格式: {e}")
        st.stop()
        
    required_cols = ["年月", "销售额", "回款金额", "回款占比"]
    if not all(col in df_input.columns for col in required_cols):
        st.error(f"上传表头缺失！需包含以下字段：{required_cols}")
        st.stop()

    # 计算核心逻辑
    records = []
    for _, row in df_input.iterrows():
        ym = str(row["年月"])
        sales = float(row["销售额"])
        total_x = float(row["回款金额"]) # 万美金
        
        # 拆分个人及成员回款 (万美金)
        my_x = total_x * my_share
        june_x = total_x * june_share
        zoey_x = total_x * zoey_share
        
        # 提点率获取
        orig_rate = get_senior_op_rate(total_x)
        plan_a_rate = get_senior_op_rate(my_x)
        plan_b_rate = get_leader_rate(total_x)
        
        # 提成计算 (美金)
        orig_comm = total_x * orig_rate * 10000
        plan_a_comm = my_x * plan_a_rate * 10000
        plan_b_comm = total_x * plan_b_rate * 10000
        plan_c_comm = (my_x * plan_a_rate + total_x * override_rate) * 10000
        
        diff_a = plan_a_comm - orig_comm
        diff_b = plan_b_comm - orig_comm
        diff_c = plan_c_comm - orig_comm
        
        records.append({
            "年月": ym,
            "平台总回款(万美金)": total_x,
            "个人回款(万美金)": my_x,
            "原模式(全盘高运)": orig_comm,
            "方案A(拆分后个人高运)": plan_a_comm,
            "方案A损益": diff_a,
            "方案B(正式组长)": plan_b_comm,
            "方案B损益": diff_b,
            "方案C(个人高运+团队津贴)": plan_c_comm,
            "方案C损益": diff_c
        })
        
    df_res = pd.DataFrame(records)
    
    # 顶部 KPI 指标看板
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("累计平台总回款", f"${df_res['平台总回款(万美金)'].sum():,.2f} 万")
    kpi2.metric("原模式累计提成", f"${df_res['原模式(全盘高运)'].sum():,.2f}")
    kpi3.metric("方案A累计提成", f"\({df_res['方案A(拆分后个人高运)'].sum():,.2f}", f"\){df_res['方案A损益'].sum():,.2f}")
    kpi4.metric("方案B累计提成", f"\({df_res['方案B(正式组长)'].sum():,.2f}", f"\){df_res['方案B损益'].sum():,.2f}")
    
    st.markdown("---")
    
    # 趋势对比图表
    st.subheader("📈 提成趋势对比图")
    chart_data = df_res.set_index("年月")[["原模式(全盘高运)", "方案A(拆分后个人高运)", "方案B(正式组长)", "方案C(个人高运+团队津贴)"]]
    st.line_chart(chart_data)
    
    # 损益柱状图
    st.subheader("📊 各方案对比原模式的月度损益")
    diff_data = df_res.set_index("年月")[["方案A损益", "方案B损益", "方案C损益"]]
    st.bar_chart(diff_data)
    
    # 详细数据表格
    st.subheader("📋 明细数据对比表")
    
    formatted_df = df_res.copy()
    currency_cols = [
        "原模式(全盘高运)", "方案A(拆分后个人高运)", "方案A损益", 
        "方案B(正式组长)", "方案B损益", "方案C(个人高运+团队津贴)", "方案C损益"
    ]
    
    st.dataframe(
        formatted_df.style.format({
            "平台总回款(万美金)": "{:.2f}",
            "个人回款(万美金)": "{:.2f}",
            **{col: "${:,.2f}" for col in currency_cols}
        }).map(
            lambda v: 'color: red; font-weight: bold;' if isinstance(v, (int, float)) and v < 0 else '',
            subset=["方案A损益", "方案B损益", "方案C损益"]
        ),
        use_container_width=True
    )

else:
    st.info("👈 请在左侧侧边栏上传数据表（Excel 或 CSV）以查看看板。")
