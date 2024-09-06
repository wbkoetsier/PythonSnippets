from unittest.mock import mock_open
from pathlib import Path

import pytest
from segments_timeline import (
    find_first_place_segment,
    get_timeline_object_generator,
    clean_timeline_object,
    is_place_visit,
    is_activity_segment,
    is_in_passenger_vehicle,
    is_on_a_weekday,
    make_bin,
    make_bins,
    make_segment,
    peek,
)


@pytest.fixture
def mock_path_exists(mocker):
    return mocker.patch("segments_timeline.Path.exists")


@pytest.fixture
def mock_file_open(mocker):
    return mocker.patch("builtins.open", mock_open(read_data='{"timelineObjects": [{"id": 1}, {"id": 2}]}'))


def test_clean_timeline_object_place_visit():
    item = {
        "placeVisit": {
            "location": {"latitudeE7": 123456789, "longitudeE7": 987654321},
            "duration": {"startTimestamp": "2023-01-01T12:00:00Z", "endTimestamp": "2023-01-01T12:30:00Z"},
            "otherKey": "should be removed",
        }
    }
    expected = {
        "placeVisit": {
            "location": {"latitudeE7": 123456789, "longitudeE7": 987654321},
            "duration": {"startTimestamp": "2023-01-01T12:00:00Z", "endTimestamp": "2023-01-01T12:30:00Z"},
        }
    }
    assert clean_timeline_object(item) == expected


def test_clean_timeline_object_activity_segment():
    item = {
        "activitySegment": {
            "startLocation": {"latitudeE7": 123456789, "longitudeE7": 987654321},
            "endLocation": {"latitudeE7": 123456789, "longitudeE7": 987654321},
            "distance": 1000,
            "activityType": "WALKING",
            "duration": {"startTimestamp": "2023-01-01T12:00:00Z", "endTimestamp": "2023-01-01T12:30:00Z"},
            "otherKey": "should be removed",
        }
    }
    expected = {
        "activitySegment": {
            "startLocation": {"latitudeE7": 123456789, "longitudeE7": 987654321},
            "endLocation": {"latitudeE7": 123456789, "longitudeE7": 987654321},
            "distance": 1000,
            "activityType": "WALKING",
            "duration": {"startTimestamp": "2023-01-01T12:00:00Z", "endTimestamp": "2023-01-01T12:30:00Z"},
        }
    }
    assert clean_timeline_object(item) == expected


def test_clean_timeline_object_no_place_visit_or_activity_segment():
    item = {"otherKey": "should raise error"}
    with pytest.raises(ValueError, match="No place visit or activity segment found in the timeline object."):
        clean_timeline_object(item)


def test_get_timeline_object_generator(mock_path_exists, mock_file_open):
    mock_path_exists.return_value = True
    expected = [{"id": 1}, {"id": 2}] * 12  # a file for each month
    assert expected == list(get_timeline_object_generator(Path("/a/path"), 1994))


def test_get_timeline_object_generator_file_not_found(mock_path_exists):
    mock_path_exists.return_value = False
    assert [] == list(get_timeline_object_generator(Path("/a/path"), 1993))

def test_is_place_visit():
    assert is_place_visit({'placeVisit': {}})
    assert not is_place_visit({'noPlaceVisit': {}})
    assert not is_place_visit({'placeVisit': {}, 'noPlaceVisit': {}})

def test_is_activity_segment():
    assert is_activity_segment({'activitySegment': {}})
    assert not is_activity_segment({'noActivitySegment': {}})
    assert not is_place_visit({'activitySegment': {}, 'noActivitySegment': {}})

def test_is_in_passenger_vehicle():
    assert is_in_passenger_vehicle({"activityType": "IN_PASSENGER_VEHICLE"})
    assert not is_in_passenger_vehicle({"activityType": "BLABLA"})
    assert not is_in_passenger_vehicle({"noActivityType": "BLABLA"})
    assert not is_in_passenger_vehicle({"noActivityType": "IN_PASSENGER_VEHICLE"})

