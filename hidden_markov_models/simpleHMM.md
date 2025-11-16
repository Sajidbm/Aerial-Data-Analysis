# Simple spoofing model and HMM-based inference framework


First I describe an 1D spoofing model for an autonomous UAV:

- The UAV must maintain GPS velocity, $\text{GPS}_t = 1 ~m/s$ to reach target destination.
    - Like before, the UAV’s belief system is guided by GPS velocity alone. To navigate the route (or ensure that it is maintaining 1 m/s) the UAV takes sensor measurements from GPS velocity estimate at every time step.
    - The UAV also knows (and controls) its own body velocity $U_t$ (resulting from thrust).
- The route also contains randomly distributed wind, described by $W_t \in \{-1,0,1 \}$.
    - Naively, we assume that $P(W_t = -1) = P(W_t = 1) = P(W_t = 0) = \frac{1}{3}$.
    - Moreover, the transition model of wind is given by: $P(W_t~|~W_{t-1}) = \frac{1}{3}$. This means, knowing the wind velocity at time step $t-1$ reveals no new information about time step $t$.
        - This is rather unrealistic because wind distribution follows a gradient. More realistically, we could describe $W_{t} = \rho W_{t-1}$  where $0<\rho <1$.  But doing so will obstruct the static/discrete assumption of our model.
- Number of available/visible GPS satellites, $Q \in \{0,1,2,3,4\}$  is another observable variable that can indicate spoofing because DOS (denial of service) through GPS jamming is common in all spoofing scenarios.
    - Suppose, we have the following probability distribution
    
$$P(Q=i~|~ G_t = 1) = \begin{cases}
    \frac{1}{5} &\text{when } i = 0,2\\
\frac{3}{5} &\text{when } i = 1\\
0 &\text{otherwise}
\end{cases}$$
    
$$P(Q=i~|~ G_t = 0) = \begin{cases}
    \frac{3}{5} &\text{when } i = 4\\
\frac{1}{5} &\text{when } i = 3\\
\frac{1}{5} &\text{when } i = 2\\
0 &\text{otherwise}
\end{cases}$$
    
- Wind has no influence on the number of visible satellites. Meaning: $P(Q~|~G,W) = P(Q~|~G)$ and $P(Q~|~W) = P(Q)$
- At the given time step $t$, $\text{GPS}_t = U_t + W_t + \Delta_t$  where $\Delta_t \in \{-2,-1,0,1,2\}$ is the spoofing bias.
    - In absence of spoofing, $G_t = 0,$ the UAV maintains $\text{GPS}_t = 1~m/s$ by setting $U_t = 1 - W_t.$
    - In presence of spoofing, $G_t = 1,$ the UAV maintains $\text{GPS}_t = 1$ by setting $U_t = 1-W_t-\Delta_t.$
        - More realistically, the spoofing bias $\Delta_t \in \mathbb{R}$.
        - $\text{GPS}_t$  incorporates measurement noise $\epsilon_t$.
    - The true ground velocity is given by $V_t = U_t + W_t$.
    - The UAV doesn’t have any wind sensors on board.
- The task of the spoofer is to fully stop the UAV.
    - Spoofer can fully control the GPS velocity estimate $\text{GPS}_t$ that the UAV sees and maintains at 1 m/s.
    - So to stop the UAV, the spoofer will (falsely) show that $\text{GPS}_t>1.$
    - As a result of this, UAV will slow down by the corresponding amount until GPS velocity is back to 1, whereas in reality UAV was moving at normal speed $V_t = 1~m/s$.
- The central detection idea revolves around the observable variable $r_t = \text{GPS}_t- U_t$ or the residual. Using the formula for $\text{GPS}_t$ above, we can rewrite the residual: $r_t = W_t+ \Delta_t.$
    - When there is no spoofing, $P(r_t) = P(W_t)$ that is, the residual must follow the distribution of wind.
    - When there *is* spoofing, $P(r_t) \neq P(W_t)$.
- Another layer of detection can be derived from the UAV’s control constraints:
    - Body velocity cannot exceed a threshold: $|U_t|< U_{max.}$
    - We frame this as an observable variable:
        
$$s_t = \begin{cases}0 &\text{if}~  |U_t|< U_{max.}\\
1 &\text{otherwise} 
\end{cases}$$
        

## HMM assumptions:

- Our first assumption that the latent state variables satisfy the first order Markov property.
- Next, conditional independence.


## Latent and Observation Variables

- The latent random variables are $G, ~ W$ which refer to spoofing variable and wind variable respectively.
- The observable random variables are $\text{GPS}_t$,  which is the GPS velocity estimate and body velocity $U_t$. We transform these variables to fit the detection framework: $r_t,$ the residual and $s_t$ the saturation variable.

## Observation/Sensor/Emission model

The observation model is given by $P(r_t, s_t~|~ G, W)$.  Now, we must first consider distributions of saturation and residual separately before we can combine them. 

- We assume that $r_t$ and $s_t$ are conditionally independent given $(G, W)$. This follows from the fact that once we know $(G, W)$, knowing $s_t$ does not help predict $r_t$. Similarly, knowing $R_t$ does not help predict $s_t.$
- As a result:

$$P(r_t, s_t~|~ G, W) = P(r_t~|~ G, W)~P(s_t~|~ G, W)$$

- Next, we define the probability mass function of each independent component: $P(r_t~|~G,W) = P(W_t+\Delta_t~|~G, W)$
    
$$P(W_t+\Delta_t = 0~|~ G=i, ~W=j) = \begin{cases}
1 &\text{if } i,j = 0,0\\
0 &\text{if } i,j = 1,0\\
\frac{1}{4} &\text{if } i,j = 1,-1\\
\frac{1}{4} &\text{if } i,j = 1,1\\
\end{cases}$$

