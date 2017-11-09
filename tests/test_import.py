import unittest


class TestImport(unittest.TestCase):
    def test_simple(self):
        import nrlib
        self.assertIn('amplitude', nrlib.quote())


if __name__ == '__main__':
    unittest.main()
