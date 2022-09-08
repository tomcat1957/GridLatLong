import os
from pathlib import Path

import axipy
from PySide2 import QtCore
from PySide2.QtCore import QFile
from PySide2.QtGui import QDoubleValidator, QIntValidator
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QDialog, QFileDialog
from axipy import CoordSystem, ChooseCoordSystemDialog, Rect, Geometry, GeometryType

from .DopTool import DoubleRect, getCsAndRectSelection, findAvtoStep, findAvtoStepLatLong, decdeg2dms
from .Utils import readPropertyes, saveProperties


class DlgGridBuilder(QDialog):
    __bound_sel=None
    __def_style_line='Pen (1, 2, 0)'
    __name_plugin = 'MapGridBuilder'
    __name_file_plugin_proporties = 'MapGridBuilder_properties.json'
    __isOk=False
    def __init__(self,base_cs=None,parent=None):

        self.__parent=parent
        self.__base_cs=base_cs
        self.load_ui()
        self.__ui.setWindowFlags(
            self.__ui.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint & ~QtCore.Qt.WindowContextHelpButtonHint)
        if base_cs is None:
            self.__base_cs=CoordSystem.from_epsg(4326)
        db_validator=QDoubleValidator()
        db_validator.setBottom(0.00001)
        int_validator=QIntValidator(0,10)
        self.__ui.ln_step_line.setValidator(db_validator)
        self.__ui.ln_add_points.setValidator(int_validator)
        self.__curent_coord_sys=self.__base_cs
        self.__update_bound_for_coordsys(self.__base_cs)
        self.__ui.pb_change_coodsys.clicked.connect(self.__change_coordsys)
        self.__ui.pb_run.clicked.connect(self.__run)
        self.__ui.ch_using_obj.stateChanged.connect(self.__change_using_selection)
        self.__ui.ln_edit_out_tab.textChanged.connect(self.__change_out_tab)
        self.__ui.pb_update_step.clicked.connect(self.__update_step)
        self.__ui.pb_cancel.clicked.connect(self.__cancel)
        self.__ui.pb_saveAs.clicked.connect(self.__selectFileSave)
        self.__ui.cm_format_label_grd.currentIndexChanged.connect(self.__change_format_label)
        self.__ui.ln_step_line.textChanged.connect(self.__change_step)
        self.__isSelectObj()
        self.__initFormatGradus()
        home = str(Path.home())
        out_tab=os.path.join(home,"Сетка.tab")
        self.__ui.ln_edit_out_tab.setText(out_tab)
        self.__readInitStyle()
        self.__init_style()
        self.__widgetStyle()
    def load_ui(self):
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "DlgBuildGrid.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.__ui  = loader.load(ui_file,self.__parent)
        ui_file.close()
    def __update_bound_for_coordsys(self,curent_cs:CoordSystem,rect=None):
        self.__ui.lb_curent_prj.setText(curent_cs.name)
        line_unit_cs=curent_cs.unit
        name_line_unit=line_unit_cs.name
        self.__ui.label_unit_north.setText(name_line_unit)
        self.__ui.label_unit_south.setText(name_line_unit)
        self.__ui.label_unit_east.setText(name_line_unit)
        self.__ui.label_unit_west.setText(name_line_unit)
        self.__ui.lb_unti_step_line.setText(name_line_unit)
        cs_rect=curent_cs.rect
        if rect is not None:
            cs_rect=rect
        '''
        if self.__ui.ch_using_obj.isChecked():
            cs_rect=self.__bound_sel
        '''
        '''
        self.__ui.ln_bnd_north.setText(str(cs_rect.ymax))
        self.__ui.ln_bnd_south.setText(str(cs_rect.ymin))
        self.__ui.ln_bnd_east.setText(str(cs_rect.xmax))
        self.__ui.ln_bnd_west.setText(str(cs_rect.xmin))
        '''
        xmin,ymin,xmax,ymax=self.__fromat_bound(curent_cs,cs_rect)
        self.__ui.ln_bnd_north.setText(ymax)
        self.__ui.ln_bnd_south.setText(ymin)
        self.__ui.ln_bnd_east.setText(xmax)
        self.__ui.ln_bnd_west.setText(xmin)
    def __change_coordsys(self):
        dlg = ChooseCoordSystemDialog(self.__curent_coord_sys)
        if dlg.exec() == QDialog.Accepted:
            self.__curent_coord_sys=dlg.chosenCoordSystem()
            if self.__ui.ch_using_obj.isChecked():
                new_bound=self.__bound_sel.reproject(self.__curent_coord_sys)
                self.__update_bound_for_coordsys(self.__curent_coord_sys,new_bound)
                self.__bound_sel=new_bound
            else:
                self.__update_bound_for_coordsys(self.__curent_coord_sys)
            self.__calcStep()
            self.__ui.group_grag.setEnabled(self.__curent_coord_sys.lat_lon)
    def __change_format_label(self):
        self.__update_step()
        if not(self.__curent_coord_sys.lat_lon) or self.__ui.cm_format_label_grd.currentIndex()==0:
            self.__ui.labestep_grad.setText("")

    def __change_step(self):
        xmin=float(self.__ui.ln_bnd_west.text())
        xmax=float(self.__ui.ln_bnd_east.text())
        ymin=float(self.__ui.ln_bnd_south.text())
        ymax=float(self.__ui.ln_bnd_north.text())
        curent_rec=DoubleRect(self.__curent_coord_sys,xmin,ymin,xmax,ymax)
        curent_step=float(self.__ui.ln_step_line.text())
        self.__update_info_objects(curent_rec,curent_step)
        if self.__curent_coord_sys.lat_lon and self.__ui.cm_format_label_grd.currentIndex()==1:
            grad,min,sec=decdeg2dms(curent_step)
            grad_str_step=str(grad)+'°'+str(min)+"'"+f'{sec:0.1f}'+'"'
            self.__ui.labestep_grad.setText(grad_str_step)
        else:
            self.__ui.labestep_grad.setText("")

    def __run(self):
        self.__writeIniStyle()
        self.__isOk=True
        self.__ui.close()
    def __cancel(self):
        self.__isOk=False
        self.__ui.close()
    @property
    def isOk(self):
        return self.__isOk
    @property
    def dataForBuild(self):
        xmin=float(self.__ui.ln_bnd_west.text())
        xmax=float(self.__ui.ln_bnd_east.text())
        ymin=float(self.__ui.ln_bnd_south.text())
        ymax=float(self.__ui.ln_bnd_north.text())
        property_grid={}
        property_grid['xmin']=xmin
        property_grid['xmax']=xmax
        property_grid['ymin']=ymin
        property_grid['ymax']=ymax
        property_grid['step']=self.__curent_step
        property_grid['out_cs']=self.__curent_coord_sys
        property_grid['table_grid']=self.__ui.ln_edit_out_tab.text()
        property_grid['style']=self.__pb_style_line.style()
        property_grid['add_interval']=int(self.__ui.ln_add_points.text())
        property_grid['format']= self.__ui.cm_format_label_grd.currentIndex()
        if not self.__ui.cm_format_label_grd.isEnabled():
            property_grid['format']=0
        return property_grid
    def __calcStep(self,rect=None):
        curent_step=None
        curent_rec=None
        if self.__ui.ch_using_obj.isChecked():
            curent_rec=self.__bound_sel
        else:
            curent_rec=DoubleRect(self.__curent_coord_sys,self.__curent_coord_sys.rect.xmin,self.__curent_coord_sys.rect.ymin,self.__curent_coord_sys.rect.xmax,self.__curent_coord_sys.rect.ymax)
        if rect is not None:
            curent_rec=rect
        if self.__curent_coord_sys.lat_lon:
            curent_step=findAvtoStepLatLong(curent_rec.xmin,curent_rec.ymin,curent_rec.xmax,curent_rec.ymax)
        else:

            curent_step=findAvtoStep(curent_rec.xmin,curent_rec.ymin,curent_rec.xmax,curent_rec.ymax)
        if curent_step is not None:
            str_step_value=None
            if curent_rec.coordsystem.lat_lon:
                str_step_value=f'{curent_step:0.6f}'
                if self.__ui.cm_format_label_grd.currentIndex()==1:
                    grad,min,sec=decdeg2dms(curent_step)
                    grad_str_step=str(grad)+'°'+str(min)+"'"+f'{sec:0.1f}'+'"'
                    self.__ui.labestep_grad.setText(grad_str_step)
            else:
                str_step_value=f'{curent_step:0.2f}'
                self.__ui.labestep_grad.setText("")
            self.__curent_step=curent_step
            self.__ui.ln_step_line.setText(str_step_value)
            self.__update_info_objects(curent_rec,curent_step)
    def __isSelectObj(self):
        count_sel=axipy.gui.selection_manager.count
        if count_sel==0:
            self.__ui.ch_using_obj.setEnabled(False)
            return False
        cs,bound_sel=getCsAndRectSelection()
        if bound_sel is not None:
            self.__bound_sel=bound_sel
            self.__cs_bound_sel=cs
            self.__ui.ch_using_obj.setEnabled(True)
            return True
    def __update_info_objects(self,rect,step):
        nx=(rect.xmax-rect.xmin)/step+1
        ny=(rect.ymax-rect.ymin)/step+1
        self.__ui.count_lines.setText(str(int(nx*ny+0.5)))
    def __fromat_bound(self,cs:CoordSystem,bound:Rect):
        if cs.lat_lon:
            xmin=f'{bound.xmin:0.6f}'
            xmax=f'{bound.xmax:0.6f}'
            ymin=f'{bound.ymin:0.6f}'
            ymax=f'{bound.ymax:0.6f}'
            return xmin,ymin,xmax,ymax
        xmin=f'{bound.xmin:0.2f}'
        xmax=f'{bound.xmax:0.2f}'
        ymin=f'{bound.ymin:0.2f}'
        ymax=f'{bound.ymax:0.2f}'
        return xmin,ymin,xmax,ymax
    def __change_using_selection(self):
        if self.__ui.ch_using_obj.isChecked():
            if self.__bound_sel is not None:
                self.__curent_coord_sys=self.__cs_bound_sel
                self.__ui.lb_curent_prj.setText(self.__curent_coord_sys.name)
                self.__update_bound_for_coordsys(self.__curent_coord_sys,self.__bound_sel)
                self.__ui.group_grag.setEnabled(self.__curent_coord_sys.lat_lon)
                self.__calcStep(self.__bound_sel)
    def __initFormatGradus(self):
        self.__ui.cm_format_label_grd.addItem("гг.xx")
        #self.__ui.cm_format_label_grd.addItem("гг.мм.xx")
        self.__ui.cm_format_label_grd.addItem("гг.мм.сек.xx")

        self.__ui.group_grag.setEnabled(self.__curent_coord_sys.lat_lon)
    def __update_step(self):
        xmin=float(self.__ui.ln_bnd_west.text())
        xmax=float(self.__ui.ln_bnd_east.text())
        ymin=float(self.__ui.ln_bnd_south.text())
        ymax=float(self.__ui.ln_bnd_north.text())
        rect=DoubleRect(self.__curent_coord_sys,xmin,ymin,xmax,ymax)
        self.__calcStep(rect)

    def __selectFileSave(self):
        ext_files = "MapInfo tab (*.tab)"
        name_load_file = QFileDialog.getSaveFileName(self.__ui, 'Выбрать файл с диска',self.__ui.ln_edit_out_tab.text(), ext_files)
                                                     #options = QFileDialog.DontConfirmOverwrite)
        if name_load_file is None:
            return
        file_tab=name_load_file[0]
        self.__ui.ln_edit_out_tab.setText(file_tab)
    def __change_out_tab(self):
        path_out=self.__ui.ln_edit_out_tab.text()
        path_file=Path(path_out)
        self.__ui.pb_run.setEnabled(os.path.isdir(str(path_file.parent)))
    def __readInitStyle(self):
        try:
            obj_property=readPropertyes(self.__name_plugin,self.__name_file_plugin_proporties)
            self.__style_line=axipy.Style.from_mapinfo(obj_property['line_style'])
        except:
            obj_property=None
        if obj_property is None:
            self.__style_line=axipy.Style.from_mapinfo(self.__def_style_line)
    def __init_style(self):

        self.__pb_style_line = axipy.StyledButton(self.__style_line, self.__ui)
        self.__pb_style_line.setFixedHeight(40)
        self.__pb_style_line.setFixedWidth(40)
        self.__pb_style_line.setEnabled(True)
    def __widgetStyle(self):
        self.__ui.wg_style_line.addWidget(self.__pb_style_line)
    def __writeIniStyle(self):
        property_plugins={}
        property_plugins['line_style']=self.__pb_style_line.style().to_mapinfo()

        saveProperties(self.__name_plugin,self.__name_file_plugin_proporties,property_plugins)
    def show(self):
        #isNotSelect=self.__isSelectObj()

        self.__ui.exec()