def test_item_is_on_a_weekday():
    # a random week in July 2024, starting on a Monday
    for d in range(8, 13):
        assert is_on_a_weekday(
                {
                    "duration": {
                        "startTimestamp": f"2024-07-{d:02}T12:00:00.000Z",
                        "endTimestamp": f"2024-07-{d:02}T13:00:00.000Z",
                    }
                }
            )

def test_item_is_not_on_a_weekday():
    for d in range(13, 15):
        assert not is_on_a_weekday(
                {
                    "duration": {
                        "startTimestamp": f"2024-07-{d:02}T12:00:00.000Z",
                        "endTimestamp": f"2024-07-{d:02}T13:00:00.000Z",
                    }
                }
            )

def test_item_is_not_on_a_weekday_if_night_and_starts_or_ends_in_weekend():
    # and a night time situation
    assert not is_on_a_weekday(
            {"duration": {"startTimestamp": "2024-07-07T23:00:00.000Z", "endTimestamp": "2024-07-08T01:00:00.000Z"}}
        )
    assert not is_on_a_weekday(
            {"duration": {"startTimestamp": "2024-07-12T23:00:00.000Z", "endTimestamp": "2024-07-13T01:00:00.000Z"}}
        )

def test_peek():
    lst = [1, 2, 3, 4, 7]
    assert 7 == peek(lst, -1)
    assert 3 == peek(lst, -3)
    assert 1 == peek(lst, -5)
    assert 1 == peek(lst, 0)
    assert 7 == peek(lst, 4)
    assert None == peek(lst, 5)
    assert None == peek(lst, -6)

def test_make_segment_with_activity():
    obj_gen = (
        to
        for to in [
            {"activitySegment": {"activityType": "WALKING", "duration": 1}},
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 2}},
            {"activitySegment": {"activityType": "WALKING", "duration": 3}},
            {"placeVisit": {"duration": 4}},
        ]
    )

    current_obj, _, actual_segment = make_segment(next(obj_gen), obj_gen, [])

    assert {"placeVisit": {"duration": 4}} == current_obj
    assert [
            {"activitySegment": {"activityType": "WALKING", "duration": 1}},
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 2}},
            {"activitySegment": {"activityType": "WALKING", "duration": 3}},
        ] == actual_segment

def test_make_segment_with_address():
    obj_gen = (
        to
        for to in [
            {"placeVisit": {"duration": 1}},
            {"activitySegment": {"activityType": "WALKING", "duration": 2}},
            {"placeVisit": {"duration": 3}},
            {"activitySegment": {"activityType": "WALKING", "duration": 4}},
            {"placeVisit": {"duration": 5}},
            {"activitySegment": {"activityType": "WALKING", "duration": 6}},
            {"placeVisit": {"duration": 7}},
            {"placeVisit": {"duration": 8}},
            {"activitySegment": {"activityType": "WALKING", "duration": 9}},
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 10}},
            {"activitySegment": {"activityType": "WALKING", "duration": 11}},
            {"placeVisit": {"duration": 12}},
        ]
    )
    current_obj, _, actual_segment = make_segment(next(obj_gen), obj_gen, [])

    assert {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 10}} == current_obj
    assert [
            {"placeVisit": {"duration": 1}},
            {"activitySegment": {"activityType": "WALKING", "duration": 2}},
            {"placeVisit": {"duration": 3}},
            {"activitySegment": {"activityType": "WALKING", "duration": 4}},
            {"placeVisit": {"duration": 5}},
            {"activitySegment": {"activityType": "WALKING", "duration": 6}},
            {"placeVisit": {"duration": 7}},
            {"placeVisit": {"duration": 8}},
            {"activitySegment": {"activityType": "WALKING", "duration": 9}},
        ] == actual_segment

