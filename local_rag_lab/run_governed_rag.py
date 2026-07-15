from governed_rag import answer_with_governance
from student_info import print_student_id

CASES = [
    ("原石、祈愿和角色养成有什么关系？", "student", False),
    ("课堂讲角色养成时有什么建议？", "student", False),
    ("课堂讲角色养成时有什么建议？", "teacher", False),
]

print_student_id()
for question, role, include_expired in CASES:
    print("=" * 80)
    print("question:", question)
    print("role:", role)
    result = answer_with_governance(question, role=role, include_expired=include_expired)
    print(result["answer"])
    print("citations:", result["citations"])
    print("warnings:", result["warnings"])
