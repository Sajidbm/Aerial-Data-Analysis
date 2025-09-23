# Aerial Data Analysis

The purpose of the repo is to generate hybrid datasets that can be used to simulate GPS spoofing. We have already attempted to do this once in the `ZurichUrbanMAVData` folder with 'Zurich Urban MAV Dataset'. You can find elaborate description of my findings on `readmefirst` there. 


## Goal

The goal is to see the effect on pose following the introduction of corrupted GPS data. Advanced spoofing techniques like spoof and drift is meant to give the autopilot false impressions of drift. The autopilot then makes corrections to remain on course. This results in false correction and instills false beliefs: autopilot thinks it's on course, in reality the drone drifts off course. We have the following steps ahead of us: 

- Create a dataset from Kalman filter (w/o air drag) fusing (true) GPS, Accelerometer, Gyro, Barometer, Magnetometer (IMU) together: call it `planned_course`
- Corrupt GPS Data to simulate spoofing in a dataset, call it `spoofed_gps`
- Fuse `spoofed_gps` and IMU together using the same Kalman filter, call it: `spoofed_course`
- Compare the (x,y) coordinates of `planned_course` and `spoofed_course`. 

## What is the current status of work?

Given the limitations of working with Zurich Urban MAV Dataset, I have moved on to using [Canadian Longterm Outdoor UAV Dataset (CLOUD)](https://www.dynsyslab.org/cloud-dataset/). 

- As of Tuesday/23 Afternoon, I have created an extended Kalman filter and fused the IMU and GPS from the CLOUD dataset. In the analysis [notebook](https://github.com/Sajidbm/Aerial-Data-Analysis/blob/main/CLOUDData/cloud_utias_winter_trial1_teach_analysis.ipynb) I have described the reason I had chosen the winter UTIAS trial 1 dataset. Before I go on to describe my learning from the implementation and possible consequences for future analysis, I want to briefly discuss the plan forward. 
    - To simulate spoof and drift attack on a UAV, we must create three scenarios. 
        - First, we need a planned flight course: `Pure (unfused) INS+ Pure (unspoofed) GPS`
            - In the deployment, this will be a pre-flight input to the UAV. The UAV's autopilot, guided by GPS (and other navigation systems), uses flight control to follow this path to target.
            - In testing stage, given a dataset, we must generate the planned flight course ourselves. This is because, in most cases, we are only given a dataset and are not provided the filtering algorithm used to fuse the onboard sensors. We accomplish this by creating our own filtering algorithm, and performing fusion of onboard sensor data ourselves. 
            - To create a robust flight path during testing, we must be given (1) raw (**bias**) acceleration + gyroscope + magnetometer data for the entire duration of the flight, (2) GPS position coordinates in GCS coordinate system, (3) GPS velocity estimates, (4) noise covariance estimates for the acceleration + gyroscope + magnetometer, (5) Horizontal dilution of precision (HDOP) and Vertical dilution of precision (VDOP) of GPS, and (6) noise covariance estimates for GPS velocity estimates. 
            - While the error estimates can be derived using inferential or statistical techniques, there's no alternative to (1), (2), (3), and (4). 

