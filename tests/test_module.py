import unittest

import stactools.msbuildings


class TestModule(unittest.TestCase):
    def test_version(self) -> None:
        self.assertIsNotNone(stactools.msbuildings.__version__)
