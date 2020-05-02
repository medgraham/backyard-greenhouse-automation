# -*- coding: utf-8 -*-
"""
function "guage" dreates a speedometer type guage as a fig file 
    -maps eng units to 180, degree meter
    -displays value in title
    -uses matplotlib color maps to enhance scaling
    -requires imports:
                 from matplotlib import cm
                 from matplotlib import pyplot as plt
                 from matplotlib import patches as pth
                 import numpy as np

 gauge(fign                   ==>figure handle
                                   fig should be initalized at start of caller
                                   fig should be closed before calling
                                   fig number to (re) create is passed
          min,               ==> meter range minimum (eng units)
          max,               ==> meter range maximum (eng units)
          colors='jet_r',    ==> matplotlib colormap
          arrow=1,           ==> pointer value (eng units)
          title='',          ==> meter title without current value
          fname=False        ==> filename to save as
          ): 
"""
#import os, sys
#import matplotlib
from matplotlib import cm
from matplotlib import pyplot as plt
from matplotlib import patches as pth
import numpy as np
#matplotlib inline
def degree_range(n): 
    start = np.linspace(0,180,n+1, endpoint=True)[0:-1]
    end = np.linspace(0,180,n+1, endpoint=True)[1::]
    mid_points = start #+ ((end-start)/2.)
    return np.c_[start, end], mid_points

def rot_text(ang): 
    rotation = np.degrees(np.radians(ang) * np.pi / np.pi - np.radians(90))
    return rotation

def gauge(fign,gmin,gmax , \
          colors='jet_r', arrow=1, title='', fname=False): 
    
    #set  label tickmark frequency
    N=10
    """
    check to see if range is exceeded. if it is, re-scale
    """
    #determine initial step size
    step=int((gmax-gmin)/10)
   
    if (arrow>gmax):
        gmax=int(arrow+step) #make max one step greater than arrow
    if (arrow<gmin):
        gmin=int(arrow-step)#reduce min if undershot
        #recalculate new step
    step=int((gmax-gmin)/10)    
    labels = list(str(gmin+i*step) for i in range (N+1))
   
 
    
    """
    if colors is a string, we assume it's a matplotlib colormap
    and we discretize in N discrete colors 
    """
    
    if isinstance(colors, str):
        cmap = cm.get_cmap(colors, N)
        cmap = cmap(np.arange(N))
        colors = cmap[::-1,:].tolist()
    if isinstance(colors, list): 
        if len(colors) == N:
            colors = colors[::-1]
        else: 
            raise Exception("\n\nnumber of colors {} not equal \
            to number of categories{}\n".format(len(colors), N))

    """
    begins the plotting
    """
    #set title to include current value
    title=title +'=%.2f' %(arrow)
    fig, ax = plt.subplots(num=fign)

    ang_range, mid_points = degree_range(N)

    labels = labels[::-1]
    
    """
    plots the sectors and the arcs
    """
    patches = []
    for ang, c in zip(ang_range, colors): 
        # sectors
        patches.append (pth.Wedge((0.,0.), .4, *ang, facecolor='w', lw=2))
        # arcs
        patches.append(pth.Wedge((0.,0.), .4, *ang, width=0.10, facecolor=c, lw=2, alpha=0.5))
    
    [ax.add_patch(p) for p in patches]

    
    """
    set the labels (e.g. 'LOW','MEDIUM',...)
    """

    for mid, lab in zip(mid_points, labels): 

        ax.text(0.35 * np.cos(np.radians(mid)), 0.35 * np.sin(np.radians(mid)), lab, \
            horizontalalignment='center', verticalalignment='center', fontsize=14, \
            fontweight='bold', rotation = rot_text(mid))

    """
    set the bottom banner and the title
    """
    r = pth.Rectangle((-0.4,-0.1),0.8,0.1, facecolor='w', lw=2)
    ax.add_patch(r)
    
    ax.text(0, -0.05, title, horizontalalignment='center', \
         verticalalignment='center', fontsize=22, fontweight='bold')

    """
    plots the arrow now
    """
    
    pos = 180-(arrow-gmin)/(gmax-gmin)*180
    #mid_points[abs(arrow - N)]
    
    ax.arrow(0, 0, 0.225 * np.cos(np.radians(pos)), 0.225 * np.sin(np.radians(pos)), \
                 width=0.02, head_width=0.04, head_length=0.1, fc='k', ec='k')
    
    ax.add_patch(pth.Circle((0, 0), radius=0.02, facecolor='k'))
    ax.add_patch(pth.Circle((0, 0), radius=0.01, facecolor='w', zorder=11))

    """
    removes frame and ticks, and makes axis equal and tight
    """
    
    ax.set_frame_on(False)
    ax.axes.set_xticks([])
    ax.axes.set_yticks([])
    ax.axis('equal')
    plt.tight_layout()
    if fname:
        fig.savefig(fname, dpi=200)
    #plt.draw()

