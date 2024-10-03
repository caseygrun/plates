"""
Plot microplate data.
"""

import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from .utils import *
from .data import fortify_plate, add_row_column, pivot_plate

def parse_hue(values, order=None, palette=None):
    import seaborn as sns
    # https://stackoverflow.com/questions/26139423/plot-different-color-for-different-categorical-levels-using-matplotlib

    if order is None:
        if isinstance(values,pd.DataFrame):
            levels = list(values.drop_duplicates().itertuples(index=False))
        else:
            levels = values.unique()
    else:
        levels = order
    n_colors = len(levels)

    # if palette wasn't specified, use current palette
    if palette is None:
        # Determine whether the current palette will have enough values
        # If not, we'll default to the husl palette so each is distinct
        current_palette = sns.utils.get_color_cycle()
        if n_colors <= len(current_palette):
            colors = sns.color_palette(n_colors=n_colors)
        else:
            colors = sns.husl_palette(n_colors, l=.7)
    else:
        colors = sns.color_palette(palette,n_colors=n_colors)

    # map levels of the hue variable to different RGB color triplets
    hue_map = dict(zip(levels, colors))
    return hue_map

def plot_plate(plate,labels=None,size=None,
               hue=None,hue_order=None,palette=None,
               text_hue=False,text_hue_order=None,text_palette=None, text_kwargs=None,
               edgecolors=None,edgecolors_order=None,edgecolors_palette=None,
               default_color=[0,0,0],
               wells=96,
               ax=None,
               **kwargs):
    """Plot microplate data on a microplate-shaped plot

    Parameters
    ----------
    plate : pd.DataFrame
        Tidy microplate data; the index should contain the well names, or there
        should be a column named ``well`` or ``wells`` containing the well
        names. Each row should be a distinct well. Well names should be unique.
    wells : int, default=96
        Shape of the microplate, or None to infer size from the
    ax : mpl.Axes, optional
        Axes on which to draw the plot; if not given, plot is drawn on a new
        set of axes in a new figure
    labels : list of str
        Names of columns to draw as text labels on the plot; each column will be
        drawn as a separate row.
    hue : str
        Name of column to map to the hue channel
    hue_order : list of str, optional
        Order for the hue levels, defaults to the order in the plate
    palette : str, optional
        Colors to use for the different levels of the hue variable. Should be
        something that can be interpreted by ``sns.color_palette``, or a
        dictionary mapping hue levels to matplotlib colors.
    text_hue : bool or str, default=False
        Name of column to map to the text hue channel, or ``True`` to use the
        column from ``hue`` to set the color of the text as well
    text_kwargs : dict
        Additional kwargs to pass to ``plt.text``
    text_hue_order : list of str, optional
        Order for the text hue levels, if given separately from ``hue``
    text_palette : str, optional
        Palette for the text hues
    edgecolors : str, optional
        Name of column to map to the edge color channel
    edgecolors_order : list of str, optional
        Order for the edge hue levels
    edgecolors_palette : str, optional
        Palette for the edge colors
    default_color : list, default=[0,0,0]
        RGB triple indicating the default color for NA values
    """
    import numbers


    plate = fortify_plate(plate)
    if wells is None:
        wells = infer_plate_size(plate.index)

    shape = plates[wells]
    xs = np.arange(shape[1])
    ys = np.arange(shape[0])
    xx, yy = np.meshgrid(xs,ys)
    if ax is None: ax = plt.gca()

    row_labels = list(map(row2letters, ys))
    col_labels = list(map(lambda x: str(x+1), xs))
    ss = None
    cs = None
    ecs = None
    if size is not None:
        ss = np.zeros(shape[0]*shape[1])
        if isinstance(size,numbers.Number):
            ss += size
            size = None
    if hue is not None:
        cs = np.zeros((shape[0]*shape[1],3))
        hue_map = parse_hue(plate[hue], hue_order, palette)

    if text_hue is not None and text_hue != True and text_hue != False:
        text_cs = np.zeros((shape[0]*shape[1],3))
        text_hue_map = parse_hue(plate[text_hue], text_hue_order, text_palette)

    if edgecolors is not None:
        ecs = np.zeros((shape[0]*shape[1],3))
        edgecolors_map = parse_hue(plate[edgecolors], edgecolors_order, edgecolors_palette)

    if text_kwargs is None:
        text_kwargs = {}


    # Iterate across each well of the plate
    for i,row in enumerate(ys):
        for j,col in enumerate(xs):
            well = row_labels[row]+col_labels[col]
            if well not in plate.index:
                continue
            if size is not None:
                ss[row*shape[1]+col] = plate.loc[well,size]
            if hue is not None:
                cs[row*shape[1]+col,:] = hue_map.get(plate.loc[well,hue],default_color)
            if edgecolors is not None:
                ecs[row*shape[1]+col,:] = edgecolors_map.get(plate.loc[well,edgecolors],default_color)
            if labels is not None:
                if labels == True:
                    label = [well]
                elif isinstance(labels,str):
                    label = [plate.loc[well,labels]]
                elif isinstance(labels,list):
                    label = [plate.loc[well,l] for l in labels]

                if text_hue == True and hue is not None:
                    if isinstance(hue, str):
                        color = hue_map.get(plate.loc[well,hue],default_color)
                    else:
                        color = hue_map.get(tuple(plate.loc[well,hue]),default_color)
                elif text_hue != False:
                    if isinstance(text_hue, str):
                        color = text_hue_map.get(plate.loc[well,text_hue],default_color)
                    else:
                        color = text_hue_map.get(tuple(plate.loc[well,text_hue]),default_color)
                else:
                    color = default_color

                for k,txt in enumerate(label):
                    ax.annotate(
                        txt,
                        xy=(col, row), xytext=( col, row-0.2+(0.8*k*1/len(label)) ),
                        textcoords=ax.transData, #textcoords='offset points',
                        # ax=ax,
                        ha='center', va='baseline',
                        color=color, **text_kwargs)

    # plt.scatter(xx,yy,c=cs,s=ss, edgecolors=ecs, ax=ax, **kwargs)
    ax.scatter(xx,yy,c=cs,s=ss, edgecolors=ecs, **kwargs)
    ax.invert_yaxis()
    ax.xaxis.tick_top()
    plt.yticks(ys, row_labels)
    # ax.set_yticks(ys, labels=row_labels)
    plt.xticks(xs, col_labels)
    # ax.set_xticks(xs, labels=col_labels)

