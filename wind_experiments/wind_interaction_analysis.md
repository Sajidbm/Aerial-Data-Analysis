# Wind Interaction Analysis for ArduPlane

## 1. Vector Kinematics: The Wind Triangle

To understand how the UAV reacts to wind, we must first define the fundamental vector relationship governing its motion.

Let:
*   $\vec{V}_a$ = **Airspeed Vector** (Velocity of UAV relative to the air mass)
*   $\vec{V}_w$ = **Wind Vector** (Velocity of the air mass relative to the ground)
*   $\vec{V}_g$ = **Ground Speed Vector** (Velocity of UAV relative to the ground)

The relationship is:
$$ \vec{V}_g = \vec{V}_a + \vec{V}_w $$

### Scenario Setup
*   **Target Course**: North ($0^\circ$)
*   **UAV Airspeed Magnitude**: $|\vec{V}_a| = S_{air}$
*   **Wind**: From West to East (Eastward wind). $\vec{V}_w = [W_E, 0]$ where $W_E > 0$. *Note: Wind is conventionally defined by where it comes FROM, but physically it pushes TO. An "Eastward" wind usually means blowing TOWARDS East (Westerly wind), but your prompt says "moving towards East". We will assume the wind vector points East.*

If the UAV points its nose directly North ($\psi = 0^\circ$), its airspeed vector is $[0, S_{air}]$.
The resulting ground velocity would be:
$$ \vec{V}_g = [W_E, S_{air}] $$
This results in a drift angle $\alpha$ off the desired North track:
$$ \alpha = \arctan\left(\frac{W_E}{S_{air}}\right) $$
The UAV would drift East of the desired path.

---

## 2. Sideslip Angle (β): The Aerodynamic Response

When a lateral wind hits the aircraft, it creates a **sideslip angle** β, defined as the angle between the aircraft's longitudinal axis (where the nose points) and its velocity vector relative to the air.

### Definition
$$ \beta = \arctan\left(\frac{V_{lateral}}{V_{forward}}\right) $$

Where:
*   $V_{lateral}$ = Lateral component of airspeed (perpendicular to fuselage)
*   $V_{forward}$ = Forward component of airspeed (along fuselage)

### Physical Meaning
*   **β = 0**: Air flows directly along the fuselage (coordinated flight)
*   **β ≠ 0**: Air hits the fuselage from the side, creating aerodynamic side forces

### Weathervaning Effect
The vertical stabilizer generates a restoring yaw moment proportional to β:
$$ N_{\beta} = C_{n_\beta} \cdot \beta $$

This moment tries to align the nose with the relative wind, reducing β. However:
*   **Passive aerodynamics alone** cannot eliminate β completely in a crosswind
*   **Active control** (rudder/autopilot) is needed to fully zero β or maintain a specific heading

---

## 3. Course Hold vs. Heading Hold

### Course Hold (Crabbing - Standard Navigation)
To maintain a true North **ground track**, the autopilot must **Crab**.

**Crabbing** involves rotating the vehicle's heading (yaw) into the wind so that the lateral component of airspeed exactly cancels the lateral component of the wind.

ArduPlane's navigation controller (typically the L1 controller) computes the required **Lateral Acceleration** to return to the path. In a steady-state crosswind, this settles into a crab angle.

#### Mathematical Condition for Zero Cross-Track Error
We need the East component of $\vec{V}_g$ to be zero:
$$ V_{g_E} = V_{a_E} + V_{w_E} = 0 $$
$$ S_{air} \sin(\psi) + W_E = 0 $$
$$ \sin(\psi) = -\frac{W_E}{S_{air}} $$
$$ \psi_{crab} = \arcsin\left(-\frac{W_E}{S_{air}}\right) $$

For an Eastward wind ($W_E > 0$), $\psi_{crab}$ is negative (West). The UAV points slightly West to fly North.

The resulting Ground Speed magnitude will be reduced:
$$ |\vec{V}_g| = S_{air} \cos(\psi_{crab}) = \sqrt{S_{air}^2 - W_E^2} $$

### Heading Hold (No Crabbing/Drift Mode)
When the flight controller is told to **maintain heading** (e.g., North = $0°$):
*   The controller does **not** regulate lateral position or ground velocity direction
*   A lateral wind adds a sideways component to the ground velocity
*   This produces a sideslip $\beta$ in the air-relative frame
*   **Aerodynamics (weathervaning)** tries to reduce β, but cannot eliminate it completely without control action
*   The **autopilot corrects** by commanding the nose back to North
*   Once yaw rate is zero and heading is correct, the controller is "satisfied"
*   **Ground track is displaced downwind** - this is **drift equilibrium**

#### Drift Equilibrium
In this state:
*   The aircraft flies **straight relative to the air mass** (constant heading in air)
*   The aircraft **slides over the ground** (diagonal ground track)
*   Heading = North ($0°$), but Ground Course $\neq$ North

### Crabbing vs. Sideslipping vs. Drifting
It is crucial to distinguish between these three flight conditions:

1.  **Crabbing (Course Hold/Standard Navigation):** 
    *   Wings are level (Roll $\phi = 0$)
    *   Nose points into the wind at angle $\psi_{crab}$
    *   Sideslip β ≈ 0 (coordinated flight)
    *   Ground track follows desired path
    *   **ArduPlane AUTO/GUIDED modes do this**