$$P(W_t+\Delta_t = 1~|~ G=i, ~W=j) = \begin{cases}
1 &\text{if } i,j = 0,1\\
\frac{1}{4} &\text{if } i,j = 1,0\\
\frac{1}{4} &\text{if } i,j = 1,-1\\
\end{cases}$$

$$P(W_t+\Delta_t = -1~|~ G=i, ~W=j) = \begin{cases}
1 &\text{if } i,j = 0,-1\\
\frac{1}{4} &\text{if } i,j = 1,0\\
0 &\text{if } i,j = 1,-1\\
\frac{1}{4} &\text{if } i,j = 1,1\\
0 &\text{otherwise}
\end{cases}$$

$$P(W_t+\Delta_t = -2~|~ G=i, ~W=j) = \begin{cases}
\frac{1}{4} &\text{if } i,j = 1,0\\
\frac{1}{4} &\text{if } i,j = 1,-1\\
0 &\text{otherwise}
\end{cases}$$

$$P(W_t+\Delta_t = 2~|~ G=i, ~W=j) = \begin{cases}
\frac{1}{4} &\text{if } i,j = 1,0\\
\frac{1}{4} &\text{if } i,j = 1,1\\
0 &\text{otherwise}
\end{cases}$$

$$P(W_t+\Delta_t = -3~|~ G=i, ~W=j) = \begin{cases}
\frac{1}{4} &\text{if } i,j = 1,-1\\
0 &\text{otherwise}
\end{cases}$$

$$P(W_t+\Delta_t = 3~|~ G=i, ~W=j) = \begin{cases}
\frac{1}{4} &\text{if } i,j = 1,1\\
0 &\text{otherwise}
\end{cases}$$
    
- Next, $P(s_t~|~G,W)$ . Suppose that $U_{max} =2$. Note that $s_t =0$, when $|U_t| < U_{max}.$
    
$$P(s_t=0~|~G_t = i,~W_t=j) = \begin{cases}
0 &\text{if } i,j = 0,-1\\
1 &\text{if } i,j = 0,0\\
1 &\text{if } i,j = 0,1\\
\frac{1}{2} &\text{if } i,j = 1,-1\\
\frac{1}{2} &\text{if } i,j = 1,0\\
\frac{1}{2} &\text{if } i,j = 1,1\\
\end{cases}$$
    
$$P(s_t=1~|~G_t = i,~W_t=j) = \begin{cases}
\frac{1}{2} &\text{if } i,j = 1,-1\\
\frac{1}{2} &\text{if } i,j = 1,0\\
\frac{1}{2} &\text{if } i,j = 1,1\\
1 &\text{if } i,j = 0,-1\\
\end{cases}$$
    

## Discrete Transition models

The latent variables $W_t$ and $G_t$ are independent. We have the following transition probabilities for $W_t$:

- $P(W_t = i~|~W_{t-1} = j) = \frac{1}{3}$  for all  $i,j \in \{ -1,0,1\}$.
- Note that $0\leq \alpha, B \leq 1$ are learnable parameters. As $\alpha$ grows, the chances of getting spoofed between successive time step grows. On the other hand, $\beta$ determines the type of spoofing. If $\beta \approx 0,$ then the spoofer is likely conducting stealthy attack, where larger values of $\beta$ might indicate an attempt to compromise the UAV or confuse the controller.

$$P(G_t = i~|~ G_{t-1} = j) = \begin{cases}
\alpha &\text{when} ~i =1,~j=0\\
\beta  &\text{when} ~i =0,~j=1\\
1-\alpha &\text{when} ~i =0,~j=0\\
1-\beta &\text{when} ~i =1,~j=1\\
\end{cases}$$

- To get the state transition matrix, we can simply multiply the state transition matrices of the spoofing variable and the wind variable. We can fix the following ordering of our states:
    
$$\{0,1\} \times \{-1,0,1 \} = \{(0,-1), (0,0), (0,1), (1, -1), (1, 0), (1,1)\}$$
    
- Prior distribution:

$$P(G_0) ~\otimes~ P(W_0) =  [\frac{\beta}{\alpha+\beta}, \frac{\alpha}{\alpha+\beta}] ~\otimes~ [\frac{1}{3}, \frac{1}{3}, \frac{1}{3}]$$

## Inference 

- For now, we apply a simple filtering technique that will estimate $P(G_t~|~o_{0:t})$, where $o_{0:t}$ is the sequence of observations $(r_0, s_0, Q_0), \cdots, (r_t, s_t, Q_t)$. 
- This is achieved by marginalizing wind variable $W_t$ from the latent state $S_t = (G_t, W_t)$. Recall that our latent variable has 6 joint states given by $\{(0,-1), (0,0), (0,1), (1, -1), (1, 0), (1,1)\}$
- Define $$\alpha_t(i) = P(S_i ~|~o_{0:t}$$ over six joint states. 
- For each of the possible six states, we can define emission probability given by $$b_t(i) = P(o_{t}~|~S_i)$$ 
- This leads us to an iterative formula for $\alpha_t(j)$: $$\alpha_t(j) = \gamma \cdot b_t(j) \sum_{i=1}^{6} \alpha_{t-1}(i) T_{ij}$$ where $T_{ij}$ is the transition probability from state $i$ to state $j$ and $\gamma$ is the normalizing constant. 


## Future work

- Moving from velocity to acceleration in 3D. 
- Considering Gaussian mixture models.
- Using EM or Variational Inference for learning.


