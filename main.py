from io import BytesIO
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal
from unicodedata import normalize
from ics import Calendar, Event
from ics.parse import ContentLine
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta, WE, TU, SA, TH
from zoneinfo import ZoneInfo
import pandas as pd
import re

timezone = ZoneInfo("US/Central")
types = {
    "DIS": "Discussion",
    "LEC": "Lecture",
    "LAB": "Lab"
}


def toiCal(pdf):
    """
    This method creates an ics file based off of a UW course schedule pdf
    :param pdf: either a string path to the file, or a BytesIO object containing the file
    :return: if pdf is a string, nothing.
            if pdf is a BytesIO object, toiCal returns a BytesIO object containing the ics file
    """
    semester = list(list(extract_pages(pdf))[0])[2].get_text().replace("Course Schedule - ", "").strip("\n").split()
    print(semester)
    month, year, days = getMonthYear(semester)
    firstDay = getFirstDay(date(year, month, 1))

    pages = list(extract_pages(pdf))[1::]
    elements = []
    courses = []
    for page in pages:
        element = list(page)[1:]  # filter out timestamp
        element = list(filter(
            lambda ele:
                "MyUW" not in str(ele) and "https" not in str(ele) and isinstance(ele, LTTextBoxHorizontal), element)
        )
        for e in element:
            elements.append(normalize("NFKC", e.get_text())[:-1])  # remove unneeded unicode characters
    for element in elements:
        courses.append([ele.strip() for ele in element.split('\n')])

    currentDay = ""
    cal = Calendar()
    i = 0

    while i < len(courses):
        #  check if page break
        if len(courses[i]) != 4 and len(courses[i]) != 5:
            courses[i].extend(courses[i + 1])
            courses.pop(i + 1)

        # check if day is present in field
        if len(courses[i]) == 5:
            fields = ["day", "name", "section", "location", "duration"]
        else:
            fields = ["name", "section", "location", "duration"]

        course = dict(zip(fields, courses[i]))
        print(course)

        # update current day if needed
        if 'day' in course.keys():
            currentDay = course['day']

        courseName = course['name'].replace("  ", " ")
        courseType = types[re.match('(\w+) (\d+)', course['section']).group(1)]
        room, building = re.match('(\d+) (\w+)', course['location']).groups()
        location = getAddress(building)
        timeSpan = course['duration'].split("to")
        start, end = getStartEndTimes(timeSpan)

        startHour, startMinute = list(map(int, start.split(":")))
        dtStart = datetime(year, month, getDay(firstDay, currentDay, days), startHour, startMinute, tzinfo=timezone)
        print(f"utc start: {dtStart}")

        endHour, endMinute = list(map(int, end.split(":")))
        dtEnd = datetime(year, month, (firstDay + timedelta(days=days[currentDay])).day, endHour, endMinute, tzinfo=timezone)
        print(f"utc end: {dtEnd}\n")

        createEvent(cal, f"{courseName} {courseType}", dtStart, dtEnd, location, room)
        i += 1

    calendarAsBytes = str(cal).encode()

    if isinstance(pdf, str):
        with open('courses.ics', 'w') as f:
            f.write(str(cal))
    else:
        return BytesIO(calendarAsBytes)


def toMilitaryTime(time: str) -> str:
    """
    This method converts a 12hr formatted time into a 24hr formatted time
    :param time: a string containing a 12hr formatted time
    :return: a string containing a 24hr formatted time
    """

    hour = int(time[:2]) % 12
    minutes = int(time[3:5])
    if time[6] == 'P':
        hour += 12
    return "{:02}:{:02}".format(hour, minutes)


def getFirstDay(dt: date) -> date:
    """
    this method computes the first day of the semester
    :param dt: a datetime object containing the month and year of the schedule
    :return: the first day of the semester
    """

    if dt.month == 1:
        day = (dt + relativedelta(day=1, weekday=TU(4)))  # Spring semester starts on 4th tuesday in january
    elif dt.month == 9:
        day = (dt + relativedelta(day=1, weekday=WE(2)))  # Fall semester always starts on 2nd wednesday in september
    else:
        raise Exception("Invalid start month!")

    return day


