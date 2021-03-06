"""
Spectrum Layer Plotting
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from qtpy.QtGui import *

from astropy.units import spectral_density, spectral, Unit

import pyqtgraph as pg
import logging
import numpy as np

__all__ = [
    'LinePlot',
]


class LinePlot(object):
    """
    Plot representation of a layer

    Parameters
    ----------
    layer: `Spectrum1DRefLayer`
        The layer to plot

    plot: LinePlot
        LinePlot instance to reuse.

    visible: bool
        If True, the plot will be visible

    style: str
        The plotting style

    pen: str
        If defined, the pen style to use.

    err_pen: str
        If defined, the pen style to use for the error/uncertainty.
    """
    def __init__(self, layer, plot=None, visible=True, style='line',
                 pen=None, err_pen=None, mask_pen=None, color=(0, 0, 0)):
        self._layer = layer
        self.style = style
        self._plot = plot
        self.error = None
        self.mask = None
        self._plot_units = (self._layer.dispersion_unit,
                            self._layer.unit,
                            None)
        self.line_width = 1
        self.mode = None
        self.checked = True

        r, g, b = color
        r, g, b = r * 255, g * 255, b * 255

        rand_pen = pg.mkPen(QColor(r, g, b, 255), width=self.line_width)

        _pen = pg.mkPen(pen, width=self.line_width) if pen is not None else rand_pen

        _inactive_pen = pg.mkPen(QColor(_pen.color().red(),
                                        _pen.color().green(),
                                        _pen.color().blue(),
                                        255))

        _err_pen = err_pen if err_pen is not None else pg.mkPen(
            color=(100, 100, 100, 50))

        _mask_pen = mask_pen if mask_pen is not None else pg.mkPen(
            color=(100, 100, 100, 50))

        self._pen_stash = {'pen_on': pg.mkPen(_pen),
                           'pen_inactive': pg.mkPen(_inactive_pen),
                           'pen_off': pg.mkPen(None),
                           'error_pen_on': _err_pen,
                           'error_pen_off': pg.mkPen(None),
                           'mask_pen_on': _mask_pen,
                           'mask_pen_off': pg.mkPen(None)}

        self.set_plot_visibility(True)
        self.set_error_visibility(True)
        self.set_mask_visibility(False)

        if self._plot is not None:
            self.change_units(self._layer.dispersion_unit,
                              self._layer.unit)

    @staticmethod
    def from_layer(layer, **kwargs):
        """Create a LinePlot from a layer

        Parameters
        ----------
        layer: `Spectrum1DRefLayer`
            The layer to create from.

        kwargs: dict
            Other arguments for `LinePlot` class.

        Returns
        -------
        plot_container:
            The new LinePlot
        """
        plot_data_item = pg.PlotDataItem(layer.masked_dispersion, layer.masked_data)

        plot_container = LinePlot(layer=layer, plot=plot_data_item, **kwargs)

        if plot_container.layer.raw_uncertainty is not None:
            plot_error_item = pg.ErrorBarItem(
                x=plot_container.layer.masked_dispersion.compressed().value,
                y=plot_container.layer.masked_data.compressed().value,
                height=plot_container.layer.raw_uncertainty.compressed().value,
            )
            plot_container.error = plot_error_item

        if plot_container.layer.mask is not None:
            mask = plot_container.layer.mask
            x = plot_container.layer.masked_dispersion.data.value[mask]
            y = plot_container.layer.masked_data.data.value[mask]
            plot_mask_item = pg.ScatterPlotItem(
                x=x,
                y=y,
                symbol='x'
            )
            plot_container.mask = plot_mask_item

        return plot_container

    def change_units(self, x, y=None, z=None):
        """
        Change the displayed units

        Parameters
        ----------
        x: `~astropy.units`
            The new units for the dispersion

        y: `~astropy.units`
            The new units for the flux

        z: `~astropy.units`
            The new units for the multi-spectral dimension.
        """
        is_convert_success = [True, True, True]

        x = x or Unit('')
        y = y or Unit('')

        if not self._layer.dispersion_unit.is_equivalent(
                x, equivalencies=spectral()):
            logging.error("Failed to convert x-axis plot units from [{}] to"
                          " [{}].".format(self._layer.dispersion_unit, x))
            x = None
            is_convert_success[0] = False

        if not self._layer.unit.is_equivalent(
                y, equivalencies=spectral_density(self.layer.masked_dispersion)):
            logging.error("Failed to convert y-axis plot units from [{}] to "
                          "[{}].".format(self._layer.unit, y))
            y = self._layer.unit
            is_convert_success[1] = False

        self._layer.set_units(x, y)
        self._plot_units = (x, y, z)
        self.update()

        return is_convert_success

    def set_plot_visibility(self, show=None, inactive=None):
        """
        Set visibility and active state

        Parameters
        ----------
        show: bool
            If True, show the plot

        inactive: bool
            If True, set plot style to indicate this is not
            the active plot.
        """
        if show is not None:
            if show:
                self._plot.setPen(self._pen_stash['pen_on'])
            else:
                self._plot.setPen(self._pen_stash['pen_off'])

        if inactive is not None:
            if inactive:
                self._plot.setPen(self._pen_stash['pen_inactive'])

    def set_error_visibility(self, show=None):
        """
        Show the error/uncertainty

        Parameters
        ----------
        show: bool
            If True, show the error/uncertainty info.
        """
        if self.error is not None and show is not None:
            if show:
                self.error.setOpts(pen=self._pen_stash['error_pen_on'])
            else:
                self.error.setOpts(pen=self._pen_stash['error_pen_off'])

    def set_mask_visibility(self, show=None):
        """
        Show masked data
        
        Parameters
        ----------
        show: bool
            If True, display data points with mask value True.
        """
        if self.mask is not None and show is not None:
            if show:
                self.mask.setSymbol('x')
                self.mask.setPen(pen=self._pen_stash['mask_pen_on'])
            else:
                self.mask.setSymbol(None)

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, plot_item):
        self._plot = plot_item
        # self._plot.setPen(self.pen)

    @property
    def layer(self):
        return self._layer

    @property
    def pen(self):
        return self._pen_stash['pen_on']

    @pen.setter
    def pen(self, pen):
        if isinstance(pen, QColor):
            pen = pg.mkPen(pen)

        _inactive_pen = pg.mkPen(QColor(pen.color().red(),
                                        pen.color().green(),
                                        pen.color().blue(),
                                        50))

        if self._plot.opts['pen'] == self._pen_stash['pen_on']:
            self._pen_stash['pen_on'] = pg.mkPen(pen, width=self.line_width)
            self._plot.setPen(self._pen_stash['pen_on'])
        elif self._plot.opts['pen'] == self._pen_stash['pen_inactive']:
            self._pen_stash['pen_inactive'] = _inactive_pen
            self._plot.setPen(self._pen_stash['pen_inactive'])

    @property
    def error_pen(self):
        return self._pen_stash['error_pen_on']

    @error_pen.setter
    def error_pen(self, pen):
        self._pen_stash['error_pen_on'] = pg.mkPen(pen)

        if self.error is not None:
            self.error.setOpts(pen=pg.mkPen(pen))

    @property
    def mask_pen(self):
        return self._pen_stash['mask_pen_on']

    @mask_pen.setter
    def mask_pen(self, pen):
        self._pen_stash['mask_pen_on'] = pg.mkPen(pen)

        if self.error is not None:
            self.error.setPen(pen=pg.mkPen(pen))

    def set_mode(self, mode):
        """
        Set the line plotting mode

        Parameters
        ----------
        mode: 'line' | 'scatter | 'histogram'
            The plot mode
        """
        if mode in ['line', 'scatter', 'histogram']:
            self.mode = mode
        else:
            self.mode = None

        self.update()

    def set_line_width(self, width):
        """
        Set the line plot width

        Parameters
        ----------
        width: float
            The width of the line
        """
        self.line_width = width
        _pen = pg.mkPen(self._plot.opts['pen'])
        _pen.setWidth(self.line_width)
        self.pen = _pen

    def update(self, autoscale=False):
        """
        Refresh the plot

        Parameters
        ----------
        autoscale: bool
            If True, rescale the plot to match the data.
        """
        if hasattr(self.layer, '_model'):
            disp = self.layer.unmasked_dispersion.compressed().value
            data = self.layer.unmasked_data.compressed().value
            uncert = self.layer.unmasked_raw_uncertainty.compressed().value

        else:
            disp = self.layer.masked_dispersion.compressed().value
            data = self.layer.masked_data.compressed().value
            uncert = self.layer.raw_uncertainty.compressed().value

        # Change specific marker for scatter plot rendering
        symbol = 'o' if self.mode == 'scatter' else None
        pen = None if self.mode == 'scatter' else self.pen

        # Change specific style for histogram rendering
        stepMode = True if self.mode == 'histogram' else False
        disp = np.append(disp, disp[-1]) if self.mode == 'histogram' else disp

        self._plot.setData(disp,
                           data,
                           symbol=symbol,
                           stepMode=stepMode,
                           pen=pen)

        if self.error is not None:
            self.error.setData(x=disp[:-1] if self.mode == 'histogram' else disp,
                               y=data, height=uncert)
        if self.mask is not None:
            mask = self.layer.mask
            x = self.layer.masked_dispersion.data.value[mask]
            y = self.layer.masked_data.data.value[mask]
            self.mask.setData(x=x, y=y)
