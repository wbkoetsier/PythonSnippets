import csv
import logging
import os
from typing import Generator, List, Tuple, Union
import json
import logging
from enum import Enum
from pathlib import Path
from datetime import datetime, time
from pytz import timezone


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Define month names
class Month(Enum):
    JANUARY = 'JANUARY'
    FEBRUARY = 'FEBRUARY'
    MARCH = 'MARCH'
    APRIL = 'APRIL'
    MAY = 'MAY'
    JUNE = 'JUNE'
    JULY = 'JULY'
    AUGUST = 'AUGUST'
    SEPTEMBER = 'SEPTEMBER'
    OCTOBER = 'OCTOBER'
    NOVEMBER = 'NOVEMBER'
    DECEMBER = 'DECEMBER'


TZ_AMS = timezone('Europe/Amsterdam')


def filter_keys(source: dict, keys: list) -> dict:
    """
    Filter the unwanted keys from the source dict.
    :param source: The source dict.
    :param keys: The keys that should remain in the dict.
    :return: The filtered dict.
    """
    return {key: source[key] for key in keys if key in source}


def timeline_object_hook(obj: dict) -> dict:
    """
    Hook to clean the timeline objects by removing unnecessary keys and converting the string timestamps to datetime
    using the local timezone.
    :param obj: The timeline object.
    :return: The cleaned timeline object.
    """
    if is_place_visit(obj):
        return {"placeVisit": filter_keys(obj.get("placeVisit"), ['location', 'duration'])}
    if is_activity_segment(obj):
        return {
            "activitySegment": filter_keys(
                obj.get("activitySegment"), ['startLocation', 'endLocation', 'distance', 'activityType', 'duration']
            )
        }
    if "duration" in obj:
        obj["duration"]["startTimestamp"] = datetime.fromisoformat(obj["duration"]["startTimestamp"]).astimezone(TZ_AMS)
        obj["duration"]["endTimestamp"] = datetime.fromisoformat(obj["duration"]["endTimestamp"]).astimezone(TZ_AMS)
    return obj


