import unittest

import stactools.bingbuildings


class TestModule(unittest.TestCase):
    def test_version(self) -> None:
        self.assertIsNotNone(stactools.bingbuildings.__version__)
