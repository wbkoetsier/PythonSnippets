from datetime import datetime
from unittest.mock import mock_open, patch
from pathlib import Path

import pytest
from segments_timeline import (
    TZ_AMS,
    find_first_place_segment,
    get_timeline_object_generator,
    filter_keys,
    timeline_object_hook,
    get_duration_from_timeline_object,
    is_place_visit,
    is_activity_segment,
    is_in_passenger_vehicle,
    bin_is_in_date_day_time_range,
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


def test_filter_keys():
    assert filter_keys(
        {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        },
        ["key1", "key3"],
    ) == {"key1": "value1", "key3": "value3"}


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
    assert timeline_object_hook(item) == expected


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
    assert timeline_object_hook(item) == expected


def test_clean_duration():
    item = {"duration": {"startTimestamp": "2023-01-01T12:00:00Z", "endTimestamp": "2023-01-01T12:30:00Z"}}
    expected = {
        "duration": {
            "startTimestamp": datetime(2023, 1, 1, 13, 0, 0).astimezone(TZ_AMS),
            "endTimestamp": datetime(2023, 1, 1, 13, 30, 0).astimezone(TZ_AMS),
        }
    }
    assert timeline_object_hook(item) == expected


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


def test_bin_is_in_date_day_time_range():
    journey = [  # journey starts and ends on a Monday outside holiday inside office hours
        {
            "placeVisit": {
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 12, 0, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 12, 30, 0, tzinfo=TZ_AMS),
                }
            }
        },
        {
            "activitySegment": {
                "activityType": "WALKING",
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 12, 30, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 13, 0, 0, tzinfo=TZ_AMS),
                },
            }
        },
        {
            "placeVisit": {
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 13, 0, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 13, 30, 0, tzinfo=TZ_AMS),
                }
            }
        },
    ]
    bin = ["first segment", journey, "third segment"]
    assert bin_is_in_date_day_time_range(bin)


def test_bin_starts_in_range_ends_outside_range():
    journey = [  # journey starts a Monday outside holiday inside office hours, but ends outside office hours
        {
            "placeVisit": {
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 12, 0, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 12, 30, 0, tzinfo=TZ_AMS),
                }
            }
        },
        {
            "activitySegment": {
                "activityType": "WALKING",
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 12, 30, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 13, 0, 0, tzinfo=TZ_AMS),
                },
            }
        },
        {
            "placeVisit": {
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 13, 0, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 23, 30, 0, tzinfo=TZ_AMS),
                }
            }
        },
    ]
    bin = ["first segment", journey, "third segment"]
    assert bin_is_in_date_day_time_range(bin)


def test_bin_starts_outside_range_ends_in_range():
    journey = [
        {
            "placeVisit": {
                "duration": {
                    "startTimestamp": datetime(2023, 5, 13, 12, 0, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 12, 30, 0, tzinfo=TZ_AMS),
                }
            }
        },
        {
            "activitySegment": {
                "activityType": "WALKING",
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 12, 30, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 13, 0, 0, tzinfo=TZ_AMS),
                },
            }
        },
        {
            "placeVisit": {
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 13, 0, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 13, 30, 0, tzinfo=TZ_AMS),
                }
            }
        },
    ]
    bin = ["first segment", journey, "third segment"]
    assert bin_is_in_date_day_time_range(bin)


