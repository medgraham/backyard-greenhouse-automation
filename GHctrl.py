######################################################################
# program GHctrl.py for Python 3.x
#used to measure inputs and output data and control signals
#specifically written for M. Graham’s greenhouse & sensors
#April 2020
######################################################################


# libraries to include. Some may need to be installed using pip
import time     				#used for formatting & storing dates
import csv				#used for writing output text files
import piplates.DAQC2plate as daq2	# library for DAQC2 data acquisition
import math				# math functions
import pymysql as msql			# MySQL library
import Adafruit_DHT			#DHT22 sensor library

#functions required to convert between RH and dewpoint

def T2esat(t): #t in C	      		#convert dew point to saturation vapour pressure in mb
    a=17.62*t/(243.12+t)
    e=6.112*math.exp(a) 
    return e
    
def esat2T(e): 				#convert vapour pressure in mb to dew point (in C)
    a=math.log(e/6.112)
    t=a*243.12/(17.62-a)
    return t # t in C

def Tdew(rh,t):				# calculate Tdew from given Tair and RH
    es=T2esat(t)
    ea=rh/100*es
    td=esat2T(ea)
    return td



#set up database connection to existing server

def dbcon():   
    connection = msql.connect(host=’192.168.0.2’,  #IP address of database server - edit as appropriate
                             user='user',
                             password='password',  #user and password are ones entered during database configuration
                             db='greenhouse',
                             charset='utf8mb4',
                             cursorclass=msql.cursors.DictCursor)
    return connection

#create the database
#remove comment status of this section and run as a separate program  to create a database if one does not already exist. Database structure created in “sql”  variable should be compatible with the DB write statements later in the  program
###################################################
  #with connection.cursor() as cursor:
        # Create a new table
  #     sql ="CREATE TABLE IF NOT EXISTS `data` (`id` DATETIME NOT NULL UNIQUE,`temp` double NOT NULL,`soilm` double NOT NULL,PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin AUTO_INCREMENT=1 ;"
  #      cursor.execute(sql)
###################################################

        
# set constants
RHsensor = Adafruit_DHT.DHT22  #sensor type required for library
RHpin = 15			   #connected to GPIO 15
vnton=27			   # Ventilation turn on temperature
vntoff=24			   # Ventilation turn off temperature
R1=5.00 			   #pull up resistor for thermistor on chan 7 (K-Ohm)
R2=5.00			   # pull up resistor thermistor on chan 5 (k-Ohm)
Ltsf=10 				   #scale factor for light sensor to read 100% in full sun
SMdry=2.750  			   # 0% moisture condition for soil moisture sensor 
SMwet=1.4920  		   #100% condition for soil moisture sensor 
SMslope=(SMdry-SMwet)/100      # multiplier for soil moisture
SMset=65 			  #default irrigation setpoint
SMoff=SMset+5 		#default irrigation hysteresis of 5
count=sT1=sSM1=x=sT2=sRH=sT3=sIRR=RHcount=Svnt=SLt=vnt=0;  #initialize for averaging
IRRenable=True  		#start with reservoir not empty (i.e. can irrigate)
irr=0				#start with irrigation off


# data acquisition section
#######################################################

def volts():  			# function to read analog inputs
    return [daq2.getADC(0,i) for i in range (0,9)]  # reads all channels

mlimit=1440*2/5    # set a maximum number of readings – useful in debugging
measurements=0   # initialize measurement counter

# start global measurement loop

