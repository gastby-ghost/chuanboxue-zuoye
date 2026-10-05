#!/usr/bin/env python3
"""研究设计的分析流水线 —— 《研究设计.md》第八节与《预注册与分析.md》的可运行实现。

用法
    # 没有真实数据时，先跑通整条流水线（生成一份模拟数据并全流程自检）
    python3 tools/analysis_pipeline.py --simulate

    # 有真实数据后（列名见《测量工具.md》「计分表」）
    python3 tools/analysis_pipeline.py --data data/clean.csv

依赖
    python3 -m pip install numpy pandas scipy statsmodels

约定
    group        0 = 对照（平台原始评论流）／1 = AI 搜索
    主要结局      perceived_gap（感知极化）
    次要结局      perceived_bias、affect_out（情感极化）、willingness、incivility（表达对立化）

设计原则（与预注册一致）
    1. H1／H2 报效应量与其 95% CI，不做 p 值单点判断；
    2. H2 是「无效／反向」型假设，零假设检验的不显著**不能**支持它，
       因此额外跑等效检验（TOST）与贝叶斯因子；
    3. H3c 用并行中介的 bootstrap（5000 次）间接效应与对比；
    4. 缺失以完整案例为主；多重插补（SPSS 步骤见《预注册与分析.md》）作敏感性分析。
"""
import argparse
import os
import sys
from datetime import date

import numpy as np
import pandas as pd
from scipy import stats

try:
    import statsmodels.api as sm
except ImportError:
    sys.exit("缺少依赖：请先运行  python3 -m pip install numpy pandas scipy statsmodels")

SEED = 20260924
N_BOOT = 5000
SESOI_D = 0.20          # H2 等效边界：预注册的小效应界
ALPHA = 0.05

# 变量列名（与《测量工具.md》计分表一致）
ITEMS_WILLING = ["E_1", "E_2", "E_3"]
NEEDED = ["group", "perceived_gap", "affect_out", "willingness", "incivility"]


# --------------------------------------------------------------------------
# 基础统计工具
# --------------------------------------------------------------------------
def cohen_d(x, y):
    """Cohen's d：x 相对 y 的标准化均值差（正 = x 更大）。"""
    n1, n2 = len(x), len(y)
    sp = np.sqrt(((n1 - 1) * np.var(x, ddof=1) + (n2 - 1) * np.var(y, ddof=1)) / (n1 + n2 - 2))
    return (np.mean(x) - np.mean(y)) / sp


def welch(x, y):
    """Welch t 检验，返回 (t, p, df, se)。"""
    t, p = stats.ttest_ind(x, y, equal_var=False)
    n1, n2 = len(x), len(y)
    s1, s2 = np.var(x, ddof=1), np.var(y, ddof=1)
    se = np.sqrt(s1 / n1 + s2 / n2)
    df = (s1 / n1 + s2 / n2) ** 2 / ((s1 / n1) ** 2 / (n1 - 1) + (s2 / n2) ** 2 / (n2 - 1))
    return float(t), float(p), float(df), float(se)