def test_bin_is_not_in_date_day_time_range():
    journey = [
        {
            "placeVisit": {
                "duration": {
                    "startTimestamp": datetime(2023, 5, 13, 12, 0, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 12, 30, 0, tzinfo=TZ_AMS),
                }
            }
        },
        {
            "activitySegment": {
                "activityType": "WALKING",
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 12, 30, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 15, 13, 0, 0, tzinfo=TZ_AMS),
                },
            }
        },
        {
            "placeVisit": {
                "duration": {
                    "startTimestamp": datetime(2023, 5, 15, 13, 0, 0, tzinfo=TZ_AMS),
                    "endTimestamp": datetime(2023, 5, 13, 13, 30, 0, tzinfo=TZ_AMS),
                }
            }
        },
    ]
    bin = ["first segment", journey, "third segment"]
    assert not bin_is_in_date_day_time_range(bin)


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
            {
                "activitySegment": {
                    "activityType": "WALKING",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 1, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 1, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            {
                "activitySegment": {
                    "activityType": "IN_PASSENGER_VEHICLE",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 2, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 2, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            # start p-segment, bin 1 ('home')
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 5, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 5, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            # start a-segment, bin 1 ('drive')
            {
                "activitySegment": {
                    "activityType": "IN_PASSENGER_VEHICLE",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 6, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 6, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            # start p-segment, bin 1 & 2 ('customer 1')
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 7, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 7, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            {
                "activitySegment": {
                    "activityType": "WALKING",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 8, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 8, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 9, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 9, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            {
                "activitySegment": {
                    "activityType": "WALKING",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 12, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 12, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 13, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 13, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            {
                "activitySegment": {
                    "activityType": "WALKING",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 14, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 14, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 15, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 15, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 16, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 16, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            {
                "activitySegment": {
                    "activityType": "WALKING",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 19, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 19, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            # start a-segment, bin 2 ('drive')
            {
                "activitySegment": {
                    "activityType": "IN_PASSENGER_VEHICLE",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 20, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 20, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            {
                "activitySegment": {
                    "activityType": "WALKING",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 21, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 21, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            # start p-segment, bin 2 & 3 ('home')
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 22, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 22, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            {
                "activitySegment": {
                    "activityType": "WALKING",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 23, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 23, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 26, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 26, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            # start a-segment, bin 3 ('drive')
            {
                "activitySegment": {
                    "activityType": "IN_PASSENGER_VEHICLE",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 27, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 27, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            # start p-segment, bin 3 (& 4 fwiw) ('customer 2')
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 28, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 28, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            {
                "activitySegment": {
                    "activityType": "WALKING",
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 29, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 29, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
            {
                "placeVisit": {
                    "duration": {
                        "startTimestamp": datetime(2023, 6, 30, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 6, 30, 12, 30, 0).astimezone(TZ_AMS),
                    }
                }
            },
            # start a-segment, bin 4, incomplete bin
            {
                "activitySegment": {
                    "activityType": "IN_PASSENGER_VEHICLE",
                    "duration": {
                        "startTimestamp": datetime(2023, 7, 3, 12, 0, 0).astimezone(TZ_AMS),
                        "endTimestamp": datetime(2023, 7, 3, 12, 30, 0).astimezone(TZ_AMS),
                    },
                }
            },
        ]
    )

    actual_bins = make_bins(next(obj_gen), [], obj_gen, [])

    # the first and last bins aren't included, bc they're both incomplete
    assert 3 == len(actual_bins)
    assert get_duration_from_timeline_object(actual_bins[0][0][0]).get("startTimestamp") == datetime(
        2023, 6, 5, 12, 0, 0
    ).astimezone(TZ_AMS)
    assert get_duration_from_timeline_object(actual_bins[-1][-1][-1]).get("startTimestamp") == datetime(
        2023, 6, 30, 12, 0, 0
    ).astimezone(TZ_AMS)
    # generator should now be empty
    with pytest.raises(StopIteration):
        next(obj_gen)
    # but, yk, just to be sure
    assert actual_bins == [
        [
            [
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 5, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 5, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                }
            ],
            [
                {
                    "activitySegment": {
                        "activityType": "IN_PASSENGER_VEHICLE",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 6, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 6, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                }
            ],
            [
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 7, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 7, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 8, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 8, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 9, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 9, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 12, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 12, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 13, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 13, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 14, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 14, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 15, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 15, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 16, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 16, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 19, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 19, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
            ],
        ],
        [
            [
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 7, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 7, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 8, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 8, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 9, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 9, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 12, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 12, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 13, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 13, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 14, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 14, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 15, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 15, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 16, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 16, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 19, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 19, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
            ],
            [
                {
                    "activitySegment": {
                        "activityType": "IN_PASSENGER_VEHICLE",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 20, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 20, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 21, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 21, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
            ],
            [
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 22, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 22, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 23, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 23, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 26, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 26, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
            ],
        ],
        [
            [
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 22, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 22, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 23, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 23, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 26, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 26, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
            ],
            [
                {
                    "activitySegment": {
                        "activityType": "IN_PASSENGER_VEHICLE",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 27, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 27, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                }
            ],
            [
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 28, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 28, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
                {
                    "activitySegment": {
                        "activityType": "WALKING",
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 29, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 29, 12, 30, 0).astimezone(TZ_AMS),
                        },
                    }
                },
                {
                    "placeVisit": {
                        "duration": {
                            "startTimestamp": datetime(2023, 6, 30, 12, 0, 0).astimezone(TZ_AMS),
                            "endTimestamp": datetime(2023, 6, 30, 12, 30, 0).astimezone(TZ_AMS),
                        }
                    }
                },
            ],
        ],
    ]