while (measurements < mlimit):  # measurements is not normally  updated, so while is infinite 
    count=sT1=sSM1=0;  #initialize for averaging
    ftime=time.time()+300   #averaging period set to 5 minutes (i.e. 300 s)
    ##begin 5 minute averaging loop 
    while (time.time()<ftime):   # if 5 minutes are not up 
        stime=time.time()+10;   #take readings every 10 s
        daq2.setLED(0,'off')	  #change color of LED while reading (allows visual monitoring of operation)
        daq2.setLED(0,'green') 
        time.sleep(0.1)         #pause so light can be seen
        rawd=volts()              #rawd is a list channels 0..8 - chan 8 is 3.3 supply volts
        Rt=rawd[7]/(rawd[8]-rawd[7])*R1  #calculate soil T resistance
        T1=222.973+2.26e-4*Rt*1000-23.376*math.log(Rt*1000) #calculate soil T 
        Rt=rawd[5]/(rawd[8]-rawd[5])*R2   #calculate airT resistance
        T2=222.973+2.26e-4*Rt*1000-23.376*math.log(Rt*1000)   #calculate air T 
        Lt=rawd[4]
        Lt=Lt*Lt*Ltsf     #calc light as power relative to full sun (arbitary units)
        SLt=SLt+Lt		#update sum of light levels for measurement period
        SM1=(rawd[6]-SMwet)/SMslope  #calculate soil moisture
        SM1=100-SM1       #update sum of soil moisture for measurement period
        RH, T3 = Adafruit_DHT.read_retry(RHsensor, RHpin)  #update sum of light levels for measurement period
        if ((RH<100) and (RH >0)):            #check for RH errors (between max and min)
            RH=Tdew(RH,T3)		#if ok calculate dew point
            sRH=sRH+RH                  #update sum of dew points for measurement period
            RHcount=RHcount+1   #update count of valid RH measurements
				#end if
        Flt1=daq2.getDINbit(0,7) #read irrigation float switches
        Flt2=daq2.getDINbit(0,6)
        irtime=time.localtime()  #read time 
        if  Flt2 !=0:			#if irrigation empty
            IRRenable=False		#disable irrigation 
            daq2.clrDOUTbit(0,7)       #turn off pump
        else:
            IRRenable=True		#enable irrigation 
				#end if
        if ((SM1<SMset) and IRRenable):   # if soil dry and tank not empty
            irr=1			#note that irrigation is on
            daq2.setDOUTbit(0,7)	#turn on pump relay
            sIRR=sIRR+10 		#record another 10 secs of irrigation
        elif ((SM1<SMoff) and IRRenable): #in hysterisis band – continue irrigation if already started
            #keep everything the way it was (this section is a placeholder- here in case other actions needed in future)
            irr=irr
        else:
            irr=0
            daq2.clrDOUTbit(0,7)  #turn off irrigation
        if ((irtime.tm_hour==7) and (irtime.tm_min<33 and irtime.tm_min>30) and IRRenable):
	#irrigate for 2 minutes every morning starting at 07:31
           irr=1           
           sIRR=sIRR+10 #another 10 secs of irrigation 

        Tv=(T2+T3)/2 #calcuate average air temperature from 2 sensors
        if (Tv>vnton):  #if venting is required
            daq2.setDOUTbit(0,6) #turn fan on
            vnt=vnt+10;  #another 10 sec of vent operation
        if (Tv>vntoff):  #if greenhouse has cooled
            daq2.clrDOUTbit(0,6)  #turn off fan 
#print raw data to terminal output for monitoring        print("%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%i,%i,%i,%i,%.2f,%i" %(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),T1,SM1,T2,RH,T3,rawd[8],Flt1,Flt2,irr,SMset,Lt,vnt),flush=True)
   #update sums for averaging
        count=count+1 # increment measurement count (except for RH)
        sT1=sT1+T1
        sSM1=sSM1+SM1
        sT2=sT2+T2
        sT3=sT3+T3
        daq2.setLED(0,'off') # Measurements completed. Change LED color to “idle” status
        daq2.setLED(0,'blue') 
        while (time.time()<stime): # wait until measurement period up
            x=x  #do nothing line
    #averaging period up – calculate means
    sT1=sT1/count
    sSM1=sSM1/count
    sT2=sT2/count
    sRH=sRH/RHcount
    sT3=sT3/count
    sRH=T2esat(sRH)/T2esat(sT3)*100 #calculate  average RH from average dew point air temperatures 
    SLt=SLt/count
   
    tstmp=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    # unlimited measurements. set to =measurements+1 to auto stop at mlimit
    measurements=1 

    #write data to file
    print(count) #note number of measurements on terminal for monitoring
    #update an excel CSV file of data (backup on Pi)
    with open('ghdata.csv','a+',newline='') as f:
        fw=csv.writer(f,dialect='excel',)
        T1,SM1,T2,RH,T3,rawd[8],Flt1,Flt2,irr,SMset,Lt,vnt
        fw.writerow([tstmp]+[sT1]+[sSM1]+[sT2]+[sRH]+[sT3]+[SLt])
    outstr='"%s",%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%i,%i,%i,%i,%.2f,%.2f,%.2f,%i' %(tstmp,sT1,sSM1,sT2,sRH,sT3,sIRR,Flt1,Flt2,count,RHcount,SMset,rawd[8],SLt,vnt)
    print()
    print()
    print(outstr,flush=True) #print data on terminal for monitoring
    print()
   #print warning messages on terminal as required
    if ((Flt1==1) and (Flt2==0)):
        print('Warning: Irrigation reservoir is getting low')
        print()
    if Flt2==1:
        print("WARNING:   Irrigation reservoir empty. Cannot irrigate!!!!!")
        print()
    print()    #tstmp,sT1,sSM1,sT2,sRH,sT3,sIRR,Flt1,Flt2,count,SMset,rawd[8]             
   #write data to database
    sql2='INSERT INTO data (id,SoilT,Soilm,AirT1,RH,AirT2,IRRtime,TankLow,TankMT,count,RHcount,IRRset,Vss,Lt,vnt) VALUES ('+ outstr +')' #SQL command to submit
    try: #prevent crash in cobbection is down
        connection=dbcon()
        with connection.cursor() as cursor:
            cursor.execute(sql2)
            connection.commit()
            connection.close()
    # data now in  db if no exceptions
    except:  #if exception encountered
        #print error on terminal
        print ('db Connection or SQL execution error',flush=True)    
 
   #initialize for next averaging period
    count=sT1=sSM1=x=sT2=sRH=sIRR=RHcount=vnt=SLt=0; 
 
  #measurement while loop ends
  #change LED color to indicate mlimit reached an program has terminated (normaly does not happen)
daq2.setLED(0,'off')
daq2.setLED(0,'yellow')