def getLastDay(dt: date) -> str:
    """
    this method computes the last class day of the semester
    :param dt: a datetime object containing the first day of the semester
    :return: a string containing the last class day of the semester in YYYYMMDD format
    """

    if dt.month == 1:
        # last day of classes in spring semester in the 1st friday of may
        endDate = (datetime(dt.year, 5, 1) + relativedelta(day=1, weekday=SA(1)))
    elif dt.month == 9:
        # last day of classes in fall semester is the 3rd wednesday in december
        endDate = (datetime(dt.year, 12, 1) + relativedelta(day=1, weekday=TH(3)))
    else:
        raise Exception("Invalid month!")

    return endDate.strftime("%Y%m%d")  # return in timestamp format


def getDay(firstDay: datetime, currentDay: str, dayOffset: dict) -> int:
    """
    this method computes the date of which the class occurs
    :param firstDay: a datetime object containing the first day of the semester
    :param currentDay: a string containing the current day
    :param dayOffset: a dict mapping days to their offset from either tuesday or wednesday, depending on the semester
    :return: an int containing the day of the class
    """

    return (firstDay + timedelta(days=dayOffset[currentDay])).day


def getStartEndTimes(timeSpan: list) -> tuple[str, str]:
    """
    this method computes the start and end time of the course
    :param timeSpan: a list containing the starting time in the 0th index and the end time in the 1th index
    :return: a tuple containing the start and end time in 24hr format
    """
    if len(timeSpan[0].strip().split(":")[0]) == 1:
        start = toMilitaryTime(f"0{timeSpan[0].strip()}")
    else:
        start = toMilitaryTime(timeSpan[0].strip())
    if len(timeSpan[1].strip().split(":")[0]) == 1:
        end = toMilitaryTime(f"0{timeSpan[1].strip()}")
    else:
        end = toMilitaryTime(timeSpan[1].strip())

    return start, end


def getMonthYear(semester: list[str]):
    """
    this method gets the month and year from the semester
    :param semester: a list of strings containing fall/spring in index 0 and the year span in index 1
    :return: a list containing the month, year, and day offset
    """

    yearSpan = semester[1].split('-')
    if semester[0] == "Spring":
        # Spring semester starts on 4th tuesday in january
        month = 1
        year = int(yearSpan[1])
        dayOffset = {
            "Monday": 6,
            "Tuesday": 0,
            "Wednesday": 1,
            "Thursday": 2,
            "Friday": 3,
            "Saturday": 4,
            "Sunday": 5,
        }
    elif semester[0] == "Fall":
        # Fall semester always starts on 2nd wednesday in september
        month = 9
        year = int(yearSpan[0])
        dayOffset = {
            "Monday": 5,
            "Tuesday": 6,
            "Wednesday": 0,
            "Thursday": 1,
            "Friday": 2,
            "Saturday": 3,
            "Sunday": 4,
        }

    else:
        raise Exception("Invalid Semester! (Only Fall and Spring are supported)")

    return month, year, dayOffset


def getAddress(building: str):
    """
    this method gets the address for the provided building
    :param building: a string containing the name of the building
    :return: the address of the building
    """
    facilities = pd.read_excel('FacilityList2020.xls', 'Sheet1')
    for index, row in facilities.iterrows():
        if building in row['Name']:
            return row['Street Address'] + ", Madison, WI 53715"

    raise Exception(f"Building not found! {building}")


def createEvent(calendar: Calendar, eventName: str, start: date, end: date, location: str, room: str):
    """
    this method appends an event to the given calendar
    :param calendar: Calendar to append event to
    :param eventName: the name of the event
    :param start: a datetime object containing the start time of the event
    :param end: a datetime object containing the end time of the event
    :param location: a string containing the address of the event
    :param room: a string containing the room in which the course is held in
    """
    event = Event()
    event.begin = start
    event.name = eventName
    event.extra.append(ContentLine(name="RRULE", params={}, value=f"FREQ=WEEKLY;UNTIL={getLastDay(start)};"))
    event.end = end
    event.location = location
    event.description = f"Room {room}"
    calendar.events.add(event)


if __name__ == "__main__":
    toiCal('MyUW.pdf')


