import logging
import os
from typing import Generator, List, Tuple, Union
import json
import logging
from enum import Enum
from pathlib import Path
from datetime import datetime, time


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
                data = json.load(file)
            yield from (item for item in data['timelineObjects'])


def clean_timeline_object(item: dict) -> dict:
    """
    Clean the timeline object by removing unnecessary keys.
    """
    place_visit = item.get('placeVisit')
    activity_segment = item.get('activitySegment')
    item = {} # todo dit kan mooier
    if place_visit:
        obj = {}
        for key in place_visit.keys():
            if key in ['location', 'duration']:
                obj[key] = place_visit.get(key)
        item["placeVisit"] = obj
        return item
    elif activity_segment:
        obj = {}
        for key in activity_segment.keys():
            if key in ["startLocation", "endLocation", "distance", 'activityType', 'duration']:
                obj[key] = activity_segment.get(key)
        item["activitySegment"] = obj
        return item
    raise ValueError("No place visit or activity segment found in the timeline object.")


def is_on_a_weekday(timeline_object: dict) -> bool:
    """
    Check if the timeline object is on a weekday. Both start and end timestamps have to be on a weekday.

    Args:
        timeline_object (dict): The timeline object, which has a 'duration' key.

    Returns:
        bool: True if the item is on a weekday, False otherwise.
    """

    start = datetime.fromisoformat(timeline_object.get('duration', {}).get('startTimestamp', ''))
    end = datetime.fromisoformat(timeline_object.get('duration', {}).get('endTimestamp', ''))
    return start.weekday() < 5 and end.weekday() < 5


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
    Create an activity or place segment.

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
        nxt_obj = clean_timeline_object(nxt_obj)
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


def make_bins(current_obj, current_bin, gen, bins) -> List[list]:
    if not bins:
        logger.info("make_bins: manually create first bin with first place segment")
        # find the left segment of the first bin, which has to be a place-segment
        current_obj, segment, gen = find_first_place_segment(current_obj, gen)
        # the bin is a list of lists, the first item is the segment
        current_obj, gen, current_bin = make_bin(current_obj, gen, [segment])
        bins.append(current_bin)
        logger.info("make_bins: start making bins")

    logger.debug(f"make_bins: current object: {current_obj}")
    logger.debug(f"make_bins: current bin: {current_bin}")

    while current_obj:
        # each new bin has the last segment of the previous bin as first segment
        current_obj, gen, current_bin = make_bin(current_obj, gen, [current_bin[-1]])
        bins.append(current_bin)

    logger.info("make_bins: no more objects found, return bins w/o adding last incomplete bin")
    if len(bins[-1]) < 3:
        logger.info("make_bins: last bin is incomplete, remove it")
        bins.pop()
    return bins


def main(gen):
    try:
        first_obj = next(gen)
        first_obj = clean_timeline_object(first_obj)
    except StopIteration:
        logger.error("No objects found, so no bins created")
        return []
    bins = make_bins(current_obj=first_obj, current_bin=[], gen=gen, bins=[])

    # Write bins to file
    with open('bins.json', 'w') as file:
        json.dump(bins, file)

if __name__ == "__main__":
    pth = Path(os.path.expanduser('~'), 'OneDrive', 'Documenten', 'Wil', 'Takeout', 'Locatiegeschiedenis (Tijdlijn)', 'Semantic Location History')

    gen = get_timeline_object_generator(pth, 2023)
    main(gen)