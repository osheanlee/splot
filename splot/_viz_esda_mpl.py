import matplotlib.pyplot as plt
import geopandas as gpd
import pysal as ps
import esda

from matplotlib import patches, colors

from ._viz_utils import mask_local_auto, moran_hot_cold_spots

"""
Lightweight visualizations for pysal using Matplotlib and Geopandas

TODO
geopandas plotting, change round shapes in legends to boxes
change function input naming to be in line with bokeh functionality
check if geopandas can read **kwargs
check if attribute in gdf.plot works without attribute str
"""

__author__ = ("Stefanie Lumnitz <stefanie.lumitz@gmail.com>")


def moran_loc_scatterplot(moran_loc, p=None,
                      ax=None, **kwargs):
    """
    Moran Scatterplot with option of coloring of Local Moran Statistics

    Parameters
    ----------
    moran_loc : esda.moran.Moran_Local instance
        Values of Moran's I Local Autocorrelation Statistics
    p : float, optional
        If given, the p-value threshold for significance. Points will
        be colored by significance. By default it will not be colored.
        Default =None.
    ax : Matplotlib Axes instance, optional
        If given, the Moran plot will be created inside this axis.
        Default =None.
    **kwargs : keyword arguments, optional
        Keywords used for creating and designing the plot.TODO fixed amount:list

    Returns
    -------
    fig : Matplotlib Figure instance
        Moran scatterplot figure
    ax : matplotlib Axes instance
        Axes in which the figure is plotted

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import pysal as ps
    >>> import esda
    >>> from pysal.contrib.pdio import read_files
    >>> from splot.esda import moran_loc_scatterplot

    >>> link = ps.examples.get_path('columbus.shp')
    >>> db = read_files(link)
    >>> y = db['HOVAL'].values
    >>> w = ps.queen_from_shapefile(link)
    >>> w.transform = 'R'

    >>> m = esda.moran.Moran_Local(y, w)
    >>> moran_loc_scatterplot(m)

    >>> moran_loc_scatterplot(m, figsize=(7,7), p=0.05)
    >>> plt.show()
            
    """
    lag = ps.lag_spatial(moran_loc.w, moran_loc.z)
    fit = ps.spreg.OLS(moran_loc.z[:, None], lag[:,None])

    if p is not None:
        if not isinstance(moran_loc, esda.moran.Moran_Local):
            raise ValueError("`moran_loc` is not a Moran_Local instance")
        
        spots = moran_hot_cold_spots(moran_loc, p)

        hmap = colors.ListedColormap(['lightgrey', '#d7191c', '#abd9e9', '#2c7bb6', '#fdae61'])

    # Customize plot
    if ax is None:
        figsize = kwargs.pop('figsize', (7,7))
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()

    # customize figure
    xlabel = kwargs.pop('xlabel', 'Attribute')
    ylabel = kwargs.pop('ylabel', 'Spatial Lag')
    title = kwargs.pop('title', 'Moran Scatterplot')
    alpha = kwargs.pop('alpha', 0.6)

    ax.spines['left'].set_position(('axes', -0.05))
    ax.spines['right'].set_color('none')
    ax.spines['bottom'].set_position(('axes', -0.05))
    ax.spines['top'].set_color('none')
    ax.spines['left'].set_smart_bounds(True)
    ax.spines['bottom'].set_smart_bounds(True)
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    if p is not None:
        ax.scatter(moran_loc.z, lag, c=spots, cmap=hmap, s=60, alpha=alpha)
    else:
        ax.scatter(moran_loc.z, lag, s=60, color='k', alpha=alpha)

    ax.plot(lag, fit.predy, color='k', alpha=.8)

    ax.axvline(0, alpha=0.5, linestyle='--')
    ax.axhline(0, alpha=0.5, linestyle='--')

    return fig, ax