def test_make_bin():
    # bin is always place-segment, activity-segment, place-segment, first place-segment is the same as the last
    # place-segment of the previous bin
    # left segment should always be present
    obj_gen = (
        to
        for to in [
            # left p-segment
            {"placeVisit": {"duration": 3}},
            # a-segment
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 4}},
            # right p-segment
            {"placeVisit": {"duration": 5}},
            {"activitySegment": {"activityType": "WALKING", "duration": 6}},
            {"placeVisit": {"duration": 7}},
            {"activitySegment": {"activityType": "WALKING", "duration": 8}},
            {"placeVisit": {"duration": 9}},
            {"activitySegment": {"activityType": "WALKING", "duration": 10}},
            {"placeVisit": {"duration": 11}},
            {"placeVisit": {"duration": 12}},
            {"activitySegment": {"activityType": "WALKING", "duration": 13}},
            # start next a-segment, should not be in the bin, current object should be 14
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 14}},
            {"activitySegment": {"activityType": "WALKING", "duration": 15}},
            {"placeVisit": {"duration": 16}},
        ]
    )

    # first bin, so manually create the left segment and set the generator head to the next object (a with value 4)
    bin_left_seg = next(obj_gen)

    current_obj, _, actual_bin = make_bin(next(obj_gen), obj_gen, [[bin_left_seg]])  # bin is list of lists

    assert {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 14}} == current_obj
    assert 3 == len(actual_bin)
    assert [
            [{"placeVisit": {"duration": 3}}],
            [{"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 4}}],
            [
                {"placeVisit": {"duration": 5}},
                {"activitySegment": {"activityType": "WALKING", "duration": 6}},
                {"placeVisit": {"duration": 7}},
                {"activitySegment": {"activityType": "WALKING", "duration": 8}},
                {"placeVisit": {"duration": 9}},
                {"activitySegment": {"activityType": "WALKING", "duration": 10}},
                {"placeVisit": {"duration": 11}},
                {"placeVisit": {"duration": 12}},
                {"activitySegment": {"activityType": "WALKING", "duration": 13}},
            ],
        ] == actual_bin

def test_make_last_bin():
    # the last bin could be incomplete
    obj_gen = (
        to
        for to in [
            # left p-segment
            {"placeVisit": {"duration": 1}},
            # a-segment
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 2}},
            # and that's it
        ]
    )

    # manually create first bin with left segment, which is just the first object in this case
    bin_left_seg = next(obj_gen)
    current_obj, obj_gen, actual_bin = make_bin(next(obj_gen), obj_gen, [[bin_left_seg]])  # bin is list of lists

    assert None == current_obj
    assert 2 == len(actual_bin)
    with pytest.raises(StopIteration):
        next(obj_gen)
    assert [
            [{"placeVisit": {"duration": 1}}],
            [{"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 2}}],
        ] == actual_bin

def test_find_first_place_segment():
    obj_gen = (
        to
        for to in [
            # first segment is activity
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 1}},
            # second segment is place
            {"placeVisit": {"duration": 2}},
            # first object of the next segment (activity)
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 3}},
        ]
    )
    current_obj, segment, obj_gen = find_first_place_segment(next(obj_gen), obj_gen)
    # segment is place segment
    assert any("placeVisit" in obj for obj in segment)
    # last object to have been yielded from the generator is the first object of the next segment
    assert {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 3}} == current_obj
    # so the generator should now be empty
    with pytest.raises(StopIteration):
        next(obj_gen)