2.  **Drifting (Heading Hold/No Lateral Correction):**
    *   Wings are level (Roll $\phi = 0$)
    *   Nose points at commanded heading (e.g., North)
    *   Small sideslip β exists (weathervaning tries to reduce it)
    *   Ground track drifts downwind
    *   **Our drift experiment demonstrates this**

3.  **Sideslipping (Cross-Control/Specialized Maneuver):** 
    *   Aircraft is banked into the wind
    *   Nose points at desired ground track (not into wind)
    *   Large intentional sideslip β
    *   Used for steep descents or crosswind landings
    *   **Force Balance**:
        *   Horizontal lift component ($L \sin \phi$) opposes wind drift
        *   Requires opposite rudder (cross-control)
        *   Creates high drag
    *   **Rarely used in cruise flight**

---

## 4. Control Loop Dynamics: The "Bank-to-Crab" Sequence (Course Hold Mode)

You asked an excellent question: *Why does it bank if crabbing just means pointing the nose?*

**Key Concept: To Change Heading, a Plane Must Bank.**
Unlike a car or a boat, a fixed-wing aircraft cannot simply "yaw" to a new heading efficiently. Using the rudder alone to yaw causes a sideslip (inefficient and uncomfortable). To change its heading to point into the wind, the aircraft must perform a **Coordinated Turn**.

Here is the step-by-step sequence of events for a 10-second gust:

### Phase 1: The Gust Hits ($t=0$)
*   **Displacement:** The wind pushes the aircraft **East**. The Ground Track immediately drifts East.
*   **Weathervaning (Passive Aerodynamics):** The vertical tail acts like a weather vane. The relative wind hitting the side of the tail naturally pushes the nose **West** (into the wind).
    *   *Note:* This is purely aerodynamic. The plane wants to align with the airflow to zero out sideslip. This happens instantly and *helps* the autopilot by starting the turn into the wind.

### Phase 2: The Correction (ArduPlane L1 Controller) ($t + \delta t$)
*   **Detection:** The L1 controller sees the Cross-Track Error (XTrack) growing. It calculates that it needs to fly a heading of, say, $350^\circ$ (North-West) to get back on the North line.
*   **The Turn Command:** To get to heading $350^\circ$, the controller demands a **Bank Left**.
*   **The Tun:** The aircraft rolls Left. The horizontal lift component pulls the nose around to the Left.
*   **Result:** The Heading changes from $360^\circ$ to $350^\circ$.

### Phase 3: Establishing the Crab ($t + \Delta t$)
*   **Leveling Off:** Once the nose is pointing at $350^\circ$ (the correct Crab Angle), the controller **removes the bank**. The wings go back to **Level**.
*   **The Crab State:** The aircraft is now **Crabbing**.
    *   **Definition:** Crabbing is the *flight condition* where the nose points into the wind to maintain a desired ground track.
    *   **Active vs. Passive:** While weathervaning *starts* the rotation, **Crabbing is the deliberate control strategy** of holding a specific heading to keep the Ground Course aligned with the Target Path.

### Phase 4: The "10-Second Gust" Problem
If the wind disappears after 10 seconds:
1.  **Wind Stops:** The aircraft is still pointing $350^\circ$ (West), but now there is no wind to push it back.
2.  **Overshoot:** The aircraft instantly starts flying West, crossing the North track and going too far left.
3.  **New Correction:** The controller sees it is now left of track. It demands a **Bank Right** (East).
4.  **Oscillation:** The plane turns Right to correct.

**Conclusion:** For a 10s gust, you will see a constant cycle of **Bank -> Turn -> Level -> Wait -> Bank -> Turn**. The aircraft is *trying* to Crab, but the wind changes before it can settle into a steady state.

### EKF (Extended Kalman Filter) Role
The EKF estimates wind velocity explicitly ($Wind\_Vel$).
$$ \dot{\hat{V}}_w = K (V_{gps} - V_{imupulled}) $$
When the gust hits, the EKF sees a discrepancy between the IMU (which measures acceleration, but doesn't instantly see wind) and GPS (which sees the drift). The EKF updates the `WIND` estimate.
This `WIND` estimate allows the navigation controller to "feed forward" a correction, effectively predicting the crab angle needed, rather than just reacting to error.

## 5. Summary of Phenomena

1.  **Weathervaning**:
    *   The vertical tail ensures the aircraft naturally wants to point into the relative wind (Sideslip $\beta \to 0$).
    *   When an Eastward gust hits, the relative wind comes from the **West**.
    *   The tail pushes the nose **West** (into the wind) automatically. This is a *stabilizing* passive aerodynamic effect that helps the autopilot.

2.  **Inertial Drift**:
    *   The physical displacement of the center of mass due to the side force of the wind.

3.  **Ground Track Deviation**:
    *   The difference between where the nose points (Heading) and where the GPS says it's going (Course).

## Conclusion
Under a heavy, periodic Eastward wind:
*   The UAV will **Crab** (yaw West) to fight the wind.
*   Because the wind is periodic/gusty, the heading will **oscillate**.
*   The position will likely trace a **Sinusoidal** path around the North line, as the controller lags slightly behind the wind changes.
*   **Phenomena involved:** Vector addition (Kinematics), L1 Guidance (Feedback Loop), Aerodynamic Weathervaning (Passive Stability), and EKF Wind Estimation (State Estimation).
