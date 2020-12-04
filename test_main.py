import unittest
import main
import datetime
from datetime import datetime
from datetime import timedelta

class testmain(unittest.TestCase):
    def test_get_covid(self):
        covid = main.get_covid()
        length = len(covid)
        self.assertGreater(len(covid[0]['content']), 1)
        self.assertEqual(length, 1)

    def test_get_news(self):
        news = main.get_news()
        self.assertGreater(len(news),0)

    def test_get_weather(self):
        weather = main.get_weather()
        self.assertEqual(len(weather),1)

    def test_get_api(self):
        api = main.get_api()
        self.assertEqual(len(api), 10)

    def test_get_alarms(self):
        alarm = main.get_alarms('2020-12-02T14:05', 'test')
        self.assertEqual(len(alarm), 1)
        self.assertEqual(alarm[0]['title'], "test")
        self.assertEqual(alarm[0]['alarm'], "yes")
    
    def test_alarm_set(self):
        now = datetime.now() + timedelta(seconds = 60)
        alarm_set = main.alarm_set(now)
        self.assertGreater(alarm_set, 0)

