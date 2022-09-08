import axipy
from axipy import Rect, Point, CoordSystem, Polygon


class DoubleRect:
    __xmin=None
    __ymin=None
    __xmax=None
    __ymax=None
    def __init__(self,cs:CoordSystem,xmin=None,ymin=None,xmax=None,ymaх=None):
        self.__cs=cs
        self.__xmin=xmin
        self.__ymin=ymin
        self.__xmax=xmax
        self.__ymax=ymaх
    @property
    def xmin(self):
        return self.__xmin
    @property
    def ymin(self):
        return self.__ymin
    @property
    def xmax(self):
        return self.__xmax
    @property
    def ymax(self):
        return self.__ymax
    def merge(self,rect:Rect ):
        if rect.xmin<self.__xmin:
            self.__xmin=rect.xmin
        if rect.xmax>self.__xmax:
            self.__xmax=rect.xmax
        if rect.ymin<self.__ymin:
            self.__ymin=rect.ymin
        if rect.ymax>self.__ymax:
            self.__ymax=rect.ymax
    @property
    def coordsystem(self):
        return self.__cs
    def mergePoint(self,point:Point):
        if self.__xmin is None or self.__xmax is None or self.__ymin is None or self.__ymax is None:
            self.__xmin=point.x
            self.__ymin=point.y
            self.__xmax=point.x
            self.__ymax=point.y
            return
        if point.x<self.__xmin:
            self.__xmin=point.x
        if point.x>self.__xmax:
            self.__xmax=point.x
        if point.y<self.__ymin:
            self.__ymin=point.y
        if point.y>self.__ymax:
            self.__ymax=point.y
        return
    def reproject(self,new_cs):
        poly=Polygon.from_rect(Rect(self.__xmin,self.__ymin,self.__xmax,self.__ymax),self.__cs)
        poly_rep=poly.reproject(new_cs)
        bound=poly_rep.bounds
        return DoubleRect(new_cs,bound.xmin,bound.ymin,bound.xmax,bound.ymax)

def decdeg2dms(dd):
    negative = dd < 0
    dd = abs(dd)
    minutes,seconds = divmod(dd*3600,60)
    degrees,minutes = divmod(minutes,60)
    if negative:
        if degrees > 0:
            degrees = -degrees
        elif minutes > 0:
            minutes = -minutes
        else:
            seconds = -seconds
    return int(degrees),int(minutes),seconds
def findCoordSysCosmetic():
    for mv in axipy.gui.view_manager.mapviews:
        if mv.map.cosmetic.data_object == axipy.gui.selection_manager.table:
            return mv.coordsystem
    return None
        #print('compare', mv.map.cosmetic.data_object == axipy.gui.selection_manager.table)
def existSelectionObject():
    if axipy.gui.selection_manager.count>0:
        return True
    return False
def getCsAndRectSelection():
    isCosmetic=False
    if axipy.gui.selection_manager.count==0:
        return None,None
    if axipy.gui.selection_manager.table.name=='Косметический_слой':
        isCosmetic=True
    bound_sel=None
    for f in axipy.gui.selection_manager.get_as_cursor():
        if f.geometry is None:
            continue
        if f.geometry.type== axipy.GeometryType.Polygon:

            #temp_geometry=f.geometry.reproject(self.__base_cs)
            #temp_rect=temp_geometry.bounds
            ft_rect=f.geometry.bounds
            if bound_sel is None:
                bound_sel=DoubleRect(f.geometry.coordsystem,ft_rect.xmin, ft_rect.ymin,ft_rect.xmax,ft_rect.ymax)
            else:
                bound_sel.merge(ft_rect)
    if bound_sel is None:
        return None,None
    if not isCosmetic:
        ''' не косметика'''
        return axipy.gui.selection_manager.table.coordsystem,bound_sel
    cs_map_project=findCoordSysCosmetic()
    source_bound=DoubleRect(axipy.gui.selection_manager.table.coordsystem,bound_sel.xmin,bound_sel.ymin,bound_sel.xmax,bound_sel.ymax)
    '''
    pt_1=Point(bound_sel.xmin,bound_sel.ymin,axipy.gui.selection_manager.table.coordsystem)
    pt_1_r=pt_1.reproject(cs_map_project)
    out_bound=DoubleRect(cs_map_project)
    out_bound.mergePoint(pt_1_r)
    pt_1=Point(bound_sel.xmin,bound_sel.ymax,axipy.gui.selection_manager.table.coordsystem)
    pt_1_r=pt_1.reproject(cs_map_project)
    out_bound.mergePoint(pt_1_r)
    pt_1=Point(bound_sel.xmax,bound_sel.ymax,axipy.gui.selection_manager.table.coordsystem)
    pt_1_r=pt_1.reproject(cs_map_project)
    out_bound.mergePoint(pt_1_r)
    pt_1=Point(bound_sel.xmax,bound_sel.ymin,axipy.gui.selection_manager.table.coordsystem)
    pt_1_r=pt_1.reproject(cs_map_project)
    out_bound.mergePoint(pt_1_r)
    '''
    out_bound=source_bound.reproject(cs_map_project)
    return cs_map_project,out_bound
def findAvtoStep(xmin,ymin,xmax,ymax,def_count_interval=5):
    dx=xmax-xmin
    dy=ymax-ymin
    d=dx
    if dx>dy:
        d=dy
    step_def=d/def_count_interval
    isFind=False
    level=0
    while(not isFind):
        new_step_round=int(round(step_def,level))
        if new_step_round==0:
            break
        level=level-1
    step=int(round(step_def,level+1))
    return step
def findStepInIntervals(curent_value,intervals,list_times):
    step_temp=int(curent_value/intervals)
    for index_min in list_times:
        if int(step_temp/index_min)>=1:
            return index_min
    return 0
def findAvtoStepLatLong(xmin,ymin,xmax,ymax,def_count_interval=7):
    dx=xmax-xmin
    dy=ymax-ymin
    d=dx
    if dx>dy:
        d=dy
    deg,min,sec=decdeg2dms(d)
    if deg>=def_count_interval:
        ''' шаг явно в градусах'''
        step_temp=int(deg/def_count_interval)
        return step_temp
    ''' переводим все в минуты '''
    temp_minutes=deg*60+min
    step_in_minutes=findStepInIntervals(temp_minutes,def_count_interval,[15,10,5,1])
    if step_in_minutes>0:
        return step_in_minutes/60
    temp_sec=min*60+sec
    step_in_sec=findStepInIntervals(temp_sec,def_count_interval,[30,15,10,5,1])
    if step_in_sec>0:
        return step_in_sec/3600
    temp_interval_grad=temp_sec/3600
    return temp_interval_grad






