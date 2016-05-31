import os
import logging

from ..ui.widgets.utils import ICON_PATH
from ..ui.widgets.plugin import Plugin
from ..core.comms import Dispatch, DispatchHandle
from ..ui.widgets.dialogs import TopAxisDialog, UnitChangeDialog

from astropy.units import Unit


class ToolTrayPlugin(Plugin):
    name = "Tools"
    location = "hidden"
    _all_categories = {}

    def setup_ui(self):
        self._top_axis_dialog = TopAxisDialog()
        self._unit_change_dialog = UnitChangeDialog()

        # Change top axis
        self.add_tool_button(
            description='Change top axis',
            icon_path=os.path.join(ICON_PATH, "Merge Vertical-48.png"),
            category='selections',
            callback=self._unit_change_dialog.exec_)

        # Change top axis
        self.add_tool_button(
            description='Change plot units',
            icon_path=os.path.join(ICON_PATH, "Merge Vertical-48.png"),
            category='selections',
            callback=Dispatch.on_add_roi.emit)

    def setup_connections(self):
        # On accept, change the displayed axis
        self._top_axis_dialog.accepted.connect(lambda:
                                               self.update_axis(
                                                   self._containers[0].layer,
                                                   self._top_axis_dialog.combo_box_axis_mode.currentIndex(),
                                                   redshift=self._top_axis_dialog.redshift,
                                                   ref_wave=self._top_axis_dialog.ref_wave))

    def _show_unit_change_dialog(self):
        if self._unit_change_dialog.exec_():
            x_text = self._unit_change_dialog.disp_unit
            y_text = self._unit_change_dialog.flux_unit

            x_unit = y_unit = None

            try:
                x_unit = Unit(x_text) if x_text else None
            except ValueError as e:
                logging.error(e)

            try:
                y_unit = Unit(y_text) if y_text else None
            except ValueError as e:
                logging.error(e)

            self.change_units(x_unit, y_unit)

            self._plot_item.update()
