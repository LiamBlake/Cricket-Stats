#
#
#

from pandas import DataFrame, read_csv
from random import randint, choice
from os import path
from io import StringIO

class Team:

    def __init__(self, name, players):
        self.name = name
        self.players = players

        # By default, randomly choose captain, opening bowlers
        self.captain = randint(1, 11)
        self.bowl1 = randint(8, 11)
        self.bowl2 = choice([i for i in range(8, 12) if i != self.bowl1])

        # Wicketkeeper is assumed to bat at 7
        self.wk = 7

    def save(self, filename):
        pass

    def __setattr__(self, name, value):
        if (name == 'name'):
            #assert isinstance(value, str)
            pass
        elif (name == 'players'):
            pass
        else:
           
            assert isinstance(value, int)
            assert value > 0 and value < 12

            if name == 'wk' and hasattr(self, 'bowl1') and hasattr(self, 'bowl2'):
                assert value != self.bowl1 and value != self.bowl2

            elif name == 'bowl1' and hasattr(self, 'bowl2'):
                assert value != self.bowl2

            elif name == 'bowl2' and hasattr(self, 'bowl1'):
                assert value != self.bowl1

            super().__setattr__(name, value)


    def __str__(self):
        pass

def file2team(filename):
    # Open file
    f = open(filename, 'r')

    # Read players and convert to DataFrame
    iostr = ''
    for i, x in enumerate(f):
        if i == 0:
            name = x
        elif i < 12:
            iostr = iostr + x
        else:
            strnums = x

    players = read_csv(StringIO(iostr))
    output = Team(players, name)

    # Get captain, etc.
    nums = strnums.split(',')
    output.captain = int(nums[0])
    output.wk = int(nums[1])
    output.bowl1 = int(nums[2])
    output.bowl2 = int(nums[3])

    f.close()


#ALL_PLAYERS = read_csv('PlayerStats.csv')
DIR = path.dirname(path.realpath(__file__))

file2team(DIR + '/teams/TestXI.txt')