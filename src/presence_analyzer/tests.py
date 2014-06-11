# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=E1103
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('presence_weekday')

    def test_page_to_render(self):
        """
        Test correct name of page to render
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday')
        resp = self.client.get('/base_template')
        resp1 = self.client.get('/page_not_found')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, resp1.data)

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_api_mean_time_weekday(self):
        """
        Test mean presence time
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        sample_data = json.loads(resp.data)
        self.assertEqual(sample_data, [
            [u'Mon', 0.0],
            [u'Tue', 30047.0],
            [u'Wed', 24465.0],
            [u'Thu', 23705.0],
            [u'Fri', 0.0],
            [u'Sat', 0.0],
            [u'Sun', 0.0],
        ])

        resp = self.client.get('/api/v1/mean_time_weekday/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        sample_data = json.loads(resp.data)
        self.assertEqual(sample_data, [
            [u'Mon', 24123.0],
            [u'Tue', 16564.0],
            [u'Wed', 25321.0],
            [u'Thu', 22984.0],
            [u'Fri', 6426.0],
            [u'Sat', 0.0],
            [u'Sun', 0.0],
        ])

    def test_presence_weekday_view(self):
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        sample_data = json.loads(resp.data)
        self.assertEqual(sample_data, [
            [u'Weekday', u'Presence (s)'],
            [u'Mon', 0],
            [u'Tue', 30047],
            [u'Wed', 24465],
            [u'Thu', 23705],
            [u'Fri', 0],
            [u'Sat', 0],
            [u'Sun', 0],
        ])

        resp = self.client.get('/api/v1/presence_weekday/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        sample_data = json.loads(resp.data)
        self.assertEqual(sample_data, [
            [u'Weekday', u'Presence (s)'],
            [u'Mon', 24123],
            [u'Tue', 16564],
            [u'Wed', 25321],
            [u'Thu', 45968],
            [u'Fri', 6426],
            [u'Sat', 0],
            [u'Sun', 0],
        ])

    def test_presence_start_end_view(self):
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        sample_data = json.loads(resp.data)
        self.assertEqual(sample_data, [
            [u'Mon', 0, 0],
            [u'Tue', 34745.0, 64792.0],
            [u'Wed', 33592.0, 58057.0],
            [u'Thu', 38926.0, 62631.0],
            [u'Fri', 0, 0],
            [u'Sat', 0, 0],
            [u'Sun', 0, 0]
        ])

        resp = self.client.get('/api/v1/presence_start_end/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        sample_data = json.loads(resp.data)
        self.assertEqual(sample_data, [
            [u'Mon', 33134.0, 57257.0],
            [u'Tue', 33590.0, 50154.0],
            [u'Wed', 33206.0, 58527.0],
            [u'Thu', 35602.0, 58586.0],
            [u'Fri', 47816.0, 54242.0],
            [u'Sat', 0, 0],
            [u'Sun', 0, 0]
        ])


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """
    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_data = datetime.date(2013, 9, 10)
        self.assertIn(sample_data, data[10])
        self.assertItemsEqual(data[10][sample_data].keys(), ['start', 'end'])
        self.assertEqual(data[10][sample_data]['start'],
                         datetime.time(9, 39, 5))

    def test_group_by_weekday(self):
        """
        Test groups precence entries by weekday
        """
        box = utils.get_data()
        data = utils.group_by_weekday(box[10])
        self.assertIsInstance(data, dict)
        sample_data = {
            0: [],
            1: [30047],
            2: [24465],
            3: [23705],
            4: [],
            5: [],
            6: [],
        }
        self.assertDictEqual(data, sample_data)

        data = utils.group_by_weekday(box[11])
        self.assertIsInstance(data, dict)
        sample_data = {
            0: [24123],
            1: [16564],
            2: [25321],
            3: [22969, 22999],
            4: [6426],
            5: [],
            6: [],
        }
        self.assertDictEqual(data, sample_data)

    def test_seconds_since_midnight(self):
        """
        Test correct amout of seconds since midnight.
        """
        data = utils.seconds_since_midnight(datetime.time(9, 39, 5))
        self.assertEqual(data, 34745)

        data = utils.seconds_since_midnight(datetime.time(10, 48, 46))
        self.assertEqual(data, 38926)

        data = utils.seconds_since_midnight(datetime.time(9, 28, 8))
        self.assertEqual(data, 34088)

    def test_interval(self):
        """
        Test correct interval between two datetime.time objects.
        """
        data = utils.interval(
            datetime.time(9, 39, 05),
            datetime.time(17, 59, 52)
        )
        self.assertEqual(data, 30047)

        data = utils.interval(
            datetime.time(9, 19, 52),
            datetime.time(16, 07, 37),
        )
        self.assertEqual(data, 24465)

        data = utils.interval(
            datetime.time(10, 48, 46),
            datetime.time(17, 23, 51)
        )
        self.assertEqual(data, 23705)

    def test_mean(self):
        """
        Test correct mean value.
        """
        self.assertEqual(utils.mean([10, 20, 30]), 20)
        self.assertAlmostEqual(utils.mean([10.12, 20.12, 30.12]), 20.12)
        self.assertAlmostEqual(
            utils.mean([10.1234567, 20.1234567, 30.1234567]),
            20.1234567
        )
        self.assertEqual(utils.mean([]), 0)

    def test_return_id_start_end(self):
        """
        Test correct values of id, start, end variables
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        sample_data = utils.return_id_start_end(data[10])
        self.assertDictEqual(sample_data, {
            0: {'start': [], 'end': []},
            1: {'start': [34745], 'end': [64792]},
            2: {'start': [33592], 'end': [58057]},
            3: {'start': [38926], 'end': [62631]},
            4: {'start': [], 'end': []},
            5: {'start': [], 'end': []},
            6: {'start': [], 'end': []},
        })

        sample_data = utils.return_id_start_end(data[10])
        self.assertDictEqual(sample_data, {
            0: {'start': [], 'end': []},
            1: {'start': [34745], 'end': [64792]},
            2: {'start': [33592], 'end': [58057]},
            3: {'start': [38926], 'end': [62631]},
            4: {'start': [], 'end': []},
            5: {'start': [], 'end': []},
            6: {'start': [], 'end': []},
        })


def suite():
    """
    Default test suite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
