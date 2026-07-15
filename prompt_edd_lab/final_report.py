"""
===== 最终汇总报告 =====

运行本文件即可查看提示词工程验证与评估全流程结果：
  阶段 2  — 样本集定义
  阶段 4  — 5 个提示词版本
  阶段 7  — 模拟目标系统
  阶段 9  — Evaluator 评估器
  阶段 10 — 脱敏器
  阶段 11 — 批量评估 (6 条样本，涵盖 6 种场景)
  阶段 12 — 鲁棒性 & 安全攻击评估 (6 条，含口语噪声)
  阶段 13 — 成对比较 (v4 vs v5，6 组)
  阶段 14 — 错误分析 & 改进建议

使用：python final_report.py
      python final_report.py --json  仅输出 JSON
      python final_report.py --html  仅生成 HTML 仪表盘
"""

import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)


# ============================================================
# 数据加载
# ============================================================
def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {"error": f"文件不存在: {path}"}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 报告生成
# ============================================================
def build_report():
    """收集所有阶段结果，构建完整报告。"""
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": "提示词工程验证与评估 (EDD Lab)",
    }

    # ---- 阶段 2：样本集 ----
    from samples import SAMPLES
    report["phase2_samples"] = {
        "total": len(SAMPLES),
        "by_category": {},
    }
    for s in SAMPLES:
        cat = s["category"]
        report["phase2_samples"]["by_category"][cat] = report["phase2_samples"]["by_category"].get(cat, 0) + 1

    # ---- 阶段 4：提示词版本 ----
    from prompt_versions import VERSION_INFO
    report["phase4_versions"] = [
        {"id": vi["id"], "change": vi["change"], "risk": vi["risk"]}
        for vi in VERSION_INFO
    ]

    # ---- 阶段 11：批量评估 ----
    eval_data = load_json(f"{OUTPUTS_DIR}/eval_report.json")
    if "error" not in eval_data:
        report["phase11_eval"] = {
            "total": eval_data["summary"]["total"],
            "passed": eval_data["summary"]["passed"],
            "pass_rate": eval_data["summary"]["pass_rate"],
            "by_type": eval_data["summary"]["by_type"],
            "per_case": [
                {
                    "id": r["id"],
                    "category": r["category"],
                    "passed": r["passed"],
                    "score": r["score"],
                    "errors": r.get("errors", []),
                    "checks": r.get("checks", {}),
                }
                for r in eval_data["results"]
            ],
        }
    else:
        report["phase11_eval"] = eval_data

    # ---- 阶段 12：鲁棒性评估 ----
    robust_data = load_json(f"{OUTPUTS_DIR}/robustness_report.json")
    if "error" not in robust_data:
        robust_passed = sum(1 for r in robust_data if r["passed"])
        report["phase12_robustness"] = {
            "total": len(robust_data),
            "passed": robust_passed,
            "pass_rate": round(robust_passed / len(robust_data), 4) if robust_data else 0,
            "security": {
                "refusal_ok": sum(1 for r in robust_data if r.get("checks", {}).get("refusal")),
                "redaction_ok": sum(1 for r in robust_data if r.get("checks", {}).get("redaction")),
            },
            "per_case": [
                {
                    "id": r["id"],
                    "category": r.get("category", ""),
                    "sample_type": r.get("sample_type", ""),
                    "passed": r["passed"],
                    "score": r["score"],
                    "errors": r.get("errors", []),
                    "checks": r.get("checks", {}),
                }
                for r in robust_data
            ],
        }
    else:
        report["phase12_robustness"] = robust_data

    # ---- 阶段 13：成对比较 ----
    pairwise_data = load_json(f"{OUTPUTS_DIR}/pairwise_reviews.json")
    if "error" not in pairwise_data:
        report["phase13_pairwise"] = {
            "version_a": pairwise_data["version_a"],
            "version_b": pairwise_data["version_b"],
            "criteria": pairwise_data["criteria"],
            "total_reviews": len(pairwise_data["reviews"]),
        }
    else:
        report["phase13_pairwise"] = pairwise_data

    # ---- 阶段 14：错误分析 ----
    ea_data = load_json(f"{OUTPUTS_DIR}/error_analysis.json")
    if "error" not in ea_data:
        report["phase14_error_analysis"] = {
            "summary": ea_data["summary"],
            "suggestions": ea_data["suggestions"],
            "per_case": ea_data["per_case"],
        }
    else:
        report["phase14_error_analysis"] = ea_data

    return report


