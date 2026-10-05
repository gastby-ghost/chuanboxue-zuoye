#!/usr/bin/env python3
"""生成小组展示／论文用的图，输出到 figures/。

用法
    python3 tools/make_figures.py

依赖
    python3 -m pip install numpy matplotlib

产出
    figures/fig2-理论推导链.png   理论与假设的推导结构
    figures/fig3-实验流程.png     被试旅程（招募→随机→两组→测量）
    figures/fig4-检验力.png       样本量与可检出效应（标注本设计的两个临界点）

说明：研究模型图沿用仓库根目录的 `模型图.png`（已定稿），本脚本不重复生成。
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = "Arial Unicode MS"
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc="#ffffff", ec="#222222", fs=11, bold=False, r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.005,rounding_size={r}",
                                linewidth=1.4, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=3, linespacing=1.5)


def arrow(ax, p1, p2, style="-|>", color="#222222", lw=1.4, rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=14,
                                 linewidth=lw, color=color, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls))


def blank(figsize):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


# -------------------------------------------------------------------------- 图 2
def fig2():
    fig, ax = blank((10.5, 5.6))
    ax.text(0.5, 0.955, "图 2　理论与假设的推导链", ha="center", fontsize=14, fontweight="bold")
    ax.text(0.5, 0.895, "主理论：多元无知（pluralistic ignorance）——感知极化是它的一个特例",
            ha="center", fontsize=11, color="#333333")

    # 第一层：命题
    box(ax, 0.06, 0.70, 0.26, 0.13, "P1　误判源于可见性", fs=10.5)
    box(ax, 0.37, 0.70, 0.26, 0.13, "P2　分布信息可校准判断", fs=10.5)
    box(ax, 0.68, 0.70, 0.26, 0.13, "P3　认知—行为缺口", fs=10.5, fc="#f0f0f0")

    # 第一次「能不能」
    box(ax, 0.06, 0.44, 0.57, 0.10, "第一次「能不能」：AI 搜索 → 纠正误判（认知层）",
        fs=11, bold=True, fc="#fafafa")
    box(ax, 0.68, 0.44, 0.26, 0.10, "第二次「能不能」（理论缺口）", fs=11, bold=True, fc="#f0f0f0")

    arrow(ax, (0.30, 0.70), (0.30, 0.545))
    arrow(ax, (0.50, 0.70), (0.50, 0.545))
    arrow(ax, (0.81, 0.70), (0.81, 0.545))

    # 假设
    box(ax, 0.06, 0.22, 0.175, 0.12, "H1　感知极化 ↓\n（−）", fs=10)
    box(ax, 0.255, 0.22, 0.175, 0.12, "H2　情感极化 ＝/＋\n（分化）", fs=10)
    box(ax, 0.45, 0.22, 0.18, 0.12, "RQ1 ／ RQ2", fs=10, fc="#fafafa")
    box(ax, 0.68, 0.19, 0.26, 0.18, "H3a 意愿 ↓\nH3b 对立化 ↑\nH3c 并行中介", fs=10, fc="#f0f0f0")

    arrow(ax, (0.145, 0.44), (0.145, 0.345))
    arrow(ax, (0.342, 0.44), (0.342, 0.345))
    arrow(ax, (0.53, 0.44), (0.53, 0.345))
    arrow(ax, (0.81, 0.44), (0.81, 0.375))

    ax.text(0.5, 0.085, "认知端可被校准，行为端不必然跟随——这正是本研究要冲的缺口",
            ha="center", fontsize=10.5, color="#333333", style="italic")
    fig.savefig(os.path.join(OUT, "fig2-理论推导链.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


# -------------------------------------------------------------------------- 图 3
def fig3():
    fig, ax = blank((11, 5.2))
    ax.text(0.5, 0.95, "图 3　实验流程（单因子被试间）", ha="center", fontsize=14, fontweight="bold")

    box(ax, 0.03, 0.62, 0.17, 0.15, "知情同意\n＋ 筛选 S1", fs=10)
    box(ax, 0.235, 0.62, 0.15, 0.15, "随机分组\n（1:1）", fs=10, bold=True)
    box(ax, 0.42, 0.795, 0.30, 0.115, "AI 搜索组：智搜多元观点整合（截图）", fs=9.5, fc="#fafafa")
    box(ax, 0.42, 0.60, 0.30, 0.115, "对照组：同议题原始评论流（截图）", fs=9.5)
    box(ax, 0.77, 0.62, 0.20, 0.15, "测量\nP → A → E/C\n→ M → D", fs=10)

    arrow(ax, (0.20, 0.695), (0.235, 0.695))
    arrow(ax, (0.385, 0.695), (0.42, 0.852))
    arrow(ax, (0.385, 0.695), (0.42, 0.657))
    arrow(ax, (0.72, 0.852), (0.77, 0.75), rad=-0.15)
    arrow(ax, (0.72, 0.657), (0.77, 0.65), rad=0.15)

    box(ax, 0.03, 0.30, 0.94, 0.18,
        "暴露 ≥ 10 秒（不设上限）　｜　P 感知极化（立场估计＋比例估计）　｜　A 情感极化（温度计＋反感度）\n"
        "E/C 意见表达（状态性意愿＋评论框写作）　｜　M 操纵检查　｜　D 人口学与协变量",
        fs=10, fc="#f7f7f7")

    ax.text(0.5, 0.185, "目标有效样本 N = 150（每组 75）；预留 15% 流失，招募约 175",
            ha="center", fontsize=10.5, fontweight="bold")
    ax.text(0.5, 0.085, "固定测量顺序：感知判断在先，避免表达任务启动被试对「别人有多极端」的注意",
            ha="center", fontsize=10, color="#333333")
    fig.savefig(os.path.join(OUT, "fig3-实验流程.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


# -------------------------------------------------------------------------- 图 4
def fig4():
    import numpy as np
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    n = np.arange(20, 401)
    d = (1.96 + 0.84) * np.sqrt(2 / n)
    ax.plot(n, d, color="#222222", lw=2, label="两独立样本 t 检验（α=.05, power=.80, 双尾）")

    ax.axvline(75, color="#888888", ls="--", lw=1.2)
    ax.plot([75], [0.46], "o", color="#c0392b", ms=8, zorder=5)
    ax.annotate("本设计：每组 75（总 150）\n可检出 d ≈ 0.46",
                xy=(75, 0.46), xytext=(108, 0.78), fontsize=10.5,
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.2), color="#c0392b")

    ax.axhline(0.20, color="#2c6fbb", ls=":", lw=1.6)
    ax.annotate("TOST 等效边界 d = 0.20\n「未抬高」需每组约 310 人",
                xy=(310, 0.20), xytext=(150, 0.32), fontsize=10.5,
                arrowprops=dict(arrowstyle="->", color="#2c6fbb", lw=1.2), color="#2c6fbb")
    ax.plot([310], [0.20], "s", color="#2c6fbb", ms=8, zorder=5)

    ax.set_xlabel("每组样本量 n", fontsize=11.5)
    ax.set_ylabel("可检出的最小效应量 d", fontsize=11.5)
    ax.set_title("图 4　检验力：样本量与可检出效应", fontsize=13.5, fontweight="bold")
    ax.set_xlim(20, 400); ax.set_ylim(0, 1.0)
    ax.grid(alpha=0.25, ls=":")
    ax.legend(fontsize=10, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig4-检验力.png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig2(); fig3(); fig4()
    print("已生成：", ", ".join(sorted(os.listdir(OUT))))
