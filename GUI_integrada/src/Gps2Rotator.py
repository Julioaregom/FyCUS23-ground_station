'''
# Author/s: Julio Arévalo Gómez
# Email: julioaregom02@gmail.com
# Project: FyCUS23 / 2023 Edition
# License: GNU General Public License, version 3 (GPL-3.0)
'''

import numpy as np

def Gps2Rotator(_lat:float, _lon:float,_h:float,_ref_lat:float,_ref_lon:float,_ref_h:float):
    '''This function transforms GPS coordinates: elipsoidal height(h) metres, latitude (lat), longitude (lon) to 
    rotator input coordinates: Azimuth (az) Elevation (el) and distance between reference point and GPS coordinates (p)'''

    lon=_lon
    h=_h
    lat=_lat
    # Reference point, where the antenna is settled
    phi0=_ref_lat
    lambda0=_ref_lon
    h0=_ref_h

    # phi0 = 37.3868 #latitude
    # lambda0 = -5.9855 #longitude
    # h0 = 7

    x0, y0, z0 = geo2cart(h0, phi0, lambda0)
    x, y, z = geo2cart(h, lat, lon)

    # Transform into radians
    phi0 = phi0*np.pi/180 
    lambda0 = lambda0*np.pi/180
    # ECEF2NED matrix
    R = np.array([[-np.sin(phi0)*np.cos(lambda0), -np.sin(phi0)*np.sin(lambda0), np.cos(phi0)],
                  [-np.sin(lambda0), np.cos(lambda0), 0],
                  [-np.cos(phi0)*np.cos(lambda0), -np.cos(phi0)*np.sin(lambda0), -np.sin(phi0)]])

    # Coordinate transform formula ECEF2NED
    P = R @(np.array([x, y, z]) - np.array([x0, y0, z0]))

    #----------------------------------------------------------------------------------------------------------------------------------
    # Coordinate transform NED2ENU (for better transformation to AER)
    xE=P[1]
    yN=P[0]
    zU=-P[2]

    #print(str(xE) +','+ str(yN) +','+ str(zU) )

    #Coordinate transform ENU2AER (xEast,yNorth,zUp -> Azimuth, Elevation, Range)
    hip=np.sqrt(xE**2+yN**2)
    az=np.arctan2(xE,yN) % (2*np.pi) * 180/np.pi
    el=np.arctan2(zU,hip) *  180/np.pi
    range=np.sqrt(zU**2+hip**2)

    return az, el, range


def geo2cart(h, phi, lam):
    #This function transforms geodesian to cartesian earth-centered coordinates
    #Geodesian coordinates must be given in radians and cart. coord. shown in metres.
    #Definition of ellipsoidal Earth model WGS-84 (used for GPS)
    f=1/298.257224
    re=6378.137*1e3  # In meters
   
    phi=phi*np.pi/180
    lam=lam*np.pi/180

    x=(h+re/(np.sqrt(1-f*(2-f)*(np.sin(phi))**2)))*np.cos(phi)*np.cos(lam)
    y=(h+re/np.sqrt(1-f*(2-f)*(np.sin(phi))**2))*np.cos(phi)*np.sin(lam)
    z=(h+(re*(1-f)**2)/np.sqrt(1-f*(2-f)*(np.sin(phi))**2))*np.sin(phi)    
    return x, y, z