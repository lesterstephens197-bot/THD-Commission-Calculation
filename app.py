import streamlit as st
import pandas as pd

st.set_page_config(page_title="THD平台提成差异计算与分析", layout="wide")

st.title("📊 HomeDepot (THD) 平台提成计算与差异对比工具")
st.markdown("""
本工具用于分析 **单人负责全盘 SKU** vs **拆分 SKU 给团队运营** 后的提成差异，帮助评估试用期及正式组长方案的合理性。
""")

# ----------------- 提点规则定义 -----------------
def get_senior_op_rate(x):
    """高级运营全额提点率"""
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
    """组长全额提点率"""
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

# ----------------- 侧边栏参数设置 -----------------
st.sidebar.header("⚙️ 参数配置")

total_sales = st.sidebar.number_input(
    "THD 平台月度总回款金额 (万美金)", 
    min_value=0.0, 
    value=100.0, 
    step=5.0
)

st.sidebar.subheader("SKU 销售额占比分配")
my_share = st.sidebar.slider("我的 SKU 占比 (%)", 0, 100, 60) / 100.0
june_share = st.sidebar.slider("June 的 SKU 占比 (%)", 0, 100, 28) / 100.0
zoey_share = st.sidebar.slider("Zoey 的 SKU 占比 (%)", 0, 100, 12) / 100.0

# 校验占比总和
total_share = my_share + june_share + zoey_share
if round(total_share, 2) != 1.0:
    st.sidebar.warning(f"⚠️ 当前占比总和为 {total_share*100:.1f}%，建议调整为 100%")

# 各自业绩计算
my_sales = total_sales * my_share
june_sales = total_sales * june_share
zoey_sales = total_sales * zoey_share

# ----------------- 计算逻辑 -----------------
# 1. 拆分前：原模式（全盘按高级运营提成）
orig_rate = get_senior_op_rate(total_sales)
orig_commission = total_sales * orig_rate * 10000  # 转为美金

# 2. 方案 A：直接按拆分后个人 SKU 计算（高级运营提点，无管理溢价/团队提成） - 容易亏损的方案
plan_a_rate = get_senior_op_rate(my_sales)
plan_a_commission = my_sales * plan_a_rate * 10000

# 3. 方案 B：正式组长模式（拿团队总回款的组长提点）
plan_b_rate = get_leader_rate(total_sales)
plan_b_commission = total_sales * plan_b_rate * 10000

# 4. 方案 C：过渡建议方案（个人SKU拿高级运营提点 + 团队整体拿管理提成）
# 假设管理提成点数为 0.1% ~ 0.2%
override_rate = st.sidebar.slider("方案C：团队提成管理点数 (%)", 0.0, 0.5, 0.1, 0.05) / 100.0
plan_c_commission = (my_sales * plan_a_rate + total_sales * override_rate) * 10000

# ----------------- 数据展示 -----------------
st.subheader("📌 业绩与提成对比结果")

col1, col2, col3, col4 = st.columns(4)
col1.metric("THD 平台总回款", f"${total_sales:.1f} 万")
col2.metric("我的个人 SKU 回款", f"${my_sales:.1f} 万")
col3.metric(" June 回款", f"${june_sales:.1f} 万")
col4.metric(" Zoey 回款", f"${zoey_sales:.1f} 万")

st.markdown("---")

# 提成对比表格
comparison_data = [
    {
        "方案说明": "【原模式】全盘独占 (拿全盘高级运营提点)",
        "业绩计算基数": f"全盘 ${total_sales:.1f} 万",
        "适用提点率": f"{orig_rate*100:.2f}%",
        "预计提成收入 ($)": round(orig_commission, 2),
        "对比原模式差额 ($)": 0.0
    },
    {
        "方案说明": "【现状/公司打算】拆分SKU (仅拿个人SKU高级运营提点)",
        "业绩计算基数": f"个人SKU ${my_sales:.1f} 万",
        "适用提点率": f"{plan_a_rate*100:.2f}%",
        "预计提成收入 ($)": round(plan_a_commission, 2),
        "对比原模式差额 ($)": round(plan_a_commission - orig_commission, 2)
    },
    {
        "方案说明": "【正式组长】全盘团队提成 (拿全盘组长提点)",
        "业绩计算基数": f"全盘 ${total_sales:.1f} 万",
        "适用提点率": f"{plan_b_rate*100:.2f}%",
        "预计提成收入 ($)": round(plan_b_commission, 2),
        "对比原模式差额 ($)": round(plan_b_commission - orig_commission, 2)
    },
    {
        "方案说明": "【谈判过渡方案C】个人SKU提点 + 团队总额管理津贴",
        "业绩计算基数": f"个人 \({my_sales:.1f}万 + 全盘\){total_sales:.1f}万",
        "适用提点率": f"个人 {plan_a_rate*100:.2f}% + 管理 {override_rate*100:.2f}%",
        "预计提成收入 ($)": round(plan_c_commission, 2),
        "对比原模式差额 ($)": round(plan_c_commission - orig_commission, 2)
    }
]

df_res = pd.DataFrame(comparison_data)

# 高亮显示亏损
st.dataframe(
    df_res.style.map(
        lambda v: 'color: red; font-weight: bold;' if isinstance(v, float) and v < 0 else '', 
        subset=['对比原模式差额 ($)']
    ), 
    use_container_width=True
)

# ----------------- 损失深度分析 -----------------
diff_loss = orig_commission - plan_a_commission
st.error(f"⚠️ **风险警示**：如果直接按照“拆分后个人SKU”套用高级运营提点，在当前回款规模下，你每月将直接亏损 **${diff_loss:,.2f} 美金**！")

st.markdown("""
### 💡 为什么会亏损？（双重拉低效应）
1. **基数变小**：你的业绩计算基数从 \(100\%\) 降到了 \(60\%\)。
2. **阶梯掉级**：在**全额提点**机制下，拆分后你的销售额掉到了更低的提点区间。
   * 例如：全盘回款 $100$ 万美金对应提点 **0.5%**（提成 \$5,000 美金）。
   * 拆分后你的 SKU 回款为 $60$ 万美金，落在 \(40<X≤60\) 梯队，提点降为 **0.35%**（提成 \$2,100 美金）。
   * 结果：你的业绩虽然是原来的 60%，但提成却只剩下了原来的 **42%**！
""")

st.markdown("---")

st.subheader("🤝 向主管谈判/沟通的建议切入点")
st.markdown("""
试用期只给“高级运营”提点可以理解，但**绩效计算基数不应直接缩水**，否则相当于“升职/带团队反而变相降薪”。建议提出以下三种谈判方案之一：

1. **方案一（推荐）：试用期采用“业绩保底/不低于原独占提成”**
   * 在试用期 3 个月内，按照“个人 SKU 高级运营提点”计算，但如果低于“按全盘计算的原提成”，补齐差额。
2. **方案二：试用期个人 SKU 提成 + 团队基础管理提成**
   * 个人 60% 的 SKU 拿高级运营提点，另外 40% 分出去的 SKU 抽取一定的管理重叠点数（如 0.1%~0.2%），作为带教 June 和 Zoey 的管理报酬。
3. **方案三：争取提前按“组长”提点计算**
   * 既然已经开始承担组长职责（分派 SKU、带人、对全盘负责），要求试用期直接按**组长全额提点表**去套用全盘 $100$ 万美金的提点（\(0.6\%\) 或 \(0.7\%\)）。
""")
