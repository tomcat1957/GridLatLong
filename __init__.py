'''
 Построение картографической сетки
'''
import axipy

from .toolprocessing.BuildGrid import buildGridRun1, addTabToMapAndDecor
from .toolprocessing.DlgGridBuilder import DlgGridBuilder


class Plugin:
    def __init__(self, iface):
        self.__dlg_run=None
        self.iface = iface
        menubar = iface.menubar
        tr = iface.tr
        local_file=iface.local_file
        self.__action = menubar.create_button(iface.tr('Картографическая сетка'),
                                              icon=local_file('toolprocessing', 'icon-grid.png'), on_click=self.run_tools)
        position = menubar.get_position(tr('Дополнительно'), tr('Инструменты'))
        position.add(self.__action, size=2)
        self.__catalog=axipy.app.mainwindow.catalog
        self.__selection=axipy.gui.selection_manager
    def unload(self):

        self.iface.menubar.remove(self.__action)
    def run_tools(self):
        #if self.__dlg_run is None:
        self.__dlg_run=DlgGridBuilder(None,axipy.app.mainwindow.qt_object())
        self.__dlg_run.show()
        if self.__dlg_run.isOk:
            property_grid=self.__dlg_run.dataForBuild
            isOkBuild,table_grid=buildGridRun1(property_grid)
            if isOkBuild:
                addTabToMapAndDecor(table_grid)
        self.__dlg_run=None