def get_timeline_object_generator(path_to_folder: Path, year: int = 2023) -> Generator:
    """
    Generator function that yields each timeline object from each month in the given year from the Semantic Location
    History.

    Args:
        path_to_folder (Path): Path to the Semantic Location History folder.
        year (int): Optional year to extract the timeline objects from, defaults to 2023.

    Yields:
        dict: Each timeline object from the JSON files for the given year.
    """
    for month in Month:
        file_path = path_to_folder / f"{year}/{year}_{month.value}.json"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}, skipping {month.value} for {year}")
        else:
            logger.info(f"Reading JSON file from: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file, object_hook=timeline_object_hook)
            yield from (item for item in data['timelineObjects'])


def is_in_passenger_vehicle(activity_segment: dict) -> bool:
    """
    Check if the activity segment is in a passenger vehicle.

    Args:
        item (dict): The activity segment object.

    Returns:
        bool: True if the item has activityType with value 'in a passenger vehicle', False otherwise.
    """
    return activity_segment.get('activityType') == 'IN_PASSENGER_VEHICLE'


def is_place_visit(item: dict) -> bool:
    """
    Check if the item is a place visit timeline_object. It is if the item has one key, which is 'placeVisit'.

    Args:
        item (dict): The timeline object.

    Returns:
        bool: True if the item is a place visit, False otherwise.
    """
    return 'placeVisit' in item and len(item) == 1


def is_activity_segment(item: dict) -> bool:
    """
    Check if the item is an activity segment timeline_object. It is if the item has one key, which is 'activitySegment'.

    Args:
        item (dict): The timeline object.

    Returns:
        bool: True if the item is an activity segment, False otherwise.
    """
    return 'activitySegment' in item and len(item) == 1


def peek(lst, idx):
    """
    Peek at the list at the given index, return None if the index is out of bounds.

    :param lst: The list to peek at.
    :param idx: The index to peek at.
    :return: The item at the given index, or None if the index is out of bounds.
    """
    if not lst:
        return None
    try:
        return lst[idx]
    except IndexError:
        return None


def is_drive(item: dict) -> bool:
    return is_activity_segment(item) and is_in_passenger_vehicle(item["activitySegment"])


def is_not_drive(item: dict) -> bool:
    # not the same as not is_drive ;-)
    return is_activity_segment(item) and not is_in_passenger_vehicle(item["activitySegment"])


def peek(lst, idx):
    if not lst:
        return None
    try:
        return lst[idx]
    except IndexError:
        return None


def make_segment(current_obj, gen, segment) -> Tuple[dict, Generator, list]:
    """
    Create an activity or place segment. A segment is a list of timeline objects.

    :param current_obj: The current timeline object to add to the segment.
    :param gen: The generator to get the next timeline object from.
    :param segment: The current segment being built.
    :return: The next timeline object, the generator, and the segment.
    """
    logger.info(f"make_segment: current object: {current_obj}")
    idx = -1
    while True:
        previous_obj = peek(segment, idx)
        logger.debug(f"make_segment[checking boundaries]: Current object: {current_obj}")
        logger.debug(f"make_segment[checking boundaries]: previous object: {previous_obj} (at index {idx})")
        if previous_obj:
            if is_drive(previous_obj) and is_place_visit(current_obj):
                logger.debug("make_segment[checking boundaries]: Boundary a -> p, return segment")
                return current_obj, gen, segment
            elif is_place_visit(previous_obj) and is_drive(current_obj):
                logger.debug("make_segment[checking boundaries]: Boundary p -> a, return segment")
                return current_obj, gen, segment
            elif is_not_drive(previous_obj) and is_place_visit(current_obj):
                logger.debug("make_segment[checking boundaries]: Possible boundary a -> p, check previous object")
                idx -= 1
            elif is_not_drive(previous_obj) and is_drive(current_obj):
                logger.debug("make_segment[checking boundaries]: Possible boundary p -> a, check previous object")
                idx -= 1
            else:
                logger.debug("make_segment[checking boundaries]: Not a boundary, continue")
                break
        else:
            logger.debug("make_segment[checking boundaries]: No previous object found, not a boundary, continue")
            break

    logger.info("make_segment: add current object to segment")
    segment.append(current_obj)
    try:
        nxt_obj = next(gen)
    except StopIteration:
        logger.info("No more objects found, return segment")
        # return current_obj, gen, segment
        return None, gen, segment
    logger.info("make_segment: repeat with next object")
    return make_segment(nxt_obj, gen, segment)


def make_bin(current_obj, gen, current_bin) -> Tuple[dict, Generator, List[list]]:
    """
    Create a bin. A complete bin has three segments: a place segment, an activity segment, and a place segment.
    The left segment should be the same as the right segment of the previous bin.
    The current object is the leftmost object in the next segment.

    :param current_obj: The last timeline object to have been taken from the generator
    :param gen: The generator to get the next timeline object from
    :param current_bin: The current bin being built
    :return: The next timeline object, the generator, and the bin
    """
    logger.info(f"make_bin: current object: {current_obj}")
    logger.info(f"make_bin: bin length: {len(current_bin)}")
    logger.debug(f"make_bin: bin: {current_bin}")
    if not current_obj:
        logger.info("make_bin: there are no more objects, return")
        return current_obj, gen, current_bin
    if len(current_bin) == 3:
        logger.info("make_bin: bin is complete, return")
        return current_obj, gen, current_bin
    logger.info("make_bin: make_segment and add to bin")
    current_obj, gen, segment = make_segment(current_obj, gen, [])
    logger.debug(f"make_bin: add segment to bin: {segment}")
    current_bin.append(segment)
    logger.debug("make_bin: next round making bin")
    return make_bin(current_obj, gen, current_bin)


def find_first_place_segment(first_object, gen) -> Tuple[dict, List[dict], Generator]:
    logger.info("find_first_place_segment: find the first place-segment in this generator")
    current_obj, gen, segment = make_segment(first_object, gen, [])
    if any(is_place_visit(obj) for obj in segment):
        logger.info("find_first_place_segment: found first place-segment, return")
        return current_obj, segment, gen
    else:
        logger.info("find_first_place_segment: first segment is not a place-segment, next one should be")
        return find_first_place_segment(current_obj, gen)


def is_in_date_range(datetime_obj: datetime) -> bool:
    holidays = [
        (datetime(2023, 5, 1).astimezone(TZ_AMS), datetime(2023, 5, 5).astimezone(TZ_AMS)),  # meivakantie
        (datetime(2023, 8, 7).astimezone(TZ_AMS), datetime(2023, 8, 25).astimezone(TZ_AMS)),  # bouwvak
        (datetime(2023, 12, 25).astimezone(TZ_AMS), datetime(2023, 12, 31).astimezone(TZ_AMS)),  # kerst
    ]
    for holiday_start, holiday_end in holidays:
        if holiday_start <= datetime_obj <= holiday_end:
            return False
    return True


def is_in_time_range(datetime_obj: datetime) -> bool:
    # Define the time ranges in local time
    time_ranges = {
        0: (time(6, 0), time(22, 0)),  # ma
        1: (time(6, 0), time(18, 0)),  # di
        2: (time(6, 0), time(22, 0)),  # woe
        3: (time(6, 0), time(14, 0)),  # do
        4: (time(6, 0), time(16, 0)),  # vr
    }
    day = datetime_obj.weekday()
    if day < 5:
        return time_ranges[day][0] <= datetime_obj.time() <= time_ranges[day][1]
    # it's not on a weekday anyway
    return False


def get_duration_from_timeline_object(timeline_object: dict) -> dict:
    for _, dct in timeline_object.items():
        if "duration" in dct:
            return dct["duration"]
    return {}


def bin_is_in_date_day_time_range(bin: list) -> bool:
    """
    Check if the bin is within the date, day and time range.

    Resolves to true if the journey segment in this bin is within the range. It is, if the start and/or end time of
    that journey (which may consist of several timeline objects) is within the date, day and time range.

    Date range: outside holidays
    Day range: weekdays
    Time range: weekday 'office hours'

    :param bin: The bin to check.
    :return: True if the bin is within the date/ day/ time range, False otherwise.
    """
    # the journey segment is the 2nd segment in the bin
    segment = bin[1]
    journey_start = get_duration_from_timeline_object(segment[0]).get("startTimestamp")
    journey_end = get_duration_from_timeline_object(segment[-1]).get("endTimestamp")
    return (is_in_date_range(journey_start) and is_in_time_range(journey_start)) or (
        is_in_date_range(journey_end) and is_in_time_range(journey_end)
    )


def make_bins(current_obj, current_bin, gen, bins) -> List[list]:
    """
    Organizes segments into bins, ensuring each bin starts with the last segment of the previous bin.
    This function processes segments and groups them into bins. The first bin is created manually
    with the first place segment. Each subsequent bin starts with the last segment of the previous bin.
    If the last bin is incomplete (contains fewer than 3 segments), it is removed before returning the bins.

    Each bin is accepted only if it is within the date/time range.
    TODO: make the date/time range configurable.

    In the end, a bin is a journey: a start address (place / address segment), a journey (driving segment), and an end
    address (place / address segment).

    :param current_obj: The current object being processed.
    :param current_bin: The current bin being filled with segments.
    :param gen: A generator that yields segments.
    :param bins: A list of bins, where each bin is a list of segments.
    :return: A list of bins, where each bin is a list of segments.
    """
    if not bins:
        logger.info("make_bins: manually create first bin with first place segment")
        # find the left segment of the first bin, which has to be a place-segment
        current_obj, segment, gen = find_first_place_segment(current_obj, gen)
        # the bin is a list of lists, the first item is the segment
        current_obj, gen, current_bin = make_bin(current_obj, gen, [segment])
        # only accept this bin if it is within the date/time range
        if bin_is_in_date_day_time_range(current_bin):
            bins.append(current_bin)
        logger.info("make_bins: start making bins")

    logger.debug(f"make_bins: current object: {current_obj}")
    logger.debug(f"make_bins: current bin: {current_bin}")

    while current_obj:
        # each new bin has the last segment of the previous bin as first segment
        current_obj, gen, current_bin = make_bin(current_obj, gen, [current_bin[-1]])
        # only accept this bin if it is within the date/time range
        if bin_is_in_date_day_time_range(current_bin):
            bins.append(current_bin)

    logger.info("make_bins: no more objects found, return bins w/o adding last incomplete bin")
    if len(bins[-1]) < 3:
        logger.info("make_bins: last bin is incomplete, remove it")
        bins.pop()
    return bins


def extract_row(bin: dict) -> dict:
    """
    Extract the row data from the bin.

    :param bin: The bin to extract the row data from.
    :return: The row data.
    """
    row = {}
    # het adres van de startlocatie is het adres van de laatste placeVisit
    for item in reversed(bin[0]):
        if is_place_visit(item):
            location = item["placeVisit"].get("location", {})
            break
    row["start_location_name"] = location.get("name", "")
    row["start_location_address"] = location.get("address", "")

    # de reis is het totaal van alle auto-activiteiten
    segment = bin[1]
    # start is van de eerste activitySegment
    row["activity_start"] = segment[0]["activitySegment"].get("duration", {}).get("startTimestamp", "")
    # eind is van de laatste activitySegment
    row["activity_end"] = segment[-1]["activitySegment"].get("duration", {}).get("endTimestamp", "")
    # afstand is de som van alle activitySegments
    row["distance"] = sum(item["activitySegment"].get("distance", 0) for item in segment)

    # het adres van de eindlocatie is het adres van de eerste placeVisit
    for item in bin[2]:
        if is_place_visit(item):
            location = item["placeVisit"].get("location", {})
            break
    row["end_location_name"] = location.get("name", "")
    row["end_location_address"] = location.get("address", "")

    return row


def main(gen):
    start = datetime.now()
    try:
        first_obj = next(gen)
    except StopIteration:
        logger.error("No objects found, so no bins created")
        return []
    bins = make_bins(current_obj=first_obj, current_bin=[], gen=gen, bins=[])
    logger.info(f"Found {len(bins)} bins")
    logger.info(f"Execution time finding bins: {datetime.now() - start}")

    # Dump raw bins to json file
    with open('bins.json', 'w', encoding='utf-8') as file:
        json.dump(bins, file)

    # write as csv
    with open('bins.csv', 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=';')

        # Write the header
        header = {
            "start_location_name": "Startlocatie Naam",
            "start_location_address": "Startlocatie Adres",
            "activity_start": "Begintijd reis",
            "activity_end": "Eindtijd reis",
            "distance": "Afstand in m",
            "end_location_name": "Eindlocatie Naam",
            "end_location_address": "Eindlocatie Adres",
        }
        csv_writer.writerow(
            [
                header["start_location_name"],
                header["start_location_address"],
                header["activity_start"],
                header["activity_end"],
                header["distance"],
                header["end_location_name"],
                header["end_location_address"],
            ]
        )

        # Write the data
        for bin in bins:
            row = extract_row(bin)
            csv_writer.writerow(
                [
                    row["start_location_name"],
                    row["start_location_address"],
                    row["activity_start"],
                    row["activity_end"],
                    row["distance"],
                    row["end_location_name"],
                    row["end_location_address"],
                ]
            )
    logger.info("Bins written to bins.csv")


if __name__ == "__main__":
    pth = Path(
        os.path.expanduser('~'),
        'OneDrive',
        'Documenten',
        'Wil',
        'Takeout',
        'Locatiegeschiedenis (Tijdlijn)',
        'Semantic Location History',
    )

    gen = get_timeline_object_generator(pth, 2023)
    main(gen)