def test_make_bins():
    obj_gen = (
        to
        for to in [
            # first objects excluded from any bin
            {"activitySegment": {"activityType": "WALKING", "duration": 1}},
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 2}},
            # start p-segment, bin 1 ('home')
            {"placeVisit": {"duration": 3}},
            # start a-segment, bin 1 ('drive')
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 4}},
            # start p-segment, bin 1 & 2 ('customer 1')
            {"placeVisit": {"duration": 5}},
            {"activitySegment": {"activityType": "WALKING", "duration": 6}},
            {"placeVisit": {"duration": 7}},
            {"activitySegment": {"activityType": "WALKING", "duration": 8}},
            {"placeVisit": {"duration": 9}},
            {"activitySegment": {"activityType": "WALKING", "duration": 10}},
            {"placeVisit": {"duration": 11}},
            {"placeVisit": {"duration": 12}},
            {"activitySegment": {"activityType": "WALKING", "duration": 13}},
            # start a-segment, bin 2 ('drive')
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 14}},
            {"activitySegment": {"activityType": "WALKING", "duration": 15}},
            # start p-segment, bin 2 & 3 ('home')
            {"placeVisit": {"duration": 16}},
            {"activitySegment": {"activityType": "WALKING", "duration": 17}},
            {"placeVisit": {"duration": 18}},
            # start a-segment, bin 3 ('drive')
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 19}},
            # start p-segment, bin 3 (& 4 fwiw) ('customer 2')
            {"placeVisit": {"duration": 20}},
            {"activitySegment": {"activityType": "WALKING", "duration": 21}},
            {"placeVisit": {"duration": 22}},
            # start a-segment, bin 4, incomplete bin
            {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 23}},
        ]
    )

    actual_bins = make_bins(next(obj_gen), [], obj_gen, [])

    # the first and last bins aren't included, bc they're both incomplete
    assert 3 == len(actual_bins)
    assert {"placeVisit": {"duration": 3}} == actual_bins[0][0][0]
    assert {"placeVisit": {"duration": 22}} == actual_bins[-1][-1][-1]
    # generator should now be empty
    with pytest.raises(StopIteration):
        next(obj_gen)
    # but, yk, just to be sure
    assert [
        [
            [{"placeVisit": {"duration": 3}}],
            [{"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 4}}],
            [
                {"placeVisit": {"duration": 5}},
                {"activitySegment": {"activityType": "WALKING", "duration": 6}},
                {"placeVisit": {"duration": 7}},
                {"activitySegment": {"activityType": "WALKING", "duration": 8}},
                {"placeVisit": {"duration": 9}},
                {"activitySegment": {"activityType": "WALKING", "duration": 10}},
                {"placeVisit": {"duration": 11}},
                {"placeVisit": {"duration": 12}},
                {"activitySegment": {"activityType": "WALKING", "duration": 13}},
            ],
        ],
        [
            [
                {"placeVisit": {"duration": 5}},
                {"activitySegment": {"activityType": "WALKING", "duration": 6}},
                {"placeVisit": {"duration": 7}},
                {"activitySegment": {"activityType": "WALKING", "duration": 8}},
                {"placeVisit": {"duration": 9}},
                {"activitySegment": {"activityType": "WALKING", "duration": 10}},
                {"placeVisit": {"duration": 11}},
                {"placeVisit": {"duration": 12}},
                {"activitySegment": {"activityType": "WALKING", "duration": 13}},
            ],
            [
                {"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 14}},
                {"activitySegment": {"activityType": "WALKING", "duration": 15}},
            ],
            [
                {"placeVisit": {"duration": 16}},
                {"activitySegment": {"activityType": "WALKING", "duration": 17}},
                {"placeVisit": {"duration": 18}},
            ],
        ],
        [
            [
                {"placeVisit": {"duration": 16}},
                {"activitySegment": {"activityType": "WALKING", "duration": 17}},
                {"placeVisit": {"duration": 18}},
            ],
            [{"activitySegment": {"activityType": "IN_PASSENGER_VEHICLE", "duration": 19}}],
            [
                {"placeVisit": {"duration": 20}},
                {"activitySegment": {"activityType": "WALKING", "duration": 21}},
                {"placeVisit": {"duration": 22}},
            ],
        ],
    ] == actual_bins