def lisa_cluster(moran_loc, gdf, p=0.05, ax=None,
                 legend=True, legend_kwds=None, **kwargs):
    """
    Create a LISA Cluster map

    Parameters
    ----------
    moran_loc : esda.moran.Moran_Local instance
        Values of Moran's Local Autocorrelation Statistic
    gdf : geopandas dataframe instance
        The Dataframe containing information to plot. Note that `gdf` will be
        modified, so calling functions should use a copy of the user
        provided `gdf`. (either using gdf.assign() or gdf.copy())
    p : float, optional
        The p-value threshold for significance. Points will
        be colored by significance.
    ax : matplotlib Axes instance, optional
        Axes in which to plot the figure in multiple Axes layout.
        Default = None
    legend : boolean, optional
        If True, legend for maps will be depicted. Default = True
    legend_kwds : dict, optional
        Dictionary to control legend formatting options. Example:
        ``legend_kwds={'loc': 'upper left', 'bbox_to_anchor': (0.92, 1.05)}``
        Default = None
    **kwargs : keyword arguments, optional
        Keywords used for creating and designing the plot. TODO geodataframe.plot

    Returns
    -------
    fig : matplotlip Figure instance
        Figure of LISA cluster map
    ax : matplotlib Axes instance
        Axes in which the figure is plotted

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import libpysal.api as lp
    >>> from libpysal import examples
    >>> import geopandas as gpd
    >>> import esda
    >>> from splot.esda import lisa_cluster

    >>> link = examples.get_path('columbus.shp')
    >>> gdf = gpd.read_file(link)
    >>> y = gdf['HOVAL'].values
    >>> w = lp.Queen.from_dataframe(gdf)
    >>> w.transform = 'r'
    >>> moran_loc = esda.moran.Moran_Local(y, w)

    >>> fig = lisa_cluster(moran_loc, gdf)
    >>> plt.show()
    """
    # retrieve colors5 and labels from mask_local_auto
    _, colors5, _, labels = mask_local_auto(moran_loc, p=p)

    # define ListedColormap
    hmap = colors.ListedColormap(colors5)

    if ax is None:
        figsize = kwargs.pop('figsize', None)
        fig, ax = plt.subplots(1, figsize=figsize)
    else:
        fig = ax.get_figure()

    gdf.assign(cl=labels).plot(column='cl', categorical=True,
                              k=2, cmap=hmap, linewidth=0.1, ax=ax,
                              edgecolor='white', legend=legend,
                              legend_kwds=legend_kwds, **kwargs)
    ax.set_axis_off()
    ax.set_aspect('equal')
    return fig, ax


