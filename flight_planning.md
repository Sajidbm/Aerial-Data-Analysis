
In order to navigate a flight course autonomously, the UAV follows a sequence of waypoints, tracking the flight path from the origin to the target. ![](waypoint.jpeg)


- UAV course: The direction of the velocity vector. 
- Lookahead distance: 
- To fulfill the required lateral acceleration, the UAV rolls towards the direction of the flight path. The lateral acceleration is given by $$a_{lat} = 2\frac{\bf ||v||^2}{L_1} \sin(h)$$
where $\bf v$ is the velocity vector, $L_1$ is the tunable lookahead distance, $h$ is the angle between the heading (direction of the velocity vector) and the vector $\bf L_1$

- The roll angle is given by $$\phi = \tan^{-1}(\frac{a_{lat}}{g})$$

![](rotations.png)
