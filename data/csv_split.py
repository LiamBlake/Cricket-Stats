# =============================================================================
# Splits given .csv files in half
#
# This is needed to avoid having to fluff around with the GitHub Large File 
# System for commiting the rather large .csv files I have containing ball by 
# ball data.
# =============================================================================

from os import path

from pandas import DataFrame, read_csv
from numpy import floor


DIR = path.dirname(path.realpath(__file__))

# List the names of .csv files to be split here
FILENAMES = ["bbb_full", "is_wkt_train_preds", "outcome_train_preds", "runs_train_preds"]


for fn in FILENAMES:
    filename = DIR + "\\" + fn
    print("Splitting", fn)

    # Load .csv as pandas DataFrame
    df = read_csv(filename + ".csv")
    
    # Split in half
    nrow = len(df.index)
    idx = int(floor(nrow/2))
    df1 = df.iloc[:idx,:]
    df2 = df.iloc[idx:,:]
    
    # Save splitted files
    df1.to_csv(filename + "1.csv", header=True, index=False)
    df2.to_csv(filename + "2.csv", header=True, index=False)
    
    # Delete the original file
    
    