def boot_ci(func, x, y, n_boot=N_BOOT, seed=SEED, alpha=ALPHA):
    """对任意两样本统计量做百分位 bootstrap 置信区间。"""
    rng = np.random.default_rng(seed)
    n1, n2 = len(x), len(y)
    out = np.empty(n_boot)
    for i in range(n_boot):
        out[i] = func(rng.choice(x, n1, replace=True), rng.choice(y, n2, replace=True))
    lo, hi = np.percentile(out, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def tost(x, y, bound):
    """等效检验（TOST，Welch 版）。

    H0: |mu_x - mu_y| >= bound ；  H1: |mu_x - mu_y| < bound
    bound 为原始单位。返回 (diff, p_lower, p_upper, p_tost)。
    """
    diff = float(np.mean(x) - np.mean(y))
    _, _, df, se = welch(x, y)
    t_lower = (diff + bound) / se          # H0: diff <= -bound
    t_upper = (diff - bound) / se          # H0: diff >=  bound
    p_lower = 1 - stats.t.cdf(t_lower, df)
    p_upper = stats.t.cdf(t_upper, df)
    return diff, float(p_lower), float(p_upper), float(max(p_lower, p_upper))


def bayes_factor_t(x, y):
    """独立样本 t 检验的贝叶斯因子 BF10（BIC 近似，Wagenmakers 2007）。

    仅为「无效应」提供一条旁证：BF10 < 1/3 支持 H0，BF10 > 3 支持 H1。
    正式报告建议改用 JASP／BayesFactor 包。
    """
    n = len(x) + len(y)
    t, _, df, _ = welch(x, y)
    delta_bic = -n * np.log(1 + t ** 2 / df) + np.log(n)   # BIC1 − BIC0
    return float(np.exp(-delta_bic / 2))


def bh_q(pvals):
    """Benjamini-Hochberg 的 q 值。"""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    ranked = p[order] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    q = np.empty(m)
    q[order] = np.clip(ranked, 0, 1)
    return q


def paired_d_diff_ci(data, var1, var2, group="group", n_boot=N_BOOT, seed=SEED):
    """配对 bootstrap：检验两个结局的标准化组间效应量之差 d1 − d2。

    两结局测自同一被试，故按被试重抽（而非各自独立求 CI），
    既利用了两者的相关，也是 H2「方向分离」的可检验落点。
    """
    d = data[[group, var1, var2]].dropna().reset_index(drop=True)

    def stat(dd):
        a, b = dd[dd[group] == 1], dd[dd[group] == 0]
        return (cohen_d(a[var1].values, b[var1].values)
                - cohen_d(a[var2].values, b[var2].values))

    rng = np.random.default_rng(seed)
    n = len(d)
    boots = np.array([stat(d.iloc[rng.integers(0, n, n)]) for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(stat(d)), float(lo), float(hi)


def tost_n_per_group(bound_d, alpha=ALPHA, power=0.80):
    """两组等效检验（TOST）所需的每组样本量，真实差为 0。"""
    z_a = stats.norm.ppf(1 - alpha)
    z_b = stats.norm.ppf(power)
    return int(np.ceil(2 * (z_a + z_b) ** 2 / bound_d ** 2))


def cronbach_alpha(frame):
    """Cronbach's α。"""
    d = frame.dropna()
    k = d.shape[1]
    if k < 2:
        return float("nan")
    return float(k / (k - 1) * (1 - d.var(axis=0, ddof=1).sum() / d.sum(axis=1).var(ddof=1)))


# --------------------------------------------------------------------------
# 计分：把原始题项合成为变量
# --------------------------------------------------------------------------
def score(df, actual=None):
    """按《测量工具.md》计分表合成变量。

    actual：该议题的**真实分布基准**（由第一步内容分析编码给出），
    形如 {"gap": 1.8, "pct_sup": 0.42, "pct_opp": 0.38}。
    缺省时 perceived_bias 记为缺失（不参与主分析）。
    """
    df = df.copy()
    if {"P_sup", "P_opp"} <= set(df.columns):
        df["perceived_gap"] = (df["P_sup"] - df["P_opp"]).abs()
    if {"P_pct_sup", "P_pct_opp"} <= set(df.columns):
        df["perceived_pct_opp"] = df["P_pct_opp"]
    if {"P_pct_neutral"} <= set(df.columns):
        df["perceived_pct_sum"] = df[["P_pct_sup", "P_pct_opp", "P_pct_neutral"]].sum(axis=1)
    if {"A_thermo_sup", "A_thermo_opp"} <= set(df.columns):
        df["affect_thermo_gap"] = (df["A_thermo_sup"] - df["A_thermo_opp"]).abs()
    if {"A_dislike"} <= set(df.columns):
        df["affect_out"] = df["A_dislike"]
    if set(ITEMS_WILLING) <= set(df.columns):
        df["willingness"] = df[ITEMS_WILLING].mean(axis=1)
    if {"C_conflict"} <= set(df.columns):
        df["incivility"] = df["C_conflict"]
    if actual:
        if "perceived_gap" in df.columns:
            df["perceived_bias"] = df["perceived_gap"] - actual.get("gap", np.nan)
        if {"P_pct_opp"} <= set(df.columns) and "pct_opp" in actual:
            df["pct_bias_opp"] = df["P_pct_opp"] / 100.0 - actual["pct_opp"]
    return df


# --------------------------------------------------------------------------
# 模拟数据（没有真实数据时用于自检流水线）
# --------------------------------------------------------------------------
def simulate(n_per_group=75, seed=SEED):
    rng = np.random.default_rng(seed)
    rows = []
    for group in (0, 1):
        for _ in range(n_per_group):
            stance = rng.integers(1, 8)                     # 自我立场 1-7
            strength = abs(stance - 4)                      # 立场强度
            # 感知极化：AI 组略低（H1，d≈0.45）
            gap = np.clip(rng.normal(3.2 - 0.45 * group, 1.05), 0, 6)
            sup = np.clip(4 + gap / 2 + rng.normal(0, .3), 1, 7)
            opp = np.clip(4 - gap / 2 + rng.normal(0, .3), 1, 7)
            # 情感极化：两组几乎无差（H2）
            dislike = np.clip(rng.normal(46 + 0.6 * strength, 17), 0, 100)
            # 意见表达：感知极化越高，意愿越低、对立化越高（H3a/H3b）
            willing = np.clip(rng.normal(5.0 - 0.35 * gap + 0.10 * strength, 0.9), 1, 7)
            will_items = [int(np.clip(round(willing + rng.normal(0, .5)), 1, 7)) for _ in range(3)]
            conflict = int(np.clip(round(rng.normal(0.9 + 0.30 * gap - 0.05 * strength, 0.9)), 0, 4))
            rows.append({
                "id": len(rows) + 1, "group": group,
                "P_self": int(stance), "P_sup": round(float(sup), 2), "P_opp": round(float(opp), 2),
                "P_pct_sup": int(np.clip(rng.normal(38 + gap * 5, 12), 0, 100)),
                "P_pct_opp": int(np.clip(rng.normal(34 + gap * 5, 12), 0, 100)),
                "P_pct_neutral": int(np.clip(rng.normal(28, 10), 0, 100)),
                "A_thermo_sup": int(np.clip(rng.normal(72, 18), 0, 100)),
                "A_thermo_opp": int(np.clip(rng.normal(58 - 0.5 * strength, 18), 0, 100)),
                "A_dislike": round(float(dislike), 1),
                "A_family": int(np.clip(round(rng.normal(3.2 + .15 * strength, 1.3)), 1, 7)),
                "E_1": will_items[0], "E_2": will_items[1], "E_3": will_items[2],
                "C_written": int(rng.random() < 0.72),
                "C_len": int(np.clip(rng.normal(60, 40), 0, 400)),
                "C_conflict": conflict,
                "M_source": int(1 if group == 1 else 2) if rng.random() < .8 else 3,
                "M_multi": int(np.clip(round(rng.normal(5.6 if group else 3.4, 1.2)), 1, 7)),
                "age": int(np.clip(rng.normal(26, 6), 18, 60)),
                "gender": int(rng.integers(1, 3)),
                "edu": int(np.clip(rng.integers(2, 6), 1, 6)),
                "weibo_freq": int(np.clip(rng.normal(4.2, 1.5), 1, 7)),
                "issue_involve": int(np.clip(round(rng.normal(4.5, 1.3)), 1, 7)),
                "stance_strength": int(strength),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 并行中介（bootstrap）
# --------------------------------------------------------------------------
def parallel_mediation(data, y, m1="perceived_gap", m2="affect_out", x="group",
                       n_boot=N_BOOT, seed=SEED, covars=None):
    """X → (M1, M2) → Y 的并行中介；返回点估计与 bootstrap 分布。"""
    cols = [x, m1, m2, y] + list(covars or [])
    d = data[cols].dropna().reset_index(drop=True)

    def est(dd):
        base = dd[[x] + list(covars or [])]
        a1 = sm.OLS(dd[m1], sm.add_constant(base)).fit().params[x]
        a2 = sm.OLS(dd[m2], sm.add_constant(base)).fit().params[x]
        fit = sm.OLS(dd[y], sm.add_constant(dd[[x, m1, m2] + list(covars or [])])).fit()
        b1, b2 = fit.params[m1], fit.params[m2]
        return np.array([a1, a2, b1, b2, fit.params[x], a1 * b1, a2 * b2, a1 * b1 - a2 * b2])

    point = est(d)
    rng = np.random.default_rng(seed)
    n = len(d)
    boots = np.empty((n_boot, 8))
    for i in range(n_boot):
        boots[i] = est(d.iloc[rng.integers(0, n, n)])
    return point, boots


def report_mediation(name, point, boots):
    labels = ["a1 (X→M1 感知极化)", "a2 (X→M2 情感极化)", "b1 (M1→Y)", "b2 (M2→Y)",
              "c' (X→Y 直接)", "间接 X→M1→Y", "间接 X→M2→Y", "间接差 (M1−M2)"]
    lines = [f"  ── 并行中介（{name}）──"]
    for i, lab in enumerate(labels):
        lo, hi = np.percentile(boots[:, i], [2.5, 97.5])
        flag = "*" if (lo > 0) == (hi > 0) else " "
        lines.append(f"    {lab:<24} = {point[i]:+7.3f}  95% CI [{lo:+.3f}, {hi:+.3f}] {flag}")
    return lines


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def run(df, out_lines):
    def say(s=""):
        print(s)
        out_lines.append(s)

    pvals = []
    df = df.dropna(subset=["group"] + [c for c in NEEDED if c in df.columns])
    ai = df[df["group"] == 1]
    ctrl = df[df["group"] == 0]

    say(f"有效样本：N = {len(df)}（AI 搜索 n = {len(ai)}，对照 n = {len(ctrl)}）")
    say(f"生成时间：{date.today().isoformat()}")
    say("")

    # 信度
    if set(ITEMS_WILLING) <= set(df.columns):
        say(f"[信度] 表达意愿量表 Cronbach's α = {cronbach_alpha(df[ITEMS_WILLING]):.3f}")
        say("")

    # 操纵检查
    if "M_multi" in df.columns:
        t, p, _, _ = welch(ai["M_multi"].values, ctrl["M_multi"].values)
        say(f"[操纵检查] 感知到多元整合：AI {ai['M_multi'].mean():.2f} vs 对照 "
            f"{ctrl['M_multi'].mean():.2f}，t = {t:.2f}, p = {p:.3f}")
    if "M_source" in df.columns:
        acc = (ai["M_source"] == 1).mean(), (ctrl["M_source"] == 2).mean()
        say(f"[操纵检查] 正确识别来源：AI 组 {acc[0]:.0%}，对照组 {acc[1]:.0%}")
    say("")

    # H1 / H2
    say("=" * 68)
    say("一、组间比较（H1 矫正路径 ／ H2 分化路径）")
    say("=" * 68)
    for var, label, hyp in [("perceived_gap", "感知极化", "H1"),
                            ("affect_out", "情感极化（对对立立场者的反感）", "H2"),
                            ("willingness", "意见表达意愿", "H3a 结局"),
                            ("incivility", "表达对立化程度", "H3b 结局")]:
        if var not in df.columns:
            continue
        x, y = ai[var].dropna().values, ctrl[var].dropna().values
        t, p, dfree, _ = welch(x, y)
        d = cohen_d(x, y)
        d_lo, d_hi = boot_ci(cohen_d, x, y)
        say(f"{var}（{label}）")
        say(f"  AI = {x.mean():.3f} (SD {x.std(ddof=1):.3f}) ／ 对照 = {y.mean():.3f} (SD {y.std(ddof=1):.3f})")
        say(f"  Welch t({dfree:.1f}) = {t:+.3f}, p = {p:.4f}   Cohen's d = {d:+.3f}  95% CI [{d_lo:+.3f}, {d_hi:+.3f}]")
        if hyp != "H1":
            pvals.append((f"组间 {var}", p))
        if hyp == "H2":                      # 无效／反向型假设：补等效检验与 BF
            bound = SESOI_D * np.sqrt((np.var(x, ddof=1) + np.var(y, ddof=1)) / 2)
            diff, p_lo, p_hi, p_tost = tost(x, y, bound)
            bf = bayes_factor_t(x, y)
            say(f"  等效检验 TOST（SESOI = d {SESOI_D}，原始界 ±{bound:.3f}）：diff = {diff:+.3f}, "
                f"p_TOST = {p_tost:.4f}  →  {'可判定为等效（未抬高）' if p_tost < ALPHA else '尚不能判定等效'}")
            say(f"     注：TOST 对 d {SESOI_D} 的等效边界需每组约 {tost_n_per_group(SESOI_D)} 人；"
                f"本样本不足以判定等效，故以「方向分离」为主检验。")
            say(f"  贝叶斯因子 BF10 ≈ {bf:.3f}（<1/3 支持 H0；>3 支持 H1，仅供参考，正式报告用 JASP）")
            dd, lo, hi = paired_d_diff_ci(df, "perceived_gap", var)
            star = "*" if hi < 0 or lo > 0 else " "
            say(f"  「方向分离」配对 bootstrap：d(感知极化) − d(情感极化) = {dd:+.3f}  "
                f"95% CI [{lo:+.3f}, {hi:+.3f}] {star}")
            say(f"     → CI 上界 {'< 0，支持两结局效应方向分离（H2）' if hi < 0 else '未小于 0，H2 未获支持'}")
        say("")

    # H3a / H3b：回归
    say("=" * 68)
    say("二、感知极化 → 意见表达（H3a 意愿 ／ H3b 对立化）")
    say("=" * 68)
    for y, lab in [("willingness", "表达意愿"), ("incivility", "对立化程度")]:
        if y not in df.columns:
            continue
        fit = sm.OLS(df[y], sm.add_constant(df[["perceived_gap"]])).fit()
        b = fit.params["perceived_gap"]
        ci = fit.conf_int().loc["perceived_gap"]
        say(f"{lab} ← 感知极化：b = {b:+.3f}, SE = {fit.bse['perceived_gap']:.3f}, "
            f"t = {fit.tvalues['perceived_gap']:+.2f}, p = {fit.pvalues['perceived_gap']:.4f}, "
            f"95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
        pvals.append((f"{y} ← 感知极化", float(fit.pvalues["perceived_gap"])))
    say("  （H3a 预期为负、H3b 预期为正；此为模型中的 b 路径）")
    say("")

    # H3c：并行中介
    say("=" * 68)
    say("三、并行中介（H3c）：AI 搜索 →（感知极化, 情感极化）→ 意见表达")
    say("=" * 68)
    covars = [c for c in ["stance_strength", "issue_involve", "weibo_freq", "edu"] if c in df.columns]
    for y, lab in [("willingness", "表达意愿"), ("incivility", "对立化程度")]:
        if y not in df.columns:
            continue
        point, boots = parallel_mediation(df, y, covars=covars)
        for line in report_mediation(lab, point, boots):
            say(line)
        say(f"    （协变量：{', '.join(covars) if covars else '无'}；bootstrap {N_BOOT} 次）")
        say("")

    say("=" * 68)
    say("四、多重比较（Benjamini-Hochberg FDR）")
    say("=" * 68)
    if pvals:
        qs = bh_q([p for _, p in pvals])
        for (name, p), q in zip(pvals, qs):
            say(f"  {name:<28} p = {p:.4f}   q = {q:.4f}")
    say("  主要结局为 perceived_gap（感知极化），按预注册单项检验、不作校正；")
    say("  上表为次要结局的 FDR 参考值。校正不改变效应量与 CI 的解读。")
    say("")


def main():
    ap = argparse.ArgumentParser(description="研究设计分析流水线")
    ap.add_argument("--data", help="真实数据 CSV（列名见《测量工具.md》计分表）")
    ap.add_argument("--simulate", action="store_true", help="生成模拟数据并自检")
    ap.add_argument("--n", type=int, default=75, help="模拟数据每组人数（默认 75）")
    ap.add_argument("--outdir", default="outputs", help="报告输出目录")
    ap.add_argument("--data-dir", default="data", help="模拟数据输出目录")
    args = ap.parse_args()

    if args.data:
        df = pd.read_csv(args.data, encoding="utf-8-sig")
        df = score(df)
        src = args.data
    else:
        df = score(simulate(args.n))
        src = "模拟数据"
        os.makedirs(args.data_dir, exist_ok=True)
        path = os.path.join(args.data_dir, "simulated.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"已生成模拟数据：{path}")

    out_lines = [f"分析报告 —— 数据来源：{src}"]
    print("\n" + "=" * 68)
    run(df, out_lines)

    os.makedirs(args.outdir, exist_ok=True)
    path = os.path.join(args.outdir, f"report-{date.today().isoformat()}.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out_lines) + "\n")
    print(f"报告已保存：{path}")


if __name__ == "__main__":
    main()
