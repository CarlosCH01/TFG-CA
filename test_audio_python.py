# General imports to do graphs and mathematics sequeces

# Data Analysis
import pandas as pd
# Scientific computing
import numpy as np
# Creating static, animated, and interactive visualizations
import matplotlib.pylab as plt
# To do graphics and statical data visualization 
import seaborn as sns

# Used to list all the audios we'll use 
from glob import glob

# Imports to work with audio 
import librosa

# To display the audio that we want to analyze
import librosa.display
import IPython.display as ipd

# #copy pasted code for colors no impact on implementation whatsoever
from itertools import cycle

# Change visual theme of all plots
sns.set_theme(style="white", palette=None)
color_pal = plt.rcParams["axes.prop_cycle"].by_key()["color"]
color_cycle = cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])

# List of all audios about actor 1 in this case
audio_files = glob('./dataset_audio/Actor_01/*.wav')

# Play audio from the list we can do a iterative loop on audio_file
# I only set the first one to test it
ipd.Audio(audio_files[0])