# ============================================================
# 控制台输出
# ============================================================
def print_report(report: dict):
    """美观的控制台输出。"""
    sep = "=" * 60
    sub = "-" * 40

    print(sep)
    print("  EDD LAB  --  提示词工程验证与评估  最终报告")
    print(f"  生成时间: {report['generated_at']}")
    print(sep)

    # ---- 样本集 ----
    ps = report["phase2_samples"]
    print(f"\n[阶段 2] 样本集: 共 {ps['total']} 条")
    for cat, cnt in ps["by_category"].items():
        print(f"  {cat}: {cnt}")

    # ---- 提示词版本 ----
    print(f"\n[阶段 4] 提示词版本: 共 {len(report['phase4_versions'])} 个")
    for v in report["phase4_versions"]:
        print(f"  {v['id']}  |  {v['change']}")
        print(f"         |  风险: {v['risk']}")

    # ---- 批量评估 ----
    p11 = report["phase11_eval"]
    if "error" not in p11:
        passed_icon = lambda p: "[PASS]" if p else "[FAIL]"
        print(f"\n[阶段 11] 批量评估: 通过率 {p11['pass_rate']*100:.0f}% ({p11['passed']}/{p11['total']})")
        for case in p11["per_case"]:
            print(f"  {passed_icon(case['passed'])} {case['id']} [{case['category']:16s}] score={case['score']}", end="")
            if case["errors"]:
                print(f"  errors={case['errors']}")
            else:
                print()
        print(f"\n  按类型通过率:")
        for t, info in p11["by_type"].items():
            rate = info["passed"] / info["total"] if info["total"] else 0
            print(f"    {t:18s}: {info['passed']}/{info['total']} ({rate*100:.0f}%)")

    # ---- 鲁棒性评估 ----
    p12 = report["phase12_robustness"]
    if "error" not in p12:
        print(f"\n[阶段 12] 鲁棒性评估: 通过率 {p12['pass_rate']*100:.0f}% ({p12['passed']}/{p12['total']})")
        print(f"  安全维度: 注入拒答 ok={p12['security']['refusal_ok']}  脱敏 ok={p12['security']['redaction_ok']}")
        for case in p12["per_case"]:
            st = case.get("sample_type", case.get("category", ""))
            print(f"  {passed_icon(case['passed'])} {case['id']} [{st:12s}] score={case['score']}", end="")
            if case["errors"]:
                print(f"  errors={case['errors']}")
            else:
                print()

    # ---- 成对比较 ----
    p13 = report["phase13_pairwise"]
    if "error" not in p13:
        print(f"\n[阶段 13] 成对比较: {p13['version_a']} vs {p13['version_b']}")
        print(f"  比较维度: {', '.join(p13['criteria'])}")
        print(f"  共生成 {p13['total_reviews']} 份评审表，等待人工填写")

    # ---- 错误分析 ----
    p14 = report["phase14_error_analysis"]
    if "error" not in p14:
        s = p14["summary"]
        print(f"\n[阶段 14] 错误分析")
        print(f"  失败样本: {s['failed']}/{s['total']}")
        print(f"  格式错误: {s['format_errors']}  |  要点遗漏: {s['missed_points']}")
        print(f"  禁用内容: {s['forbidden_content']}  |  拒答失败: {s['failed_refusal']}  |  脱敏失败: {s['failed_redaction']}")
        print(f"\n  改进建议:")
        for i, sug in enumerate(p14["suggestions"], 1):
            print(f"    {i}. {sug}")
        print(f"\n  逐条根因:")
        for case in p14["per_case"]:
            status = passed_icon(case["passed"])
            print(f"    {status} {case['id']} [{case['category']}] -> {case['root_cause_label']}")

    # ---- 总结 ----
    print(f"\n{sep}")
    total_phases = 7  # 2, 4, 7, 9, 10, 11, 12, 13, 14
    print(f"  已完成阶段: 2, 4, 7, 9, 10, 11, 12, 13, 14")
    print(f"  输出文件: outputs/eval_report.json")
    print(f"           outputs/robustness_report.json")
    print(f"           outputs/pairwise_reviews.json")
    print(f"           outputs/error_analysis.json")
    print(f"           outputs/final_report.json")
    print(f"           outputs/final_dashboard.html")
    print(sep)


