import pandas as pd
from data import CASES
from rag_system import keyword_baseline, run_rag, prompt_v1, prompt_v2, check_l1


if __name__ == "__main__":
	total = len(CASES)

	print("🚀 1/3 计算 Baseline (纯关键词搜索) 得分...")
	baseline_correct = sum(
		1 for case in CASES
		if keyword_baseline(case.text) == str(case.expect.get("eligible", "False"))
	)

	print("🚀 2/3 运行 Prompt Version 1 测试...")
	v1_pass = sum(1 for case in CASES if check_l1(run_rag(case.text, prompt_v1), case))

	print("🚀 3/3 运行 Prompt Version 2 测试...")
	v2_pass = sum(1 for case in CASES if check_l1(run_rag(case.text, prompt_v2), case))

	print("\n" + "=" * 45)
	print("📈 【最终评估汇总表格数据】")
	print(f"1. Non-AI Baseline Pass Rate : {baseline_correct}/{total} ({baseline_correct / total:.1%})")
	print(f"2. Prompt Version 1 Pass Rate : {v1_pass}/{total} ({v1_pass / total:.1%})")
	print(f"3. Prompt Version 2 Pass Rate : {v2_pass}/{total} ({v2_pass / total:.1%})")
	print("=" * 45)
