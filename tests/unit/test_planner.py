"""
Unit tests for PlannerAgent.
"""

import sys
import unittest
from pathlib import Path

src_path = str(Path(__file__).resolve().parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cognisynth.agents.planner import PlannerAgent
from cognisynth.schemas.research import TaskType


class TestPlannerAgent(unittest.TestCase):
    def test_default_plan_structure(self):
        planner = PlannerAgent(max_tasks=5)
        plan = planner._generate_default_plan("Quantum Computing Breakthroughs")

        self.assertEqual(plan.objective, "Quantum Computing Breakthroughs")
        self.assertGreaterEqual(len(plan.tasks), 3)

        # Check task types
        types = [t.type for t in plan.tasks]
        self.assertIn(TaskType.SEARCH, types)
        self.assertIn(TaskType.SYNTHESIZE, types)
        self.assertIn(TaskType.CRITIQUE, types)

        # Check dependencies
        synth_task = [t for t in plan.tasks if t.type == TaskType.SYNTHESIZE][0]
        self.assertTrue(len(synth_task.dependencies) >= 1)


if __name__ == "__main__":
    unittest.main()
