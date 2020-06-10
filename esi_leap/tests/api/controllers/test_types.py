
class TestCollection(unittest.TestCase):

    def setUp(self):
        self.test_collection = types.Collection()
        self.test_collection._type = 'stuff'
        self.test_collection.stuff = [1, 2, 3, 4]

    def test_has_next(self):
        self.assertEqual(has_next(self.test_collection, 3), true)
        self.assertEqual(has_next(self.test_collection, 0), false)
