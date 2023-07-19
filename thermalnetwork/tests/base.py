import unittest
from pathlib import Path


class BaseCase(unittest.TestCase):
    def setUp(self) -> None:
        here = Path(__file__).parent
        self.demos_path = here.parent.parent / 'demos'
        self.test_outputs_path = here.resolve() / 'test_outputs'
        self.test_outputs_path.mkdir(exist_ok=True)
