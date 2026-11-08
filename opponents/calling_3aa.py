"""Conservative, rolling read of voluntary responses to bets.

Free checks and forced all-in/capped calls are not evidence of willingness to
call. A 64-response window allows a changing opponent to invalidate the read.
The Wilson bound is a policy confidence heuristic, not a stationary-opponent
guarantee.
"""
import math

WINDOW=64
MIN_RESPONSES=24


def add_response(window,event):
    _,street,context,action,price=event[:5]
    available=len(event)<6 or bool(event[5])
    # A fold remains voluntary when a raise is unavailable. Retain this
    # negative evidence; only the censored continuing action is uninformative.
    if not context or (not available and int(action)!=0):return window
    return (window+(min(int(action),2),))[-WINDOW:]


def confident_caller(window):
    n=len(window)
    if n<MIN_RESPONSES:return False
    rate=window.count(1)/n;z2=1.96**2
    lower=(rate+z2/(2*n)-1.96*math.sqrt(rate*(1-rate)/n+z2/(4*n*n)))/(1+z2/n)
    return lower>=.80
