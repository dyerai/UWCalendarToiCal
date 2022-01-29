from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal
from unicodedata import normalize
from ics import Calendar, Event
from ics.parse import ContentLine
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta, WE, TU
import pytz
import arrow

timezone = pytz.timezone("US/Central")
days = {
        "Monday": 6,
        "Tuesday": 0,
        "Wednesday": 1,
        "Thursday": 2,
        "Friday": 3,
        "Saturday": 4,
        "Sunday": 5,
    }
types = {
    "DIS": "Discussion",
    "LEC": "Lecture",
    "LAB": "Lab"
}


def main():
    path = "CourseList.pdf"
    semester = list(list(extract_pages(path))[0])[2].get_text().replace("Course Schedule - ", "").strip("\n").split()
    yearSpan = semester[1].split('-')
    print(semester)
    if semester[0] == "Spring":
        month = 1
        year = int(yearSpan[1])
    elif semester[0] == "Fall":
        month = 9
        year = int(yearSpan[0])
    else:
        raise Exception("Invalid Semester! (Only Fall and Spring are supported)")
    firstDay = getFirstDay(date(year, month, 1))

    pages = list(extract_pages(path))[1::]
    elements = []
    courses = []
    for page in pages:
        element = list(page)[1::]  # filter out timestamp
        element = (list(filter(lambda ele: "MyUW" not in str(ele) and "https" not in str(ele) and isinstance(ele, LTTextBoxHorizontal), element)))
        for e in element:
            elements.append(normalize("NFKC", e.get_text())[:-2])
    for element in elements:
        courses.append([ele.strip() for ele in element.split('\n')])

    currentDay = ""
    cal = Calendar()
    i = 0
    while i < len(courses):
        course = courses[i]
        if len(course) != 4 and len(course) != 5:
            course.extend(courses[i + 1])
            courses.remove(courses[i + 1])

        print(course)

        if course[0] in days:
            currentDay = course[0]
            courseName = course[1].replace("  ", " ")
            type = types[course[2].split()[0]]
            location = course[3]
            start = toMilitaryTime(course[4].split("to")[0].strip())
            end = toMilitaryTime(course[4].split("to")[1].strip())
        else:
            courseName = course[0].replace("  ", " ")
            type = types[course[1].split()[0]]
            location = course[2]
            timeSpan = course[3].split("to")
            if len(timeSpan[0].strip().split(":")[0]) == 1:
                start = toMilitaryTime(f"0{timeSpan[0].strip()}")
            else:
                start = toMilitaryTime(timeSpan[0].strip())
            if len(timeSpan[1].strip().split(":")[0]) == 1:
                end = toMilitaryTime(f"0{timeSpan[1].strip()}")
            else:
                end = toMilitaryTime(timeSpan[1].strip())
        dtStart = datetime(year, month, getDay(firstDay, currentDay), int(start.split(":")[0]), int(start.split(":")[1]), tzinfo=timezone)
        print(f"utc start: {dtStart}")
        dtEnd = datetime(year, month, (firstDay + timedelta(days=days[currentDay])).day, int(end.split(":")[0]), int(end.split(":")[1]), tzinfo=timezone)
        print(f"utc end: {dtEnd}\n")
        createEvent(cal, f"{courseName} {type}", dtStart, dtEnd)
        i += 1
    with open("cal.ics", "w") as f:
        f.write(str(cal))


    """
    for e in element:
        if isinstance(e, LTTextBoxHorizontal):
            e = list(filter(lambda ele: "MyUW" not in ele.get_text() and "https" not in ele.get_text(), e))
            print(e)
    """


# from https://www.tutorialspoint.com/24-hour-time-in-python
def toMilitaryTime(time):
    hour = int(time[:2]) % 12
    minutes = int(time[3:5])
    if time[6] == 'P':
        hour += 12
    return "{:02}:{:02}".format(hour, minutes)


def getFirstDay(dt):
    """
    Fall semester always starts on 2nd wednesday in september
    Spring semester starts on 4th tuesday in january
    """
    # from https://stackoverflow.com/a/53926932
    if dt.month == 1:
        day = (dt + relativedelta(day=1, weekday=TU(4)))
    elif dt.month == 9:
        day = (dt + relativedelta(day=1, weekday=WE(2)))
    else:
        raise Exception("Invalid start month!")

    return day


def getDay(firstDay, currentDay):
    return (firstDay + timedelta(days=days[currentDay])).day


def createEvent(calendar, eventName, start, end):
    event = Event()
    event.begin = arrow.get(start, 'US/Central')
    event.name = eventName
    event.extra.append(ContentLine(name="RRULE", params={}, value="FREQ=WEEKLY;UNTIL=20220515T040000Z;"))
    event.end = arrow.get(end, 'US/Central')
    calendar.events.add(event)


if __name__ == "__main__":
    main()