def plot_cherrypick(pick_wells,**kwargs):
    """Draws a plate with the given wells marked

    Parameters
    ----------
    pick_wells : list of str
        Well names to mark
    **kwargs : dict, optional
        Additional parameters passed to :func:`plot_plate`
    """
    return plot_plate(cherrypick(pick_wells,
                                 {'size': 50, 'pick':True},
                                 {'size':10, 'pick':False}),
                      hue='pick', hue_order=[True, False], size='size', **kwargs)

def pandas_df_to_markdown_table(df):
    df_formatted = pd.concat([
        pd.DataFrame([['---' for i in range(len(df.columns))]], columns=df.columns, index=['---']), 
    df])
    return "\n".join(['|'+r+'|' for r in df_formatted.to_csv(sep="|", index=True).split("\n") if r != ''])

def plate_to_markdown(data, parameter='OD600'):
    # return pivot_plate(data,parameter,natural=True).to_markdown()
    return pandas_df_to_markdown_table(pivot_plate(data,parameter,natural=True))


def platemap_markdown(df):
    df = df.rename(columns={'Well':'well'})
    df['text'] = df['Expt']+'.'+df['Round']+'.'+df['Sample']
    return pandas_df_to_markdown_table(pivot_plate(df, parameter='text', natural=True))


def plate_heatmap(data,parameter='OD600',natural=True,**kwargs):
    """Plot a single microplate as a heatmap.

    Parameters
    ----------
    data : pd.DataFrame
        Tidy dataframe of microplate data
    parameter : str
        Name of the column to contain the heatmap data
    natural : bool, default=False
        True to show plate rows as ``A``, ``B``, ``C``, etc. and columns as
        ``1``, ``2``, ``3``. False to use 0-based indices for both.
    **kwargs :
        Additional arguments will be passed to :func:`seaborn.heatmap`
    """
    p = sns.heatmap(data=pivot_plate(data,parameter,natural=natural),square=True,**kwargs)
    plt.yticks(rotation=0)
    return p

def plate_heatmaps(data,parameter='OD600',row=None, col=None, natural=True,facet_kwargs={}, vmin=None, vmax=None, **kwargs):
    """Plot several plates as a grid of heatmaps

    Uses :class:`seaborn.FacetGrid`.

    Parameters
    ----------
    data : pd.DataFrame
        Tidy dataframe of microplate data
    parameter : str
        Name of the column to contain the heatmap data
    row : str
        Name of the column to use to organize plots into rows
    col : str
        Name of the column to use to organize plots into columns
    natural : bool, default=False
        True to show plate rows as ``A``, ``B``, ``C``, etc. and columns as
        ``1``, ``2``, ``3``. False to use 0-based indices for both.
    vmin : float, optional
        Lower bound of the range of heatmap values to plot; defaults to lower
        bound of the data across all facets
    vmax : float, optional
        Upper bound of the range of heatmap values to plot; defaults to lower
        bound of the data across all facets
    facet_kwargs : dict, optional
        Additional ``kwargs`` to pass to `seaborn.FacetGrid`
    **kwargs :
        Additional arguments will be passd to :func:`plate_heatmap` and in turn
        to :func:`seaborn.heatmap`


    Returns
    -------
    seaborn.FacetGrid
        FacetGrid of heatmaps

    """
    g = sns.FacetGrid(data,row=row,col=col,**facet_kwargs)

    # auto-set range
    if vmin is None: vmin = data[parameter].min()
    if vmax is None: vmax = data[parameter].max()
    return g.map_dataframe(plate_heatmap, vmin=vmin,vmax=vmax, **kwargs)
