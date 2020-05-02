######################################################################
# program GHreport.py for Python 3.x
#used to output data stored in db by GHctl.py as html & graphics using Bokeh plots
#specifically written for M. Graham’s greenhouse & sensors
#requires library “mymeter.py” by M. Graham
#April 2020
######################################################################
# library imports
from bokeh.plotting import figure, output_file,save 
from bokeh.layouts import row
from math import pi
from datetime import timedelta
import matplotlib.pyplot as plt
plt.ion()
import matplotlib.dates as dtplt
import pymysql as cur
import time
import mymeter as mym     # written by author…copy file to same directory as program


repeats = 2  #set number of time loop will run
while repeats >0:
    #will repeat loop until "repeats =0" - never if following line commented then must use ctrl-c to end pgm
    #repeats=repeats-1 
    sttime=time.time()    #start time -  secs since epoch
    looptime=sttime+300  #5-minute intervals

    ##############get data from dbase##################
    try:
       connection=cur.connect (host=192.168.0.2,   #edit IP address of SQL server
                            user=’user’,
                            password=’password’, #replace with valid username and password for database
                            db='greenhouse',
                            charset='utf8mb4',
                            cursorclass=cur.cursors.DictCursor)
          with connection.cursor() as cursor:
            sql="select max(id) from data" #get index of most recent data
            cursor.execute(sql)
            result=cursor.fetchone()
            comsok=True
    except:
       comsok=False #could not get data from database
    finally:
        connection.close
#end try
    if comsok:
        print(result.get('max(id)')) #print time of most recent data on terminal
        sdate=result.get('max(id)') -timedelta(hours=48) #calculate  time 48 hours prior to last reading
        print(sdate) #print time           
        try:
            with connection.cursor() as cursor:
                sql="select * from data where (id>'%s')"%str(sdate)  #get data less than 48 hours old
                cursor.execute(sql)
                result=cursor.fetchall()
                comsok=True
        except:
           comsok=False 
        finally:
            connection.close
    else:  # no connection to database – print error to terminal
        print()
        print('coms error with databse')
        print()
        
    #################extract data columns to lists#################
    if comsok: # valid data is available – proceed to update graphs 
        #initialize variables
        a=[]
        b=[]
        c=[]
        d=[]
        e=[]
        f=[]
        g=[]
        h=[]
        m=[]
        n=[]
        p=[]
        q=[]
        
        for i in range(len(result)):  #populate data arrays
            a=a+[result[i].get('SoilT')]
            b=b+[result[i].get('Soilm')]
            c=c+[result[i].get('AirT1')]
            d=d+[result[i].get('RH')]
            e=e+[result[i].get('AirT2')]
            f=f+[result[i].get('id')]
            ff=f
            g=g+[result[i].get('IRRtime')]
            h=h+[result[i].get('TankLow')]
            m=m+[result[i].get('TankMT')]
            n=n+[result[i].get('IRRset')]
            p=p+[result[i].get('LT')]
            q=q+[result[i].get('vnt')]
        f=dtplt.date2num(f) #convert time strings to “days since epoch” (a floating point number)

        
        ##########plot the data###################
        # output bokeh plot  to  HTML file
        output_file("/home/pi/Applications/fig1.html")
        fig1=figure(
               tools="pan,box_zoom,reset,save,hover",
               x_axis_type="datetime",
               title="Temperatures in last 48 hours",
               x_axis_label='', y_axis_label='C'
            )             # set up temperature graph
        fig1.hover.tooltips=[("x","@x{%m - %d %H:%M}"),("y","@y{%0.2f}")]  #set tool tip style
        fig1.hover.formatters={
                "x"      : 'datetime', # use 'datetime' formatter for 'date' field
                "y"      : 'printf',   # use 'printf' formatter for 'adj close' field
                }
        #plot lines on graph
        fig1.line(ff,a,color="blue",legend='SoilT')
        fig1.line(ff,c,color="red",legend='AirT1')
        fig1.line(ff,e,color="green",legend='AirT2')
        fig1.xaxis.major_label_orientation = pi/4
        fig1.legend.location="top_left"
        fig1.toolbar_location='above'
        #set up % graphs
        fig2=figure(
               tools="pan,box_zoom,reset,save,hover",
               x_axis_type="datetime",
               title="Moisture content in last 48 hours",
               x_axis_label='', y_axis_label='%'               
            )
         #plot data lines
        fig2.line(ff,b,color="blue",legend='Soil Moisture')
        fig2.line(ff,d,color="red",legend='RH')
        fig2.line(ff,p,color="green",legend='Light (relative to full sun)')
        fig2.xaxis.major_label_orientation = pi/4
        fig2.legend.location="top_left"
        fig2.toolbar_location='above'
        #set tool tip style
        fig2.hover.tooltips=[("x","@x{%m - %d %H:%M}"),("y","@y{%0.2f}")]
        fig2.hover.formatters={
                "x"      : 'datetime', # use 'datetime' formatter for 'date' field
                "y"      : 'printf',   # use 'printf' formatter for 'adj close' field
                }
        save(row(fig1,fig2)) #save the file

       #create “speedometer” graphics
        nowt=max(f)  #find latest recorded time
        fff=list(f)
        nowidx=fff.index(nowt) # get position of "now" data
        curAirT=(c[nowidx]+e[nowidx])/2 #average air T
        curRH=d[nowidx]
        curSoilT=a[nowidx]
        curSoilm=b[nowidx]
        curIRRtime=sum(g)
        curIRRset=n[nowidx]
        curTankLow=h[nowidx]
        curTankMT=m[nowidx]
 
        #using mymeter to plot current data
        plt.ioff()
        plt.close() #clear current graph
       #mymeter.guage (fignumber, min, max, color_range, pointer_value, title, file_name) 
       # use full path for fname. Autostart may start pgm in unexpected directory or with different user
        mym.gauge(30,-10,40, colors='RdBu', arrow=curAirT, title='Air Temperature', fname='/home/pi/Applications/t1.png')
        plt.close() 
        mym.gauge(11,-10,40, colors='RdBu', arrow=curSoilT, title='Soil Temperature', fname='/home/pi/Applications/t2.png')
        plt.close() 
        mym.gauge(12,90,110, colors='summer', arrow=curSoilm, title='Soil Moisture', fname='/home/pi/Applications/t3.png')
        plt.close() 
        mym.gauge(13,0,100, colors='coolwarm', arrow=curRH, title='Air RH', fname='/home/pi/Applications/t4.png')
        #t1.png – t4.png now reside in working directory. Use these in webpage along with  fig1.html 
 
        
        
        
    while time.time()<looptime: 
        time.sleep(0.01) 		#wait idly until next update time 
# end while repeats loop (program returns to while repeats >0: statement
#end program (if repeats <=0)
 
