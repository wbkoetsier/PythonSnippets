import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
from segments_timeline import (
    find_first_place_segment,
    get_timeline_object_generator,
    is_place_visit,
    is_activity_segment,
    is_in_passenger_vehicle,
    is_on_a_weekday,
    make_bin,
    make_bins,
    make_segment,
    peek,
)


class TestSegments(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{"timelineObjects": [{"id": 1}, {"id": 2}]}')
    @patch("segments_timeline.Path.exists", return_value=True)
    def test_get_timeline_object_generator(self, *args, **kwargs):
        expected = [{"id": 1}, {"id": 2}] * 12  # a file for each month
        self.assertEqual(expected, list(get_timeline_object_generator(Path("/a/path"), 1994)))

    @patch("segments_timeline.Path.exists", return_value=False)
    def test_get_timeline_object_generator_file_not_found(self, *args, **kwargs):
        self.assertEqual([], list(get_timeline_object_generator(Path("/a/path"), 1993)))

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
            self.assertTrue(
                is_on_a_weekday(
                    {
                        "duration": {
                            "startTimestamp": f"2024-07-{d:02}T12:00:00.000Z",
                            "endTimestamp": f"2024-07-{d:02}T13:00:00.000Z",
                        }
                    }
                )
            )
        for d in range(13, 15):
            self.assertFalse(
                is_on_a_weekday(
                    {
                        "duration": {
                            "startTimestamp": f"2024-07-{d:02}T12:00:00.000Z",
                            "endTimestamp": f"2024-07-{d:02}T13:00:00.000Z",
                        }
                    }
                )
            )
        # and a night time situation
        self.assertFalse(
            is_on_a_weekday(
                {"duration": {"startTimestamp": "2024-07-07T23:00:00.000Z", "endTimestamp": "2024-07-08T01:00:00.000Z"}}
            )
        )
        self.assertFalse(
            is_on_a_weekday(
                {"duration": {"startTimestamp": "2024-07-12T23:00:00.000Z", "endTimestamp": "2024-07-13T01:00:00.000Z"}}
            )
        )

    def test_peek(self):
        lst = [1, 2, 3, 4, 7]
        self.assertEqual(7, peek(lst, -1))
        self.assertEqual(3, peek(lst, -3))
        self.assertEqual(1, peek(lst, -5))
        self.assertEqual(1, peek(lst, 0))
        self.assertEqual(7, peek(lst, 4))
        self.assertEqual(None, peek(lst, 5))
        self.assertEqual(None, peek(lst, -6))

    def test_make_segment_with_activity(self):
        obj_gen = (
            to
            for to in [
                {"activitySegment": {"activityType": "WALKING", "val": 1}},
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 2}},
                {"activitySegment": {"activityType": "WALKING", "val": 3}},
                {"placeVisit": {"val": 4}},
            ]
        )

        current_obj, _, actual_segment = make_segment(next(obj_gen), obj_gen, [])

        self.assertEqual({"placeVisit": {"val": 4}}, current_obj)
        self.assertEqual(
            [
                {"activitySegment": {"activityType": "WALKING", "val": 1}},
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 2}},
                {"activitySegment": {"activityType": "WALKING", "val": 3}},
            ],
            actual_segment,
        )

    def test_make_segment_with_address(self):
        obj_gen = (
            to
            for to in [
                {"placeVisit": {"val": 1}},
                {"activitySegment": {"activityType": "WALKING", "val": 2}},
                {"placeVisit": {"val": 3}},
                {"activitySegment": {"activityType": "WALKING", "val": 4}},
                {"placeVisit": {"val": 5}},
                {"activitySegment": {"activityType": "WALKING", "val": 6}},
                {"placeVisit": {"val": 7}},
                {"placeVisit": {"val": 8}},
                {"activitySegment": {"activityType": "WALKING", "val": 9}},
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 10}},
                {"activitySegment": {"activityType": "WALKING", "val": 11}},
                {"placeVisit": {"val": 12}},
            ]
        )
        current_obj, _, actual_segment = make_segment(next(obj_gen), obj_gen, [])

        self.assertEqual({"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 10}}, current_obj)
        self.assertEqual(
            [
                {"placeVisit": {"val": 1}},
                {"activitySegment": {"activityType": "WALKING", "val": 2}},
                {"placeVisit": {"val": 3}},
                {"activitySegment": {"activityType": "WALKING", "val": 4}},
                {"placeVisit": {"val": 5}},
                {"activitySegment": {"activityType": "WALKING", "val": 6}},
                {"placeVisit": {"val": 7}},
                {"placeVisit": {"val": 8}},
                {"activitySegment": {"activityType": "WALKING", "val": 9}},
            ],
            actual_segment,
        )

    def test_make_bin(self):
        # bin is always place-segment, activity-segment, place-segment, first place-segment is the same as the last
        # place-segment of the previous bin
        # left segment should always present
        obj_gen = (
            to
            for to in [
                # left p-segment
                {"placeVisit": {"val": 3}},
                # a-segment
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 4}},
                # right p-segment
                {"placeVisit": {"val": 5}},
                {"activitySegment": {"activityType": "WALKING", "val": 6}},
                {"placeVisit": {"val": 7}},
                {"activitySegment": {"activityType": "WALKING", "val": 8}},
                {"placeVisit": {"val": 9}},
                {"activitySegment": {"activityType": "WALKING", "val": 10}},
                {"placeVisit": {"val": 11}},
                {"placeVisit": {"val": 12}},
                {"activitySegment": {"activityType": "WALKING", "val": 13}},
                # start next a-segment, should not be in the bin, current object should be 14
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 14}},
                {"activitySegment": {"activityType": "WALKING", "val": 15}},
                {"placeVisit": {"val": 16}},
            ]
        )

        # first bin, so manually create the left segment and set the generator head to the next object (a with value 4)
        bin_left_seg = next(obj_gen)

        current_obj, _, actual_bin = make_bin(next(obj_gen), obj_gen, [[bin_left_seg]])  # bin is list of lists

        self.assertEqual({"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 14}}, current_obj)
        self.assertEqual(3, len(actual_bin))
        self.assertEqual(
            [
                [{"placeVisit": {"val": 3}}],
                [{"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 4}}],
                [
                    {"placeVisit": {"val": 5}},
                    {"activitySegment": {"activityType": "WALKING", "val": 6}},
                    {"placeVisit": {"val": 7}},
                    {"activitySegment": {"activityType": "WALKING", "val": 8}},
                    {"placeVisit": {"val": 9}},
                    {"activitySegment": {"activityType": "WALKING", "val": 10}},
                    {"placeVisit": {"val": 11}},
                    {"placeVisit": {"val": 12}},
                    {"activitySegment": {"activityType": "WALKING", "val": 13}},
                ],
            ],
            actual_bin,
        )

    def test_make_last_bin(self):
        # the last bin could be incomplete
        obj_gen = (
            to
            for to in [
                # left p-segment
                {"placeVisit": {"val": 1}},
                # a-segment
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 2}},
                # and that's it
            ]
        )

        # manually create first bin with left segment, which is just the first object in this case
        bin_left_seg = next(obj_gen)
        current_obj, obj_gen, actual_bin = make_bin(next(obj_gen), obj_gen, [[bin_left_seg]])  # bin is list of lists

        self.assertEqual(None, current_obj)
        self.assertEqual(2, len(actual_bin))
        self.assertRaises(StopIteration, next, obj_gen)
        self.assertEqual(
            [
                [{"placeVisit": {"val": 1}}],
                [{"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 2}}],
            ],
            actual_bin,
        )

    def test_find_first_place_segment(self):
        obj_gen = (
            to
            for to in [
                # first segment is activity
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 1}},
                # second segment is place
                {"placeVisit": {"val": 2}},
                # first object of the next segment (activity)
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 3}},
            ]
        )
        current_obj, segment, obj_gen = find_first_place_segment(next(obj_gen), obj_gen)
        # segment is place segment
        self.assertTrue(any("placeVisit" in obj for obj in segment))
        # last object to have been yielded from the generator is the first object of the next segment
        self.assertEqual({"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 3}}, current_obj)
        # so the generator should now be empty
        self.assertRaises(StopIteration, next, obj_gen)

    def test_make_bins(self):
        obj_gen = (
            to
            for to in [
                # first objects excluded from any bin
                {"activitySegment": {"activityType": "WALKING", "val": 1}},
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 2}},
                # start p-segment, bin 1 ('home')
                {"placeVisit": {"val": 3}},
                # start a-segment, bin 1 ('drive')
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 4}},
                # start p-segment, bin 1 & 2 ('customer 1')
                {"placeVisit": {"val": 5}},
                {"activitySegment": {"activityType": "WALKING", "val": 6}},
                {"placeVisit": {"val": 7}},
                {"activitySegment": {"activityType": "WALKING", "val": 8}},
                {"placeVisit": {"val": 9}},
                {"activitySegment": {"activityType": "WALKING", "val": 10}},
                {"placeVisit": {"val": 11}},
                {"placeVisit": {"val": 12}},
                {"activitySegment": {"activityType": "WALKING", "val": 13}},
                # start a-segment, bin 2 ('drive')
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 14}},
                {"activitySegment": {"activityType": "WALKING", "val": 15}},
                # start p-segment, bin 2 & 3 ('home')
                {"placeVisit": {"val": 16}},
                {"activitySegment": {"activityType": "WALKING", "val": 17}},
                {"placeVisit": {"val": 18}},
                # start a-segment, bin 3 ('drive')
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 19}},
                # start p-segment, bin 3 (& 4 fwiw) ('customer 2')
                {"placeVisit": {"val": 20}},
                {"activitySegment": {"activityType": "WALKING", "val": 21}},
                {"placeVisit": {"val": 22}},
                # start a-segment, bin 4, incomplete bin
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 23}},
            ]
        )

        actual_bins = make_bins(next(obj_gen), [], obj_gen, [])

        # the first and last bins aren't included, bc they're both incomplete
        self.assertEqual(3, len(actual_bins))
        self.assertEqual({"placeVisit": {"val": 3}}, actual_bins[0][0][0])
        self.assertEqual({"placeVisit": {"val": 22}}, actual_bins[-1][-1][-1])
        # generator should now be empty
        self.assertRaises(StopIteration, next, obj_gen)
        # but, yk, just to be sure
        expected = [
            [
                [{"placeVisit": {"val": 3}}],
                [{"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 4}}],
                [
                    {"placeVisit": {"val": 5}},
                    {"activitySegment": {"activityType": "WALKING", "val": 6}},
                    {"placeVisit": {"val": 7}},
                    {"activitySegment": {"activityType": "WALKING", "val": 8}},
                    {"placeVisit": {"val": 9}},
                    {"activitySegment": {"activityType": "WALKING", "val": 10}},
                    {"placeVisit": {"val": 11}},
                    {"placeVisit": {"val": 12}},
                    {"activitySegment": {"activityType": "WALKING", "val": 13}},
                ],
            ],
            [
                [
                    {"placeVisit": {"val": 5}},
                    {"activitySegment": {"activityType": "WALKING", "val": 6}},
                    {"placeVisit": {"val": 7}},
                    {"activitySegment": {"activityType": "WALKING", "val": 8}},
                    {"placeVisit": {"val": 9}},
                    {"activitySegment": {"activityType": "WALKING", "val": 10}},
                    {"placeVisit": {"val": 11}},
                    {"placeVisit": {"val": 12}},
                    {"activitySegment": {"activityType": "WALKING", "val": 13}},
                ],
                [
                    {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 14}},
                    {"activitySegment": {"activityType": "WALKING", "val": 15}},
                ],
                [
                    {"placeVisit": {"val": 16}},
                    {"activitySegment": {"activityType": "WALKING", "val": 17}},
                    {"placeVisit": {"val": 18}},
                ],
            ],
            [
                [
                    {"placeVisit": {"val": 16}},
                    {"activitySegment": {"activityType": "WALKING", "val": 17}},
                    {"placeVisit": {"val": 18}},
                ],
                [{"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "val": 19}}],
                [
                    {"placeVisit": {"val": 20}},
                    {"activitySegment": {"activityType": "WALKING", "val": 21}},
                    {"placeVisit": {"val": 22}},
                ],
            ],
        ]
        self.assertEqual(expected, actual_bins)