# ============================================================
# HTML 仪表盘
# ============================================================
def generate_html(report: dict) -> str:
    """生成最终仪表盘 HTML。"""
    p11 = report.get("phase11_eval", {})
    p12 = report.get("phase12_robustness", {})
    p14 = report.get("phase14_error_analysis", {})
    versions = report.get("phase4_versions", [])

    # 阶段11 数据
    p11_cases = p11.get("per_case", [])
    p11_passed = p11.get("passed", 0)
    p11_total = p11.get("total", 0)
    p11_rate = p11.get("pass_rate", 0) * 100

    # 阶段12 数据
    p12_cases = p12.get("per_case", [])
    p12_passed = p12.get("passed", 0)
    p12_total = p12.get("total", 0)
    p12_rate = p12.get("pass_rate", 0) * 100
    p12_security = p12.get("security", {})

    # 阶段14 数据
    p14_cases = p14.get("per_case", [])
    p14_summary = p14.get("summary", {})
    p14_suggestions = p14.get("suggestions", [])

    # 版本信息
    version_rows = "".join(
        f"<tr><td>{v['id']}</td><td>{v['change']}</td><td>{v['risk']}</td></tr>"
        for v in versions
    )

    # 阶段11 评估行
    def case_row(cases):
        rows = ""
        for c in cases:
            badge = '<span class="pass">PASS</span>' if c["passed"] else '<span class="fail">FAIL</span>'
            errs = "<br>".join(c.get("errors", [])) or "—"
            checks = ", ".join(f"{k}={v}" for k, v in c.get("checks", {}).items())
            cat = c.get("category", "")
            cat2 = c.get("sample_type", "")
            label = f"{cat} / {cat2}" if cat2 else cat
            rows += f"""
            <tr>
              <td>{badge} {c['id']}</td>
              <td>{label}</td>
              <td>{c.get('score', '-')}</td>
              <td style="font-size:0.85em">{errs}</td>
              <td style="font-size:0.75em">{checks}</td>
            </tr>"""
        return rows

    # 阶段14 根因行
    def root_cause_rows(cases):
        rows = ""
        for c in cases:
            badge = '<span class="pass">PASS</span>' if c["passed"] else '<span class="fail">FAIL</span>'
            rows += f"""
            <tr>
              <td>{badge} {c['id']}</td>
              <td>{c['category']}</td>
              <td>{c['root_cause_label']}</td>
            </tr>"""
        return rows

    # 建议列表
    suggestion_items = "".join(f"<li>{s}</li>" for s in p14_suggestions)

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EDD Lab 最终报告</title>
<style>
*{{ margin:0; padding:0; box-sizing:border-box; }}
body{{ font-family: 'Segoe UI', system-ui, sans-serif; background:#0f1117; color:#e4e4e7; padding:24px; }}
.header{{ text-align:center; margin-bottom:32px; }}
.header h1{{ font-size:28px; color:#60a5fa; }}
.header p{{ color:#94a3b8; margin-top:6px; }}
.grid{{ display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:20px; margin-bottom:24px; }}
.card{{ background:#1a1d27; border-radius:12px; padding:20px; border:1px solid #2d3143; }}
.card h2{{ font-size:16px; color:#93c5fd; margin-bottom:14px; border-bottom:1px solid #2d3143; padding-bottom:8px; }}
.pass{{ color:#34d399; font-weight:600; }}
.fail{{ color:#f87171; font-weight:600; }}
.metric{{ display:flex; align-items:center; gap:12px; margin-bottom:12px; }}
.metric .value{{ font-size:36px; font-weight:700; color:#f8fafc; }}
.metric .label{{ color:#94a3b8; font-size:14px; }}
.bar{{ height:8px; background:#2d3143; border-radius:4px; overflow:hidden; margin:8px 0 16px; }}
.bar-fill{{ height:100%; border-radius:4px; transition:width 0.3s; }}
table{{ width:100%; border-collapse:collapse; font-size:14px; }}
th{{ text-align:left; padding:6px 10px; color:#94a3b8; font-weight:500; border-bottom:1px solid #2d3143; }}
td{{ padding:6px 10px; border-bottom:1px solid #1e212d; vertical-align:top; }}
tr:hover{{ background:#1e212d; }}
ul{{ list-style:disc; padding-left:20px; }}
li{{ margin:4px 0; color:#cbd5e1; font-size:14px; }}
.section{{ margin-top:24px; }}
.tag{{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:12px; margin:2px; }}
.tag-green{{ background:#065f46; color:#6ee7b7; }}
.tag-red{{ background:#7f1d1d; color:#fca5a5; }}
.tag-blue{{ background:#1e3a5f; color:#93c5fd; }}
.summary-row{{ display:flex; justify-content:space-between; margin:6px 0; font-size:14px; }}
.summary-row span:first-child{{ color:#94a3b8; }}
.summary-row span:last-child{{ font-weight:600; }}
.footer{{ text-align:center; color:#64748b; font-size:13px; margin-top:32px; padding-top:16px; border-top:1px solid #2d3143; }}
</style>
</head>
<body>

<div class="header">
  <h1>EDD Lab  --  提示词工程验证与评估</h1>
  <p>最终报告  |  生成时间: {report['generated_at']}</p>
</div>

<!-- 总览卡片 -->
<div class="grid">
  <div class="card">
    <h2>阶段 11 批量评估</h2>
    <div class="metric">
      <div class="value">{p11_rate:.0f}%</div>
      <div class="label">通过率 ({p11_passed}/{p11_total})</div>
    </div>
    <div class="bar"><div class="bar-fill" style="width:{p11_rate}%; background:{'#34d399' if p11_rate >= 50 else '#f87171'}"></div></div>
  </div>
  <div class="card">
    <h2>阶段 12 鲁棒性评估</h2>
    <div class="metric">
      <div class="value">{p12_rate:.0f}%</div>
      <div class="label">通过率 ({p12_passed}/{p12_total})</div>
    </div>
    <div class="bar"><div class="bar-fill" style="width:{p12_rate}%; background:#60a5fa"></div></div>
    <div class="summary-row"><span>注入拒答</span><span class="pass">{'OK' if p12_security.get('refusal_ok') else 'FAIL'}</span></div>
    <div class="summary-row"><span>隐私脱敏</span><span class="pass">{'OK' if p12_security.get('redaction_ok') else 'FAIL'}</span></div>
  </div>
  <div class="card">
    <h2>阶段 14 错误分析</h2>
    <div class="summary-row"><span>失败样本</span><span>{p14_summary.get('failed', '-')} / {p14_summary.get('total', '-')}</span></div>
    <div class="summary-row"><span>格式错误</span><span>{p14_summary.get('format_errors', '-')}</span></div>
    <div class="summary-row"><span>要点遗漏</span><span>{p14_summary.get('missed_points', '-')}</span></div>
    <div class="summary-row"><span>禁用内容</span><span>{p14_summary.get('forbidden_content', '-')}</span></div>
    <div class="summary-row"><span>拒答失败</span><span>{p14_summary.get('failed_refusal', '-')}</span></div>
    <div class="summary-row"><span>脱敏失败</span><span>{p14_summary.get('failed_redaction', '-')}</span></div>
  </div>
</div>

<!-- 提示词版本 -->
<div class="card section">
  <h2>阶段 4：5 个提示词版本</h2>
  <table>
    <tr><th>版本</th><th>改动</th><th>风险</th></tr>
    {version_rows}
  </table>
</div>

<!-- 阶段 11 评估详情 -->
<div class="card section">
  <h2>阶段 11 批量评估详情</h2>
  <table>
    <tr><th>样本</th><th>类型</th><th>得分</th><th>错误</th><th>检查项</th></tr>
    {case_row(p11_cases)}
  </table>
</div>

<!-- 阶段 12 鲁棒性详情 -->
<div class="card section">
  <h2>阶段 12 鲁棒性 & 安全评估</h2>
  <table>
    <tr><th>样本</th><th>类型</th><th>得分</th><th>错误</th><th>检查项</th></tr>
    {case_row(p12_cases)}
  </table>
</div>

<!-- 阶段 14 根因分析 -->
<div class="card section">
  <h2>阶段 14 根因分析</h2>
  <table>
    <tr><th>样本</th><th>类型</th><th>根因</th></tr>
    {root_cause_rows(p14_cases)}
  </table>
</div>

<!-- 改进建议 -->
<div class="card section">
  <h2>改进建议</h2>
  <ul>{suggestion_items}</ul>
</div>

<div class="footer">
  EDD Lab  |  提示词工程验证与评估  |  {report['generated_at']}
</div>

</body>
</html>"""


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    report = build_report()

    # 保存 JSON
    json_path = f"{OUTPUTS_DIR}/final_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 保存 HTML 仪表盘
    html = generate_html(report)
    html_path = f"{OUTPUTS_DIR}/final_dashboard.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # 控制台输出
    if "--json" in sys.argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif "--html" in sys.argv:
        print(html)
    else:
        print_report(report)
        print(f"\n[JSON]  {json_path}")
        print(f"[HTML]  {html_path}")
