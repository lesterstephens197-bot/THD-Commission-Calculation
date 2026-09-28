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
my_share = st.sidebar.number_input("我的 SKU 占比", value=60.0, step=1.0) / 100.0
june_share = st.sidebar.number_input("June 的 SKU 占比", value=28.0, step=1.0) / 100.0
zoey_share = st.sidebar.number_input("Zoey 的 SKU 占比", value=12.0, step=1.0) / 100.0

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
        raw_x = float(row["回款金额"])
        
        # 自动识别单位：若数值大于 10000，判定用户填的是“美金”，自动转为“万美金”
        if raw_x > 10000:
            total_x = raw_x / 10000.0  # 万美金
        else:
            total_x = raw_x            # 万美金
            
        total_usd = total_x * 10000.0  # 实际美金
        
        # 拆分个人回款
        my_x = total_x * my_share      # 万美金
        my_usd = total_usd * my_share  # 实际美金
        
        # 获取对应阶梯提点率
        orig_rate = get_senior_op_rate(total_x)
        plan_a_rate = get_senior_op_rate(my_x)
        
        # 计算实际提成（美金）
        orig_comm = total_usd * orig_rate
        plan_a_comm = my_usd * plan_a_rate
        
        diff_a = plan_a_comm - orig_comm
        
        records.append({
            "年月": ym,
            "平台总回款(万美金)": total_x,
            "原模式提点": f"{orig_rate*100:.2f}%",
            "原模式提成": orig_comm,
            "拆分后个人回款(万美金)": my_x,
            "拆分后个人提点": f"{plan_a_rate*100:.2f}%",
            "拆分后个人提成": plan_a_comm,
            "差额(损益)": diff_a
        })
        
    df_res = pd.DataFrame(records)
    
    # 明细数据表格
    currency_cols = ["原模式提成", "拆分后个人提成", "差额(损益)"]
    
    st.dataframe(
        df_res.style.format({
            "平台总回款(万美金)": "{:.2f}",
            "拆分后个人回款(万美金)": "{:.2f}",
            **{col: "${:,.2f}" for col in currency_cols}
        }).map(
            lambda v: 'color: red; font-weight: bold;' if isinstance(v, (int, float)) and v < 0 else '',
            subset=["差额(损益)"]
        ),
        use_container_width=True
    )

else:
    st.info("👈 请在左侧侧边栏上传数据表（Excel 或 CSV）。")
