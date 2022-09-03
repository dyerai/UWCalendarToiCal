from datetime import datetime

import tabula


class AcademicCalendar:
    def __init__(self):
        self.year_calendar = tabula.read_pdf("data/2795-Academic-Calendar-2021-2026.pdf", area=(237.64, 36.88, 237.64 + 431.51,
                                                                                                36.88 + 542.02), pages=1)[0]
        fall = self.year_calendar.iloc[:9]
        fall.columns = ["Event", "2021", "2022", "2023", "2024", "2025"]
        self.fall = fall.set_index("Event")

        spring = self.year_calendar.iloc[11:21]
        spring.columns = ["Event", "2022", "2023", "2024", "2025", "2026"]
        self.spring = spring.set_index("Event")

    def getFirstDayOfFall(self, year):
        month_date = self.fall.at["Instruction begins", str(year)][:-4]
        dt = datetime.strptime(month_date, "%b %d")
        return dt.replace(year=year).date()

    def getFirstDayOfSpring(self, year):
        month_date = self.spring.at["Instruction begins", str(year)][:-4]
        dt = datetime.strptime(month_date, "%b %d")
        return dt.replace(year=year).date()
