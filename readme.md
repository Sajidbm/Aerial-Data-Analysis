# Aerial Data Analysis 

The purpose of this repository is to independently analyze the Zurich MAV Dataset found here: https://rpg.ifi.uzh.ch/docs/IJRR17_Majdik.pdf. The data is collected from an MAV flight conducted by a team at University of Zurich. The whole flights lasts for about 45 minutes. 

### Goal:

The initial goal was to create a virtual simulation environment where I can demonstrate different GPS spoofing scenarios and illustrate spoofing detection solutions, but I have been struggling to get reliable pose estimates to begin with. I discuss the possible flaws and ways to recover. 

### What's here?

The most important file is `FilteringDroneData.ipynb` where I have done most of the Extended Kalman Filter (EKF) implementation. As of Sept 16/Tues, the EKF estimates are faulty and I have a few guesses as to why:

- I have purposefully chosen a simplified state covariance matrix `self.P` and a process noise matrix
`self.Q`. This may be effecting the estimates produced by the filter. 
- Next, the dataset does not come with a magnetometer file. As a result, I estimate attitude solely based on gyroscope (and accelerometer) outputs. This causes error accumulation because magnetometer gives the UAV accurate heading information relative to the earth's magnetic field. Without magnetometer, there's no absolute reference for the yaw angle, and without an absolute reference on the yaw angle, attitude estimation suffers drift error. Details can be found here: https://www.anyleaf.org/blog/estimating-drone-attitude
- I make a very simplified assumption about the error covariance propagation: `self.P += self.Q * dt`. Ideally, the error propagation is done using $$P_{k|k-1} = F_k P_{k-1|k-1} F_k^T + Q_k$$ where $Q_k$ is the process covariance and $F$ is the state transition matrix. Details can be found here: https://engineeringmedia.com/controlblog/the-kalman-filter

The file `bias_and_covariances` computes the bias and measurement noise covariance matrices directly from the dataset. `FilterDroneData` and `visual_analysis` shows some simple analysis and cleaning on the data.  

### What's next?

There are some nice resources online that can help us fully synthesize aerial data. This offers us significantly higher control over the process noises and covariances. The downside is that we will be synthesizing data purely from a dynamic, deterministic model. However, given the difficulty of extracting valuable information from `pure' datasets, I think it is worth exploring that direction. 

- https://mariogc.com/post/simple-imu-simulator/
- https://ahrs.readthedocs.io/en/latest/filters/ekf.html
- https://www.roboticsbook.org/S73_drone_sensing.html
- https://docs.duckietown.com/ente/course-intro-to-drones/ukf/project/two-dimensional-ukf.html

