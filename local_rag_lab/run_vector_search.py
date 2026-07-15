from vector_db import search_vector_db
from student_info import print_student_id

print_student_id()

for role in ["student", "teacher"]:
    print("=" * 80)
    print("role:", role)
    for item in search_vector_db("课堂讲角色养成时有什么建议？", role=role):
        print(item["chunk_id"], item["metadata"]["title"], item["score"])
