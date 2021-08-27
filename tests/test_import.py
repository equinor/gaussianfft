import unittest


class TestImport(unittest.TestCase):
    def test_simple(self):
        import gaussianfft
        self.assertIn('amplitude', gaussianfft.quote())


if __name__ == '__main__':
    unittest.main()
