import json
import asyncio
import logging
from enum import Enum
from pathlib import Path
from typing import Generator, Tuple, Dict, List
from datetime import datetime, time
import pytz


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
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


def item_is_on_a_weekday(item: dict) -> bool:
    """
    Check if the item is on a weekday. Both start and end timestamps have to be on a weekday.

    Args:
        item (dict): The timeline object, which has a 'duration' key.

    Returns:
        bool: True if the item is on a weekday, False otherwise.
    """

    start = datetime.fromisoformat(item.get('duration', {}).get('startTimestamp', ''))
    end = datetime.fromisoformat(item.get('duration', {}).get('endTimestamp', ''))
    return start.weekday() < 5 and end.weekday() < 5


def is_within_time_range(item):
    """
    Time range is: Mon 06-18:30, Tue 06-18, Wed 06-22, Thu 06-14, Fri 06-16 local timezone.
    Duration timestamps given in UTC.

    Args:
        item (dict): The timeline object, which has a duration key.

    Returns:
        bool: True if the item is within the time range, False otherwise.
    """
    # Define the time ranges for each weekday
    days = {
        0: (time(6, 0), time(18, 30)),  # Monday
        1: (time(6, 0), time(18, 0)),   # Tuesday
        2: (time(6, 0), time(22, 0)),   # Wednesday
        3: (time(6, 0), time(14, 0)),   # Thursday
        4: (time(6, 0), time(16, 0))    # Friday
    }

    start_str = item.get('duration', {}).get('startTimestamp', '')
    end_str = item.get('duration', {}).get('endTimestamp', '')

    # Define the timezone
    timezone = pytz.timezone('Europe/Amsterdam')

    # Convert the timestamps to datetime objects with timezone awareness
    start = datetime.fromisoformat(start_str.replace("Z", "+00:00")).astimezone(timezone)
    end = datetime.fromisoformat(end_str.replace("Z", "+00:00")).astimezone(timezone)

    # Check if both start and end are on weekdays
    if start.weekday() < 5 and end.weekday() < 5:
        start_day = days[start.weekday()]
        end_day = days[end.weekday()]

        # Check if the times are within the allowed range
        if start_day[0] <= start.time() <= start_day[1] and end_day[0] <= end.time() <= end_day[1]:
            return True

    return False


def is_in_passenger_vehicle(activity_segment: dict) -> bool:
    """
    Check if the activity segment is in a passenger vehicle.

    Args:
        item (dict): The activity segment object.

    Returns:
        bool: True if the item has activityType with value 'in a passenger vehicle', False otherwise.
    """
    return activity_segment.get('activityType') == 'IN_PASSENGER_VEHICLE'


def meets_requirements(item: dict) -> bool:
    """
    Check if the activity segment meets the requirements.

    Requirements are:
    - The activity segment is in a passenger vehicle.
    - The activity segment is on a weekday.
    - TODO The activity segment is within the time range.

    Args:
        item (dict): The activity segment object.

    Returns:
        bool: True if the item meets the requirements, False otherwise.
    """
    activity_segment = item.get('activitySegment', {})
    return (is_in_passenger_vehicle(activity_segment) 
            and item_is_on_a_weekday(activity_segment)
            and is_within_time_range(activity_segment))


def is_place_visit(item: dict) -> bool:
    """
    Check if the item is a place visit.

    Args:
        item (dict): The timeline object.

    Returns:
        bool: True if the item is a place visit, False otherwise.
    """
    return 'placeVisit' in item and len(item) == 1


def is_activity_segment(item: dict) -> bool:
    """
    Check if the item is an activity segment.

    Args:
        item (dict): The timeline object.

    Returns:
        bool: True if the item is an activity segment, False otherwise.
    """
    return 'activitySegment' in item and len(item) == 1


async def find_next_activity_segment(generator: Generator) -> Tuple[Dict, Generator]:
    """
    Find the next activity segment after the current item. Skip (but log) any place visits.

    Args:
        current (dict): The current item.
        generator (Generator): The timeline object generator.

    Returns:
        Tuple[Dict, Generator]: The following activity segment and the updated generator.
    """
    try:
        next_item = next(generator)
    except StopIteration:
        raise StopAsyncIteration

    if is_activity_segment(next_item):
        return next_item, generator

    logger.debug(f"Next item is not an activitySegment, ignore: {next_item}")
    return await find_next_activity_segment(generator)


async def find_next_place_visit(generator: Generator) -> Tuple[Dict, Generator]:
    """
    Find the next place visit after the current item. Skip (but log) any activity segments.

    Args:
        current (dict): The current item.
        generator (Generator): The timeline object generator.

    Returns:
        Tuple[Dict, Generator]: The next place visit and the updated generator.
    """
    try:
        next_item = next(generator)
    except StopIteration:
        raise StopAsyncIteration

    if is_place_visit(next_item):
        return next_item, generator
    
    logger.debug(f"Next item is not a placeVisit, ignore: {next_item}")
    return await find_next_place_visit(generator)


