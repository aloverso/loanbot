#!flask/bin/python
import unittest

from server import app

def add(a, b):
  return a+b


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_add(self):
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(3, 4), 7)

if __name__ == '__main__':
    unittest.main()