def plot_local_autocorrelation(moran_loc, gdf, attribute, p=0.05,
                               region_column=None, mask=None,
                               mask_color='#636363', quadrant=None,
                               legend=True, scheme='Quantiles',
                               cmap='YlGnBu', figsize=(15,4)):
    '''
    Produce three-plot visualization of Moran Scatteprlot, LISA cluster
    and Choropleth, with Local Moran region and quadrant masking

    Parameters
    ----------
    moran_loc : esda.moran.Moran_Local instance
        Values of Moran's Local Autocorrelation Statistic
    gdf : geopandas dataframe
        The Dataframe containing information to plot the two maps.
    attribute : str
        Column name of attribute which should be depicted in Choropleth map.
    p : float, optional
        The p-value threshold for significance. Points and polygons will
        be colored by significance. Default = 0.05.
    region_column: string, optional
        Column name containing mask region of interest. Default = None
    mask: str, optional
        Identifier or name of the region to highlight. Default = None
    mask_color: str, optional
        Color of mask. Default = '#636363'
    quadrant : int, optional
        Quadrant 1-4 in scatterplot masking values in LISA cluster and
        Choropleth maps. Default = None
    figsize: tuple, optional
        W, h of figure. Default = (15,4)
    legend: boolean, optional
        If True, legend for maps will be depicted. Default = True
    scheme: str, optional
        Name of PySAL classifier to be used. Default = 'Quantiles'
    cmap: str, optional
        Name of matplotlib colormap used for plotting the Choropleth.
        Default = 'YlGnBU'

    Returns
    -------
    fig : Matplotlib figure instance
        Moran Scatterplot, LISA cluster map and Choropleth

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import libpysal.api as lp
    >>> from libpysal import examples
    >>> import geopandas as gpd
    >>> import esda
    >>> from splot.esda import plot_local_autocorrelation

    >>> link = examples.get_path('columbus.shp')
    >>> gdf = gpd.read_file(link)
    >>> y = gdf['HOVAL'].values
    >>> w = lp.Queen.from_dataframe(gdf)
    >>> w.transform = 'r'
    >>> moran_loc = esda.moran.Moran_Local(y, w)

    >>> # test with quadrant and mask
    >>> fig = plot_local_autocorrelation(moran_loc, gdf, 'HOVAL', p=0.05,
    ...                                  region_column='POLYID',
    ...                                  mask=['1', '2', '3'], quadrant=1)
    >>> plt.show()
    '''
    fig, axs = plt.subplots(1, 3, figsize=figsize,
                            subplot_kw={'aspect': 'equal'})
    # Moran Scatterplot
    moran_loc_scatterplot(moran_loc, xlabel='Response', ylabel='Spatial Lag',
                     title='Moran Scatterplot', p=p, ax=axs[0])
    axs[0].set_aspect('auto')

    # Lisa cluster map
    # TODO: Fix legend_kwds: display boxes instead of points
    lisa_cluster(moran_loc, gdf, p=p, ax=axs[1], legend=legend,
                 legend_kwds={'loc': 'upper left',
                 'bbox_to_anchor': (0.92, 1.05)})
    axs[1].set_aspect('equal')

    # Choropleth for attribute
    gdf.plot(column=attribute, scheme=scheme, cmap=cmap,
            legend=legend, legend_kwds={'loc': 'upper left',
                                        'bbox_to_anchor': (0.92, 1.05)},
            ax=axs[2], alpha=1)
    axs[2].set_axis_off()
    axs[2].set_aspect('equal')

    # MASKING QUADRANT VALUES
    if quadrant is not None:
        # Quadrant masking in Scatterplot
        mask_angles = {1: 0, 2: 90, 3: 180, 4: 270}   # rectangle angles
        # We don't want to change the axis data limits, so use the current ones
        xmin, xmax = axs[0].get_xlim()
        ymin, ymax = axs[0].get_ylim()
        # We are rotating, so we start from 0 degrees and
        # figured out the right dimensions for the rectangles for other angles
        mask_width = {1: abs(xmax),
                      2: abs(ymax),
                      3: abs(xmin),
                      4: abs(ymin)}
        mask_height = {1: abs(ymax),
                       2: abs(xmin),
                       3: abs(ymin),
                       4: abs(xmax)}
        axs[0].add_patch(patches.Rectangle((0, 0), width=mask_width[quadrant],
                                           height=mask_height[quadrant],
                                           angle=mask_angles[quadrant],
                                           color='grey', zorder=-1, alpha=0.8))
        # quadrant selection in maps
        non_quadrant = ~(moran_loc.q == quadrant)
        mask_quadrant = gdf[non_quadrant]
        df_quadrant = gdf.iloc[~non_quadrant]
        union2 = df_quadrant.unary_union.boundary

        # LISA Cluster mask and cluster boundary
        mask_quadrant.plot(column=attribute, scheme=scheme, color='white',
                           ax=axs[1], alpha=0.7, zorder=1)
        gpd.GeoSeries([union2]).plot(linewidth=2, ax=axs[1], color='darkgrey')

        # CHOROPLETH MASK
        mask_quadrant.plot(column=attribute, scheme=scheme, color='white',
                           ax=axs[2], alpha=0.7, zorder=1)
        gpd.GeoSeries([union2]).plot(linewidth=2, ax=axs[2], color='darkgrey')

    # REGION MASKING
    if region_column is not None:
        # masking inside axs[0] or Moran Scatterplot
        ix = gdf[region_column].isin(mask)
        df_mask = gdf[ix]
        x_mask = moran_loc.z[ix]
        y_mask = ps.lag_spatial(moran_loc.w, moran_loc.z)[ix]
        axs[0].plot(x_mask, y_mask, color=mask_color, marker='o',
                    markersize=14, alpha=.8, linestyle="None", zorder=-1)

        # masking inside axs[1] or Lisa cluster map
        union = df_mask.unary_union.boundary
        gpd.GeoSeries([union]).plot(linewidth=2, ax=axs[1], color=mask_color)

        # masking inside axs[2] or Chloropleth
        gpd.GeoSeries([union]).plot(linewidth=2, ax=axs[2], color=mask_color)
    return fig, axs
