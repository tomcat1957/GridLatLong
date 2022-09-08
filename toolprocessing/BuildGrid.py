import time
from pathlib import Path

import PySide2
import axipy
from PySide2 import QtCore
from PySide2.QtWidgets import QProgressDialog
from axipy import Schema, Attribute, provider_manager, Pnt, LineString, Feature, Point, Style

from GridMarker.toolprocessing.DopTool import decdeg2dms


def gradToGGMM(value):
    pass
def createPolylineX(current_x,points_y,cs):
    points=[]
    for pnt_y in points_y:
        points.append(Pnt(current_x,pnt_y))
    geometry=LineString(points,cs)
    return geometry
def createPolylineY(current_y,points_x,cs):
    points=[]
    for pnt_x in points_x:
        points.append(Pnt(pnt_x,current_y))
    geometry=LineString(points,cs)
    return geometry
class PolyLineGridX:
    def __init__(self,xmin,xmax,step,add_intreval,format,cs,style):
        self.val_min=xmin
        self.val_max=xmax
        self.step=step
        self.format=format
        self.add_interval=add_intreval
        self.cs=cs
        self.style=style
        self.start_value=calc_min_start(xmin,step)
        self.end_value=calc_max_start(xmax,step)
        self.style_point= Style.from_mapinfo("Symbol (31, 0, 12)")
    def getPointsX(self):
        x_coords=createCoordBase(self.start_value,self.end_value,self.step,self.add_interval)
        curent_step=self.step/(self.add_interval+1)
        if self.val_min<self.start_value:
            x_coords.insert(0,self.val_min)

            cur_value=self.start_value-curent_step
            while(cur_value>self.val_min):
                x_coords.insert(1,cur_value)
                cur_value=cur_value-curent_step

        if self.end_value<self.val_max:
            cur_value=self.end_value
            while(cur_value<self.val_max):
                x_coords.append(cur_value)
                cur_value=cur_value+curent_step

            x_coords.append(self.val_max)
        return x_coords
    def getLabel(self,curent_value):
        if self.format ==1:
            degri,minuts,sec=decdeg2dms(curent_value)
            str_label=str(degri)+'°'+str(minuts)+"'"
            if sec >0:
                str_sec="%0.2f"%sec
                if not (str_sec=='0.00' or str_sec=='0,00'):
                    str_label=str_label+str_sec+'"'
                else:
                    if str_label.find("°0'"):
                        str_label=str(degri)+'°'
            else:
                if str_label.find("°0'"):
                    str_label=str(degri)+'°'
        else:
            str_label="%0.2f"%curent_value
            if str_label.find(".00"):
                str_label=str_label.replace(".00","")
            else:
                if str_label.find(",00"):
                    str_label=str_label.replace(",00","")
        return str_label
    def getFeature(self,curent_y):
        points_x=self.getPointsX()
        geometry=createPolylineY(curent_y,points_x,self.cs)
        str_label=self.getLabel(curent_y)
        list_features=[]
        ft=Feature({'label_text':str_label,'value_label':curent_y},geometry,self.style)
        list_features.append(ft)
        point_l=Point(points_x[0],curent_y,self.cs)
        ft_pt_l=Feature({'label_text':str_label,'value_label':curent_y,'label_side':'L'},point_l,self.style_point)
        list_features.append(ft_pt_l)
        point_r=Point(points_x[len(points_x)-1],curent_y,self.cs)
        ft_pt_r=Feature({'label_text':str_label,'value_label':curent_y,'label_side':'R'},point_r,self.style_point)
        list_features.append(ft_pt_r)
        return list_features

class PolyLineGridY(PolyLineGridX):
    def getFeature(self,curent_x):
        points_y=self.getPointsX()
        geometry=createPolylineX(curent_x,points_y,self.cs)
        str_label=self.getLabel(curent_x)
        ft=Feature({'label_text':str(str_label),'value_label':curent_x},geometry,self.style)
        list_features=[]
        list_features.append(ft)
        point_l=Point(curent_x,points_y[0],self.cs)
        ft_pt_l=Feature({'label_text':str_label,'value_label':curent_x,'label_side':'D'},point_l,self.style_point)
        list_features.append(ft_pt_l)
        point_r=Point(curent_x,points_y[len(points_y)-1],self.cs)
        ft_pt_r=Feature({'label_text':str_label,'value_label':curent_x,'label_side':'U'},point_r,self.style_point)
        list_features.append(ft_pt_r)
        return list_features

def calc_min_start(value,step):
    temp_val=int(value/step)
    new_value=temp_val*step
    if new_value<value:
        return new_value+step
    return new_value
def calc_max_start(value,step):
    temp_val=int(value/step)
    new_value=temp_val*step
    if new_value>value:
        return new_value-step
    return new_value
def createCoordBase(start_v,end_v,step,add_interval):
    curent_step=step/(add_interval+1)
    current_v=start_v
    out_values=[]
    while(current_v<=end_v):
        out_values.append(current_v)
        current_v=current_v+curent_step
    return out_values

def creatTableOut(path_out,str_cs):
    schema = Schema(
        Attribute.string('label_text', 30),
        Attribute.float('value_label'),
        Attribute.string('label_side', 6),
        coordsystem=str_cs
    )
    name_tab=Path(path_out).resolve().stem
    table = provider_manager.createfile(path_out, schema)
    table.name=name_tab
    return table

