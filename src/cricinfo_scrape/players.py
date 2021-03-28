from requests import get
from typing import List

from bs4 import BeautifulSoup, SoupStrainer
from pandas import DataFrame

# Column names for output DataFrames
COL_STATS_BAT = ["Mat", "Inns", "NO", "Runs", "HS", "Ave",
                 "BF", "SR", "100", "50", "4s", "6s", "Ct", "St"]
COL_STATS_BOWL = ["Mat", "Inns", "Balls", "Runs", "Wkts",
                  "BBI", "BBM", "Ave", "Econ", "SR", "4w", "5w", "10"]


def get_career_stats(url: str, formats: List[str] = ["test", "odi", "t20i"]):
    # Validate input

    # Create a copy of the passed list
    Formats = [""]*len(formats)
    for i in range(len(formats)):
        if formats[i] == "test":
            Formats[i] = "Tests"
        elif formats[i] == "odi":
            Formats[i] = "ODIs"
        elif formats[i] == "t20i":
            Formats[i] = "T20Is"
        elif formats[i] == "fc":
            Formats[i] = "First-class"
        elif formats[i] == "la":
            Formats[i] = "List A"
        elif formats[i] == "t20":
            Formats[i] = "T20s"
        else:
            raise ValueError("Unknown format " + formats[i])

    # Access page and process tables only
    page = get(url)
    strainer = SoupStrainer("table")
    soup = BeautifulSoup(page.content, "html.parser", parse_only=strainer)

    # Get batting and bowling stats tables
    tabs = soup.find_all("tbody")
    bat = tabs[0].find_all("tr")
    bowl = tabs[1].find_all("tr")

    assert(len(bat) == len(bowl))

    # Create output dataframes
    bat_res = DataFrame(columns=COL_STATS_BAT, index=Formats)
    bowl_res = DataFrame(columns=COL_STATS_BOWL, index=Formats)

    # Iterate through each format, checking against Formats list
    for i in range(len(bat)):
        rbat = bat[i]
        rbowl = bowl[i]
        rform = rbat.find("td").text

        if rform in Formats:
            # Grab statistics
            bat_res.loc[rform] = [t.text for t in rbat.find_all("td")[1:]]
            bowl_res.loc[rform] = [t.text for t in rbowl.find_all("td")[1:]]

    return bat_res, bowl_res
