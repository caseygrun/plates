from microplates.calculate import *

import pandas as pd
import numpy as np

def test_calc_norm():
    df = pd.DataFrame([
            ('A1', 0.004, 0, 10),
            ('A2', 0.005, 0, 100),
            ('A1', 0.022, 1, 10),
            ('A2', 0.027, 1, 100),
        ], columns=('well','OD600','time','concentration'))

    # normalize OD600 to the value at time = 0 for each concentration
    df2 = calc_norm(df, value='OD600', on='time', columns=['time','concentration'], how=lambda x: x - x.loc[0])
    assert np.allclose(df2.query('well == "A1" & time == 0').OD600,0)
    assert np.allclose(df2.query('well == "A2 & time == 0"').OD600,0)

    # normalize OD600 to the value of concentration = 10 at each timepoint
    df2 = calc_norm(df, value='OD600', on='concentration', columns=['time','concentration'], how=lambda x: x - x.loc[10])
    assert np.allclose(df2.query('well == "A1" & time == 0').OD600,0)
    assert np.allclose(df2.query('well == "A1 & time == 1"').OD600,0)

    df = pd.DataFrame([
        ('A1', 0.004, 0, 10),
        ('A2', 0.002, 0, 10),
        ('A3', 0.003, 0, 10),
        ('A1', 0.044, 1, 10),
        ('A2', 0.042, 1, 10),
        ('A3', 0.043, 1, 10),
    ], columns=('well','OD600','time','concentration'))

    # normalize OD600 to average value of the wells at the zero time point
    df2 = calc_norm(df, value='OD600', on='time', columns=['time','concentration'], how=lambda x: x - x.loc[0].mean())
