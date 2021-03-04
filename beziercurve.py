from tkinter import *
import svgwrite
from datetime import datetime

class Window:

    def __init__(self, w, h) -> None:
        
        self.width, self.height = w, h
        self.root = Tk()
        self.root.geometry('{}x{}'.format(w,h))
        self.root.resizable(False,False)
        #self.root.configure(bg='black')
        self.root.title('Bezier Curve')
        
    def createCanvas(self):

        self.canvas = Canvas(self.root, width=self.width, height=self.height-40)
        self.canvas.pack()

class Point:
    points = []
    isDragging = False
    draggable = None

    def __init__(self, canvas: Canvas, x, y, r, isAnchor = False, addGuide = False, closeLoop = False) -> None:
        
        self.x, self.y, self.r = x,y,r
        self.isAnchor = isAnchor
        self.segmentIndex = []
        self.object = canvas.create_oval(x-r, y-r, x+r, y+r, fill='red' if not isAnchor else 'green')

        self.guide = []
        if(addGuide):
            if(not closeLoop): self.guideLine(canvas, Point.points[-1])
            else:  self.guideLine(canvas, Point.points[0])

        self.points.append(self)

    def __repr__(self) -> str:
        return '{},{}'.format(self.x, self.y)

    @classmethod
    def clearAll(cls, canvas: Canvas):
        for p in cls.points:
            canvas.delete(p)
            del(p)
        cls.points = []

    @classmethod
    def checkHit(cls, x, y, radius = None):

        for p in cls.points:
            if(radius == None):
                radius = p.r
            #check if x,y is inside point
            if( (x >= p.x - radius) and (y >= p.y - radius) and
                (x <= p.x + radius) and (y <= p.y + radius)):
                return (True, p)

        return (False,None)

    def moveToCoord(self, canvas, x, y):

        canvas.coords(self.object, x - self.r, y - self.r, x + self.r, y + self.r)
        self.x, self.y = x, y

        if(not self.guide == None):
            for g in self.guide:
                g.move(canvas, self)

    def guideLine(self, canvas: Canvas, endPoint):

        _guide = Guide(canvas, self, endPoint)
        self.guide.append(_guide)
        endPoint.guide.append(_guide)

class Guide:

    def __init__(self, canvas: Canvas, start: Point, end: Point) -> None:
        
        self.start = start
        self.end = end
        self.object = canvas.create_line(start.x,start.y, end.x, end.y)

    def move(self, canvas: Canvas, point: Point):

        if(self.start == point):
            canvas.coords(self.object, point.x, point.y, self.end.x, self.end.y)
        else:
            canvas.coords(self.object, self.start.x, self.start.y, point.x, point.y)

class Bezier:
    #instance = None
    segment = []
    isClosed = False

    def __init__(self, canvas: Canvas, points: list) -> None:
        
        self.curve = [] #list of canvas lines
        for p in points:
            p.segmentIndex.append(len(self.segment))
        self.draw(canvas, 10, points)
        Bezier.segment.append(self)
    
    def draw(self, canvas, segments, points: list):

        _startX, _startY = points[0].x, points[0].y
        
        i = 0
        t = 0
        while(t < 1):
            i+=1
            t = i / segments
            x = pow((1-t),3)*points[0].x + 3*pow((1-t),2)*t*points[1].x + 3*(1-t)*pow(t,2)*points[2].x + pow(t,3)*points[3].x
            y = pow((1-t),3)*points[0].y + 3*pow((1-t),2)*t*points[1].y + 3*(1-t)*pow(t,2)*points[2].y + pow(t,3)*points[3].y

            self.curve.append(canvas.create_line( x,y,_startX, _startY, width='2'))
            _startX, _startY = x,y

    @classmethod
    def redraw(cls, canvas: Canvas, segment):
        
        _points = []
        if (segment == len(cls.segment)-1 and cls.isClosed):
            _points = Point.points[-3:]
            _points.append(Point.points[0])
        else:
            _points = (p for p in Point.points if segment in p.segmentIndex)
            _points = list(_points)

        cls.draw(cls.segment[segment], canvas, 10, _points)

    @classmethod
    def deleteCurve(cls, canvas: Canvas, deleteAll = True, seg = None):

        if(cls.segment == None):
            return

        if(deleteAll):          #delete all segments
            for s in cls.segment:
                for c in s.curve:
                    canvas.delete(c)
                del(s)
            cls.segment = []
            cls.isClosed = False
        else:                   #delete only the last segment
            #print('\na')
            for c in cls.segment[seg].curve:
                canvas.delete(c)
            del(cls.segment[seg].curve)
            cls.segment[seg].curve = []



