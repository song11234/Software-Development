from agents import planner_agent, programmer_agent, reviewer_agent, tester_agent, checkpoint_agent
from state import GoalContract, WorkflowState

g = GoalContract("add function", ["add(2,3)==5"], [], [])
s = WorkflowState(goal=g)

s = planner_agent(s)
print("plan:", s.plan)

s = programmer_agent(s)
print("draft1:", repr(s.draft), "| attempts:", s.attempts)

s = reviewer_agent(s)
print("review_passed:", s.review_passed, "|", s.review_feedback)

s = tester_agent(s)
print("tests_passed:", s.tests_passed, "| attempts:", s.attempts)

# Round 2: after review feedback, programmer should generate correct code
s = programmer_agent(s)
print("draft2:", repr(s.draft), "| attempts:", s.attempts)

s = reviewer_agent(s)
print("review_passed:", s.review_passed, "|", s.review_feedback)

s = tester_agent(s)
print("tests_passed:", s.tests_passed)

s = checkpoint_agent(s, auto_approve=True)
print("status:", s.status, "| approved:", s.human_approved)
print("history steps:", len(s.history))
print("OK")
