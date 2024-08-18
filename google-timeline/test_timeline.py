import asyncio
import unittest
import os
from unittest.mock import patch, mock_open
import json
from datetime import datetime
from pathlib import Path
from timeline import *


class TestTimeline(unittest.TestCase):

    PATH_TO_FOLDER = Path(os.path.expanduser('~'), 'OneDrive', 'Documenten', 'Wil', 'Takeout', 'Locatiegeschiedenis (Tijdlijn)', 'Semantic Location History')


    # TODO gebruik mock
    def test_get_timeline_object_generator(self):
        generator = get_timeline_object_generator(self.PATH_TO_FOLDER)
        first_item = next(generator)
        self.assertIsInstance(first_item, dict)
        self.assertEqual(list(first_item.keys()), ['placeVisit'])

    def test_timeline_object_generator_bogus_year(self):
        # this folder doen't exist
        generator = get_timeline_object_generator(self.PATH_TO_FOLDER, 1982)
        self.assertRaises(StopIteration, next, generator)

    def test_is_place_visit(self):
        self.assertTrue(is_place_visit({'placeVisit': {}}))
        self.assertFalse(is_place_visit({'noPlaceVisit': {}}))
        self.assertFalse(is_place_visit({'placeVisit': {}, 'noPlaceVisit': {}}))

    def test_is_activity_segment(self):
        self.assertTrue(is_activity_segment({'activitySegment': {}}))
        self.assertFalse(is_activity_segment({'noActivitySegment': {}}))
        self.assertFalse(is_place_visit({'activitySegment': {}, 'noActivitySegment': {}}))

    def test_is_in_passenger_vehicle(self):
        self.assertTrue(is_in_passenger_vehicle({"activityType": "IN_PASSENGER_VEHICLE"}))
        self.assertFalse(is_in_passenger_vehicle({"activityType": "BLABLA"}))
        self.assertFalse(is_in_passenger_vehicle({"noActivityType": "BLABLA"}))
        self.assertFalse(is_in_passenger_vehicle({"noActivityType": "IN_PASSENGER_VEHICLE"}))

    def test_item_is_on_a_weekday(self):
        # a random week in July 2024, starting on a Monday
        for d in range(8, 13):
            self.assertTrue(item_is_on_a_weekday({"duration": {
                "startTimestamp": f"2024-07-{d:02}T12:00:00.000Z",
                "endTimestamp": f"2024-07-{d:02}T13:00:00.000Z"
            }}))
        for d in range(13, 15):
            self.assertFalse(item_is_on_a_weekday({"duration": {
                "startTimestamp": f"2024-07-{d:02}T12:00:00.000Z",
                "endTimestamp": f"2024-07-{d:02}T13:00:00.000Z"
            }}))
        # and a night time situation
        self.assertFalse(item_is_on_a_weekday({"duration": {
            "startTimestamp": "2024-07-07T23:00:00.000Z",
            "endTimestamp": "2024-07-08T01:00:00.000Z"
        }}))
        self.assertFalse(item_is_on_a_weekday({"duration": {
            "startTimestamp": "2024-07-12T23:00:00.000Z",
            "endTimestamp": "2024-07-13T01:00:00.000Z"
        }}))
    
    def test_is_within_time_range(self):
        # all durations are UTC and it's July so the durations are 2hrs early for Amsterdam daylight saving time
        self.assertTrue(is_within_time_range({"duration": {
            "startTimestamp": "2024-07-08T10:00:00.000Z",
            "endTimestamp": "2024-07-08T11:00:00.000Z"
        }}))
        # not a weekday
        self.assertFalse(is_within_time_range({"duration": {
            "startTimestamp": "2024-07-07T10:00:00.000Z",
            "endTimestamp": "2024-07-07T11:00:00.000Z"
        }}))
        # too late on a Thursday
        self.assertFalse(is_within_time_range({"duration": {
            "startTimestamp": "2024-07-11T18:00:00.000Z",
            "endTimestamp": "2024-07-11T19:00:00.000Z"
        }}))
        # starts too early on a Thursday
        self.assertFalse(is_within_time_range({"duration": {
            "startTimestamp": "2024-07-11T03:55:00.000Z",
            "endTimestamp": "2024-07-11T05:00:00.000Z"
        }}))


    def test_is_within_date_range(self):
        # TODO
        self.assertFalse(True)

    def test_foo(self):
        new_place_visit, segment, generator = asyncio.run(bar())
        self.assertIsNotNone(segment)

if __name__ == "__main__":
    unittest.main()
