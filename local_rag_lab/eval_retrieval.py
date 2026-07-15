from eval_cases import EVAL_CASES
from retriever import retrieve
from student_info import print_student_id

print_student_id()

hit = 0
for case in EVAL_CASES:
    results = retrieve(case["question"], top_k=3)
    ids = [item["id"] for item in results]
    ok = case["expected"] in ids
    hit += int(ok)
    print(case["question"], ids, "OK" if ok else "MISS")

print(f"hit_rate={hit}/{len(EVAL_CASES)}")