async def get_segment(current_place_visit: dict, generator: Generator) -> Tuple[Dict, Dict, Generator]:
    """
    Get the segment data from the start place visit, following activity segment and then end place visit. If the 
    activity segment doesn't meet the requirements, the segment will be None.

    Args:
        current (dict): The current place visit object.
        generator (Generator): The timeline object generator.

    Returns:
        Tuple[Dict, Dict, Generator]: The end place visit (which serves as start for the next round), segment data 
        and the updated generator.
    """
    next_activity_segment, generator = await find_next_activity_segment(generator)
    end_place_visit, generator = await find_next_place_visit(generator)

    # current_place_visit, following_activity_segment and following_place_visit form a segment if the activity segment
    # meets the requirements
    if meets_requirements(next_activity_segment):
        startLocation = current_place_visit.get('placeVisit', {}).get('location', {})
        endLocation = end_place_visit.get('placeVisit', {}).get('location', {})
        activitySegment = next_activity_segment.get('activitySegment', {})
        segment = {
            'startLocation': {
                'address': startLocation.get('address', ''),
                'name': startLocation.get('name', ''),
                'latitudeE7': startLocation.get('latitudeE7', 0),
                'longitudeE7': startLocation.get('longitudeE7', 0)
            },
            'endLocation': {
                'address': endLocation.get('address', ''),
                'name': endLocation.get('name', ''),
                'latitudeE7': endLocation.get('latitudeE7', 0),
                'longitudeE7': endLocation.get('longitudeE7', 0)
            },
            'duration': activitySegment.get('duration', {}),
            'distance': activitySegment.get('distance', 0)
        }
    else:
        logger.debug(f"Activity segment doesn't meet the requirements, ignore: {next_activity_segment}")
        segment = None
    return end_place_visit, segment, generator


async def reduce_to_segment(initialiser: dict, generator: Generator) -> Tuple[Dict, Dict, Generator]:
    """
    Reduce a start place visit, activity segment and end place visit to a segment. This function is recursive and will 
    continue until a segment is found.
    A segment can be formed if the initialiser is a place visit, the following activity segment meets the requirements
    and the following place visit is found. The segment will be None if the activity segment doesn't meet the 
    requirements.

    Args:
        initialiser (dict): The initial timeline object.
        generator (Generator): The generator of timeline objects.

    Returns:
        Tuple[Dict, Dict, Generator]: A tuple containing the new place visit, the segment, and the updated generator.
    """
    if is_place_visit(initialiser):
        return await get_segment(initialiser, generator)
    else:
        logger.debug(f"Current item is not a place visit, ignore and continue until the next place visit: {initialiser}")
        next_place_visit, generator = await find_next_place_visit(generator)
        return await reduce_to_segment(next_place_visit, generator)


async def get_segments_from_timeline_files(path: Path, year: int=2023) -> List[Dict]:
    generator = get_timeline_object_generator(path, year)
    try:
        # get the initialiser
        item = next(generator)
    except StopIteration:
        logger.info("No timeline objects found, exiting")
        return

    segments = []    
    while True:
        try:
            item, segment, generator = await reduce_to_segment(initialiser=item, generator=generator)
            if segment:
                segments.append(segment)
        except StopAsyncIteration:
            logger.info("No more timeline objects found, exiting")
            break
    return segments


if __name__ == "__main__":
    my_path = Path('C:/Users/maitr/OneDrive/Documenten/Wil/Takeout/Locatiegeschiedenis (Tijdlijn)/Semantic Location History/')
    segments = asyncio.run(get_segments_from_timeline_files(my_path, 2024))
    if segments:
        with open('segments2024.json', 'a') as file:
            json.dump(segments, file, indent=2)

    # https://locationhistoryformat.com/reference/semantic/
    # https://www.andrewheiss.com/blog/2023/07/03/using-google-location-history-with-r-roadtrip/

    # 06:00 tot 19:00 op werkdagen, activiteit die bezig is of eerste die start/laatste die eindigt
    # bestand kan starten met een placeVisit of een activitySegment
    # laatste object van een file kan ook beide zijn en is degene die voor 0:00 startte, ook als die na 0:00 eindigde

    # start met de placevisit voorafgaand aan de activity
    # placeVisit.location.address, en latitudeE7 en longitudeE7
    # lees de activitySegment uit: .startLocation en endLocation beide de lat en longE7, deze komen overeen of bijna overeen
    # met die van de placeVisit. 
    # .duration.startTimestamp en endTimestamp nodig voor bepalen of dit wel of niet zakelijke rit was
    # .distance is de afstand in meters
    # activityType IN_PASSENGER_VEHICLE
    # dan de aansluitende placeVisit, deze is de eindlocatie van de activitySegment
    # dan de daaropvolgende activitySegment, etc tot de laatste activitySegment die nog gestart is voor 19h (?)

    # ma 6-22, di 6-18, woe 6-22, do 6-14, vr 6-16
    # start: ma 2/1
    # meivakantie: ma 29/4 t/m vr 3/5
    # bouwvak: ma 7/8 t/m vr 25/8
    # kerst: ma 25/12 t/m 31/12
    

    # trips = extract_trips(data)
    # for trip in trips:
    #     print(f"Start: {trip['start_time']}, End: {trip['end_time']}, Start Location: {trip['start_location']}, End Location: {trip['end_location']}, Distance: {trip['distance_km']} km")