def placePoint(event):
    
    if(len(Point.points) == 0):
        Point(window.canvas, event.x, event.y, 5)
    else:
        Point(window.canvas, Point.points[-1].x + 10, Point.points[-1].y - 10, 3, True, True)       #prev point anchor
        Point(window.canvas, event.x - 10, event.y + 10, 3, True)                                   #new point anchor
        Point(window.canvas, event.x, event.y, 5, False, True)                                      #new point
        Bezier(window.canvas, Point.points[-4:])
        
def click(event):
    
    if(Bezier.isClosed):
        return

    _hit = Point.checkHit(event.x, event.y)
    if(not _hit[0]):
        placePoint(event)
    del(_hit)

def dragPoint(event):
    
    global dragged
    dragged = True

    if(Point.isDragging):
        Point.draggable.moveToCoord(window.canvas, event.x, event.y)
        if(len(Point.points) >= 4):
            for seg in Point.draggable.segmentIndex:
                Bezier.deleteCurve(window.canvas, False, seg)
                Bezier.redraw(window.canvas, seg)
    else:
        _hit = Point.checkHit(event.x, event.y)
        if(_hit[0]):
            Point.isDragging = True
            Point.draggable = _hit[1]
        del(_hit)

def release(event):
    
    global dragged

    if(Point.isDragging):
        Point.isDragging = False
        Point.draggable = None
    
    if(not (dragged)): #close loop
        _hit = Point.checkHit(event.x, event.y)
        if(len(Point.points) > 1 and _hit[1] == Point.points[0] and not Bezier.isClosed):
            #close path
            Point(window.canvas, Point.points[-1].x + 10, Point.points[-1].y - 10, 3, True, True)
            Point(window.canvas, event.x - 10, event.y + 10, 3, True, True, True)

            _points = Point.points[-3:]
            _points.append(Point.points[0])
            Bezier(window.canvas, _points)
            Bezier.isClosed = True
            del(_points)
        del(_hit)
    dragged = False

def clearCanvas(event):
    
    Bezier.deleteCurve(window.canvas,True)
    Point.clearAll(window.canvas)
    window.canvas.delete("all")
    saveLocation.set('')
    posText.set('(x,y)')

def hoverPoint(event):
    _hit = Point.checkHit(event.x, event.y)
    if(_hit[0]):
        posText.set(_hit[1])
    del(_hit)

def export():
    
    if(len(Point.points) >=4 ):
        SaveSVG()

def SaveSVG():

    _name = str(datetime.now().strftime("%Y%M%D_%H%M%S"))
    _name = 'export{}.svg'.format(_name).replace('/','')
    dwg = svgwrite.Drawing(_name)
    dwg.viewbox(0,0,window.width,window.height-40)

    _path = 'M {} {} '.format(Point.points[0].x, Point.points[0].y)
    for i in range(3, len(Point.points),3):
        _path = _path + 'C {} {}, {} {}, {} {} '.format(Point.points[i-2].x, Point.points[i-2].y,
                                                        Point.points[i-1].x, Point.points[i-1].y,
                                                        Point.points[i].x, Point.points[i].y)
    #print(_path)
    if(Bezier.isClosed):
        _path = _path + 'C {} {}, {} {}, {} {} z'.format(Point.points[-2].x, Point.points[-2].y,
                                                        Point.points[-1].x, Point.points[-1].y,
                                                        Point.points[0].x, Point.points[0].y)

    dwg.add(dwg.path(d= _path, stroke='#000', fill='none'))
    dwg.save()

    saveLocation.set(_name)

dragged = False

if(__name__ == '__main__'):
    window = Window(500,540)
    window.createCanvas()
    window.canvas.bind('<Button-1>', click)
    window.canvas.bind('<B1-Motion>', dragPoint)
    window.canvas.bind('<ButtonRelease-1>', release)
    window.canvas.bind('<Button-3>', clearCanvas)
    window.canvas.bind('<Motion>', hoverPoint)


    exportButton = Button(window.root,width=10, text='Export', command=export)
    exportButton.place(x=10, y=window.height-31)
    saveLocation = StringVar()
    saveLocation.set('')
    locationLabel = Label(window.root, textvariable=saveLocation)
    locationLabel.place(x=100, y=window.height-30)

    posText = StringVar()
    posText.set('(x,y)')
    pointPos = Label(window.root, textvariable=posText)
    pointPos.place(x=0,y=0)

    Label(window.root,text="LMB - Place Point | LMB Drag - Move Point | RMB - Clear Canvas ").place(x=150,y=0)
    window.root.mainloop()