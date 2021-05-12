# `microplates`
Tidy data from microplate data.

This package helps to read, process, and plot data and experiments in [microtiter plates](https://en.wikipedia.org/wiki/Microtiter_plate) as tidy pandas `DataFrame`s

- **Read** (`microlates.io`): import data (e.g. OD600, fluorescence, etc.) from microplate readers, and convert to a **tidy format** (each row is an observation of one well; each column is a different variable, e.g. OD600, FITC, time, etc.)

    | Well | OD600  | FITC  |
    | ---- | ------ | ----- |
    | A1   | 0.0102 | 0.975 |
    | A2   | 0.0254 | 0.375 |
    | A3   | 0.0321 | 0.002 |
    | A4   | 0.0269 | 0.005 |

- **Metadata** (`microplates.data`): describe layout of samples/conditions on the plate (drug, concentration, strain, etc.) in a compact format, get a tidy DataFrame; join this to your measurements, and you have a dataset of the entire experiment useful for downstream processing

    | Well | OD600  | FITC  | Strain     | Induced |
    | ---- | ------ | ----- | ---------- | ------- |
    | A1   | 0.0102 | 0.975 | PAO1 sfGFP | True    |
    | A2   | 0.0254 | 0.125 | PAO1 sfGFP | False   |
    | A3   | 0.0321 | 0.002 | PAO1 WT    | True    |
    | A4   | 0.0269 | 0.005 | PAO1 WT    | False   |

- **Process** (`microplates.calculate`): subtract values of a negative control well, subtract value at the first timepoint, etc.
- **Plot** (`microplates.plot`): visualize the measured data or metadata as it appears on the plate (to detect positional effects, verify your platemap, etc.)

## Examples

```ipython    
>>> import plates
>>> platemap = plates.prog2spec({'A1:A2':{ 'strain': 'B. theta' }})
>>> platemap
       strain
A1   B. theta
A2   B. theta
A3        NaN
...
H12       NaN
[96 rows x 1 columns]

>>> df = pd.read_excel('data.xlsx')
>>> df = pd.DataFrame([
        ('A1', 0.001, 0),
        ('A2', 0.001, 0),
        ('A1', 0.011, 1),
        ('A2', 0.012, 1),
        ('A1', 0.023, 2),
        ('A2', 0.025, 2),
        ('A1', 0.048, 3),
        ('A2', 0.051, 3)
    ], columns=('well', 'OD600', 'time'))

>>> pd.merge(df,platemap, how='inner',left_on='well',right_index=True).dropna()
  well  OD600  time    strain
0   A1  0.001     0  B. theta
2   A1  0.011     1  B. theta
4   A1  0.023     2  B. theta
6   A1  0.048     3  B. theta
1   A2  0.001     0  B. theta
3   A2  0.012     1  B. theta
5   A2  0.025     2  B. theta
7   A2  0.051     3  B. theta
```

```ipython
>>> plates.prog2spec({'A1:A2':{ 'strain': [['B. theta','C. diff']] }})
      strain
A1   B. theta
A2    C. diff
A3        NaN
...
H12       NaN
[96 rows x 1 columns]
```

```
>>> plates.prog2spec({'B1:C2,E1:F2':{ 'conc': [[0,1],[2,3]] }}).dropna()
    conc
B1   0.0
B2   1.0
C1   2.0
C2   3.0
E1   0.0
E2   1.0
F1   2.0
F2   3.0
```