def initProgressBar(head,message,count):
    cls_progressbar = QProgressDialog(axipy.app.mainwindow.qt_object())
    cls_progressbar.setWindowModality(QtCore.Qt.ApplicationModal)
    cls_progressbar.setWindowFlags(
        cls_progressbar.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint & ~QtCore.Qt.WindowContextHelpButtonHint)
    cls_progressbar.setWindowTitle(head)
    cls_progressbar.setLabelText(message)
    #  progdialog.canceled.connect(self.close)
    cls_progressbar.setRange(0, count)
    return cls_progressbar
def buildGridRun(property_grid):
    xmin=property_grid['xmin']
    xmax=property_grid['xmax']
    ymin=property_grid['ymin']
    ymax=property_grid['ymax']
    step=property_grid['step']
    cs=property_grid['out_cs']
    path_out_tab=property_grid['table_grid']
    style=property_grid['style']
    dop_interval=property_grid['add_interval']

    start_xmin=calc_min_start(xmin,step)
    start_ymin=calc_min_start(ymin,step)
    start_xmax=calc_max_start(xmax,step)
    start_ymax=calc_max_start(ymax,step)
    table_grid=creatTableOut(path_out_tab,"prj:"+cs. prj)
    curent_x=start_xmin
    while(curent_x<=start_xmax):
        y_coords=createCoordBase(start_ymin,start_ymax,step,dop_interval)
        if ymin<start_ymin:
            y_coords.insert(0,ymin)
        if start_ymax<ymax:
            y_coords.append(ymax)
        geometry_line_x=createPolylineX(curent_x,y_coords,cs)
        ft=Feature({'label_1':str(curent_x)},geometry_line_x,style)
        table_grid.insert([ft])
        curent_x=curent_x+step
    jkl=0
def buildGridRun1(property_grid):
    xmin=property_grid['xmin']
    xmax=property_grid['xmax']
    ymin=property_grid['ymin']
    ymax=property_grid['ymax']
    step=property_grid['step']
    cs=property_grid['out_cs']
    path_out_tab=property_grid['table_grid']
    style=property_grid['style']
    dop_interval=property_grid['add_interval']
    format_label=property_grid['format']
    table_grid=creatTableOut(path_out_tab,"prj:"+cs. prj)
    #dop_interval=2
    poly_x=PolyLineGridX(xmin,xmax,step,dop_interval,format_label,cs,style)

    poly_y=PolyLineGridY(ymin,ymax,step,dop_interval,format_label,cs,style)
    count_object=0
    count_object=int((ymax-ymin)/step)
    count_object=count_object+int((xmax-xmin)/step)
    prg_bar=initProgressBar("Построение сетки","Оси Y",count_object)
    prg_bar.show()
    prg_bar.setValue(0)
    index_ft=0
    if poly_y.start_value>ymin:
        ft=poly_x.getFeature(ymin)
        table_grid.insert(ft)
    curent_y=poly_y.start_value
    isCancel=False
    while(curent_y<poly_y.val_max):
        index_ft=index_ft+1
        ft_list=poly_x.getFeature(curent_y)
        table_grid.insert(ft_list)
        curent_y=curent_y+step
        if prg_bar is not None:
            time.sleep(0.001)
            if prg_bar.wasCanceled():
                isCancel=True
                break
            prg_bar.setValue(index_ft)
    if isCancel:
        prg_bar.close()
        prg_bar=None
        return
    if poly_y.end_value<ymax:
        ft_list=poly_x.getFeature(ymax)
        table_grid.insert(ft_list)
    if poly_x.start_value>xmin:
        ft_list=poly_y.getFeature(xmin)
        table_grid.insert(ft_list)
    curent_x=poly_x.start_value
    prg_bar.setLabelText("Оси X")
    while(curent_x<poly_x.val_max):
        index_ft=index_ft+1
        ft_list=poly_y.getFeature(curent_x)
        table_grid.insert(ft_list)
        curent_x=curent_x+step
        if prg_bar is not None:
            time.sleep(0.001)
            if prg_bar.wasCanceled():
                isCancel=True
                break
            prg_bar.setValue(index_ft)
    if poly_x.end_value<xmax:
        ft_list=poly_y.getFeature(xmax)
        table_grid.insert(ft_list)
    prg_bar.close()
    if isCancel:
        table_grid.close()

    prg_bar=None
    return not isCancel,table_grid
def addTabToMapAndDecor(table_grid):
    layer_base= axipy.Layer.create(table_grid)
    map_view=axipy.app.mainwindow.add_layer_interactive(layer_base)
    isMapView=isinstance(map_view, axipy.MapView)
    if map_view is None:
        return
    list_propertyes=[]
    list_propertyes.append({'name_prefix':'метки_запад','side':'L'})
    list_propertyes.append({'name_prefix':'метки_восток','side':'R'})
    list_propertyes.append({'name_prefix':'метки_юг','side':'D'})
    list_propertyes.append({'name_prefix':'метки_север','side':'U'})
    list_label_table=[]
    list_layer_label=[]
    for label_layer in list_propertyes:
        sql="Select * from "+table_grid.name+" where label_side ='"+label_layer['side']+"'"
        list_label_table.append(axipy.da.data_manager.query(sql))
        list_label_table[-1].name=table_grid.name+"_"+label_layer['name_prefix']
        list_layer_label.append(axipy.Layer.create(list_label_table[-1]))
        list_layer_label[-1].label.text='label_text'
        map_view.map.layers.add(list_layer_label[-1])

    jkl=0







