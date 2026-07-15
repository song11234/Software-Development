from rag_answer import answer_with_context
from student_info import print_student_id

OUT_OF_SCOPE = [
    "今天北京天气怎么样？",
    "请推荐一款手机。",
    "请解释量子力学的测不准原理。",
]

print_student_id()
for question in OUT_OF_SCOPE:
    result = answer_with_context(question)
    print("=" * 60)
    print("Q:", question)
    print("grounded:", result["grounded"], "| answer:", result["answer"])
