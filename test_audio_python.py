# General imports to do graphs and mathematics sequeces
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import seaborn as sns

# Used to list all the audios we'll use 
from glob import glob

# Imports to work woth audio 
import librosa
import librosa.display
import IPython.display as ipd

from itertools import cycle

sns.set_theme(style="white", palette=None)
color_pal = plt.rcParams["axes.prop_cycle"].by_key()["color"]
color_cycle = cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])