# Aerial Data Analysis

The purpose of the repo is to generate hybrid datasets that can be used to simulate GPS spoofing. We have already attempted to do this once in the `ZurichUrbanMAVData` folder with 'Zurich Urban MAV Dataset'. You can find elaborate description of my findings on `readmefirst` there. 


## Goal

The goal is to see the effect on pose following the introduction of corrupted GPS data. Advanced spoofing techniques like spoof and drift is meant to give the autopilot false impressions of drift. The autopilot then makes corrections to remain on course. This results in false correction and instills false beliefs: autopilot thinks it's on course, in reality the drone drifts off course. We have the following steps ahead of us: 

- Create a dataset from Kalman filter (w/o air drag) fusing (true) GPS, Accelerometer, Gyro, Barometer, Magnetometer (IMU) together: call it `planned_course`
- Corrupt GPS Data to simulate spoofing in a dataset, call it `spoofed_gps`
- Fuse `spoofed_gps` and IMU together using the same Kalman filter, call it: `spoofed_course'
- Compare the (x,y) coordinates of `planned_course` and `spoofed_course`. 

## What is the current status of work?

Given the limitations of working with Zurich Urban MAV Dataset, I have moved on to using [Canadian Longterm Outdoor UAV Dataset (CLOUD)](https://www.dynsyslab.org/cloud-dataset/). 

