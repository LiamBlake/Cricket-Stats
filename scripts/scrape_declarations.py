from math import floor

import requests
from bs4 import BeautifulSoup, SoupStrainer
from pandas import DataFrame

url_start = "https://stats.espncricinfo.com/ci/engine/stats/index.html?class=1;filter=advanced;orderby=start;page="
url_end = ";size=200;template=results;type=team;view=innings"

strainer = SoupStrainer("tr", attrs={"class": "data1"})

df = DataFrame(
    columns=[
        "Team",
        "Score",
        "Overs",
        "RPO",
        "Lead",
        "Inns",
        "Result",
        "Opposition",
        "Ground",
        "Start Date",
    ]
)
for i in range(1, 46):
    print(f"Scraping page {i} of 45...")

    # Load and parse the webpage
    url = f"{url_start}{i}{url_end}"
    page = requests.get(url)

    rows = BeautifulSoup(page.content, "html.parser", parse_only=strainer).find_all(
        "tr"
    )

    # Parse each row into a row of the dataframe
    for row in rows:
        data = row.find_all("td")
        df.loc[len(df.index)] = [
            data[0].find("a").text,
            data[1].text,
            data[2].text,
            data[3].text,
            data[4].text,
            data[5].text,
            data[6].text,
            data[8].find("a").text,
            data[9].find("a").text,
            data[10].text,
        ]


# Save the full dataframe as a CSV file
df.to_csv("data/raw/innings_totals.csv", index=False)


def as_balls(overs: str):
    """Convert"""
    num = float(overs)
    return int(floor(num) * 6 + (num - floor(num)) * 10)


# Process into declaration data
# Use the ground and start date to uniquely identify each match
print("Processing declarations...")
declarations = DataFrame(
    columns=[
        "team1",
        "team2",
        "balls_left",
        "lead",
        "final_score",
        "final_wickets",
        "result",
        "ground",
        "date",
    ]
)
for name, group in df.groupby(["Ground", "Start Date"], sort=False):
    # Only consider games that had four innings
    if len(group.index) < 4:
        continue

    # Only consider games with 6 ball overs
    # TODO: Handle these
    if group.iloc[0].loc["Overs"][-2] == "x":
        continue

    # Only consider games with a third-innings declaration
    third_innings_score = group.iloc[2]["Score"]
    if "/" not in third_innings_score:
        continue

    team1 = group.iloc[2].loc["Team"]
    team2 = group.iloc[3].loc["Team"]

    # Calculate the number of overs left in the game upon declaration
    # Assume that a full 480 overs are availale in the game
    # Not a great assumption.
    overs_left = 480 * 6 - sum([as_balls(x) for x in group.iloc[:3]["Overs"]])

    # Calculate the lead upon declaration
    # The innings order may not be sequential,
    # e.g. declaration after following on (like Kolkata 2001)
    if group.iloc[1].loc["Team"] == team1:
        # The other team batted in the first innings
        lead = (
            -int(group.iloc[0].loc["Score"].split("/")[0])
            + int(group.iloc[1].loc["Score"].split("/")[0])
            + int(group.iloc[2].loc["Score"].split("/")[0])
        )
    else:
        # The declaring team batted in the first innings
        lead = (
            int(group.iloc[0].loc["Score"].split("/")[0])
            - int(group.iloc[1].loc["Score"].split("/")[0])
            + int(group.iloc[2].loc["Score"].split("/")[0])
        )

    try:
        final_score, final_wickets = group.iloc[3].loc["Score"].split("/")
    except ValueError:
        final_score = group.iloc[3].loc["Score"]
        final_wickets = 10

    declarations.loc[len(declarations.index)] = [
        team1,
        team2,
        overs_left,
        lead,
        final_score,
        final_wickets,
        group.iloc[2].loc["Result"],
        name[0],
        name[1],
    ]

# Save the processed data
declarations.to_csv("data/processed/declarations.csv", index=False)
