
import numpy as np
import pandas as pd

class Behavior():

    def __init__(self, file):
        print("behavior", file)

        self.behav_def = pd.read_csv(file, sep=',')
        #空部(nan)はNoneに変換する。
        self.behav_def.fillna("", inplace=True)
        #print(self.behav_def)
        #print(self.behav_def.loc[2]['no'])
        #print(len(self.behav_def))

    def get_node(self, index):
        if len(self.behav_def) < index :
            print("index error")
            return None

        return self.behav_def.loc[index]
