from typing import List, Tuple

from bs4 import BeautifulSoup, SoupStrainer
from pandas import DataFrame
from requests import get

# Column names for output DataFrames
COL_STATS_BAT = [
    "Mat",
    "Inns",
    "NO",
    "Runs",
    "HS",
    "Ave",
    "BF",
    "SR",
    "100",
    "50",
    "4s",
    "6s",
    "Ct",
    "St",
]
COL_STATS_BOWL = [
    "Mat",
    "Inns",
    "Balls",
    "Runs",
    "Wkts",
    "BBI",
    "BBM",
    "Ave",
    "Econ",
    "SR",
    "4w",
    "5w",
    "10",
]


def get_player_data(url: str, formats: List[str] = ["test", "odi", "t20i"]) -> Tuple[DataFrame, DataFrame, DataFrame]:
    """

    Arguments:
        url:
        formats:
    """
    # Validate input

    # Create a copy of the passed list
    Formats = [""] * len(formats)
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

    assert len(bat) == len(bowl)

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

    # Remove rows corresponding to missing formats
    bat_res.dropna(how="all", inplace=True)
    bowl_res.dropna(how="all", inplace=True)

    return 1, bat_res, bowl_res


def update_players():

    URL_START = "https://stats.espncricinfo.com/ci/engine/stats/index.html?class=1;filter=advanced;orderby=start;page="
    URL_END = (
        ";size=200;template=results;type=allround"
    )

    # Formatted dataframe
    COL_BAT_RES = (
        ["Name", "Country"]
        + ["test_" + s for s in COL_STATS_BAT]
        + ["fc_" + s for s in COL_STATS_BAT]
    )
    res_bat = DataFrame(columns=COL_BAT_RES)
    COL_BOWL_RES = (
        ["Name", "Country"]
        + ["test_" + s for s in COL_STATS_BOWL]
        + ["fc_" + s for s in COL_STATS_BOWL]
    )
    res_bowl = DataFrame(columns=COL_BOWL_RES)

    strainer = SoupStrainer("table")

    df_idx = 0
    page = 1
    while True:
        print("Parsing page " + str(page) + "...")

        # Get table
        web = get(URL_START + str(page) + URL_END)
        soup = BeautifulSoup(web.content, "html.parser", parse_only=strainer)
        table = soup.find_all("table")[2]

        # Check for empty table
        if table.find("td").text == "No records available to match this query":
            # Reached end of table
            print("End of table reached, terminating scrape.")
            break

        # Iterate through each entry
        table = table.find("tbody")
        for tr in table.find_all("tr"):
            try:
                cell = tr.find("td")
                ply_url = cell.find("a", href=True)["href"]
                ply_det = cell.text

                # Extract name, country
                row = [s[:-1] for s in ply_det.split("(")]

                # Scrape stats and add to row
                plr_df, bat_df, bowl_df = get_player_data(
                    "https://www.espncricinfo.com" + ply_url, formats=["test", "fc"]
                )
                bat_row = (
                    row + list(bat_df.loc["Tests"]) + list(bat_df.loc["First-class"])
                )
                bowl_row = (
                    row + list(bowl_df.loc["Tests"]) + list(bowl_df.loc["First-class"])
                )

                # Add to database
                res_bat.loc[df_idx] = bat_row
                res_bowl.loc[df_idx] = bowl_row
                df_idx = df_idx + 1

            except ValueError:
                # Something has gone wrong, skip this entry
                print("Skipping an entry :(")
                pass

        page = page + 1

    print("Saving data")
    res_bat.to_csv("data/processed/fc_test_bat_stats.csv", index=False)
    res_bowl.to_csv("data/processed/fc_test_bowl_stats.csv", index=False)
    print("Done!")
