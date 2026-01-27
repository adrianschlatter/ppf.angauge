# Development Notes

Some thoughts on which information and algorithms we could use to get the best
possible results.

Available information that we can use:

* watermeter does not move backwards
* some watermeter increments are more likely than others: Negative increments
  even have zero probability but we also know that very lange increments are
  unrealistic, too.
* error of hand tracking: We have an error bar for every hand-estimate

Arsenal of algorithms:

* Bayesian inference
* Viterbi algorithm: We can use the Viterbi algorithm to find the most likely
  sequence of hand estimates given the observed data and the known
  probabilities of increments.
* Kalman filter: We can use the Kalman filter to smooth the hand estimates and
  to predict the next value based on the previous values.


## Bayesian Inference

* We start from the previous estimate and use an exponential distribution
  starting at that value as prior.
* For each hand in turn, we update the prior
* Basic result: The a posteriori distribution becomes a combination of
  Gaussians with varying heights and widths.

Unsolved: To obtain the maximum-likelihood estimate, we have to find the
maximum of this complicated a posteriori distribution.


### Finding the Maximum

First, let's consider a simple parabola:

$$\begin{align*}
y(x) &= -a \cdot x^2 + b \cdot x + c
\end{align*}$$


The single extremum is where the derivative is zero

$$\begin{align*}
y'(\hat{x}) = -2a \cdot x + b = 0 \Rightarrow \hat{x} = \frac{b}{2a}
\end{align*}$$

and assumes the value

$$\begin{align*}
\hat{y} = y(\hat{x}) = \frac{b^2}{4a} + c.
\end{align*}$$

<!-- We will deal with superpositions of such parabolas, i.e., we have a sum of -->

<!-- $y_i(x) = -a_i \cdot x^2 + b_i \cdot x + c_i$. -->

<!-- This sum is again a parabola: -->

<!-- $y(x) = -\sum_i a_i \cdot x^2 + \sum_i b_i \cdot x + \sum_i c_i$ -->

<!-- with coefficients -->

<!-- $a = \sum_i a_i$, $b = \sum_i b_i$, and $c = \sum_i c_i$, -->

<!-- with an extremum at -->

<!-- $\hat{x} = \frac{\sum_i b_i}{2 \cdot \sum_i a_i}$ -->

<!-- assuming the value -->

<!-- $\hat{y} = \frac{\left(\sum_i b_i\right)^2}{4 \cdot \sum_i a_i} + \sum_i c_i$. -->

Our log-likelihood function is a sum of such parabolas, too. However, the
argument $x$ is somewhat unusual:

$$\begin{align*}
x(s) = ((s \cdot 10^{-k} - h_k + 5) \mod 10) - 5
\end{align*}$$

where $s$ the state of the watermeter and $h_k$ the hand reading for digit $k$.
The "+5 ... -5" is just a shift to center the parabola around zero. We want to
rewrite this without modulo:

$$\begin{align*}
x(s) = s \cdot 10^{-k} - h_k - 10 \cdot i_k
\end{align*}$$

where $i_k$ is an integer that we can choose to make $x(s)$ as close to zero as
possible. The log-likelihood function for digit $k$ has the form:

$$\begin{align*}
y_k(s) = -a_k \cdot (s \cdot 10^{-k} - h_k - 10 \cdot i_k)^2 + c_k
\end{align*}$$

where $a_k$ and $c_k$ are the parameters of the Gaussian for digit $k$ ($b_k$
is zero). Note that $i_k$ is the index of the Brillouin zone that we are
currently in. $y_k(s)$ describes the parabola valid for Brillouin zone $i_k$.
Let's expand this as

$$\begin{align*}
y_k(s) &= -a_k \cdot [10^{-2k} s^2
          - 2 (h_k + 10 \cdot i_k) \cdot 10^{-k} s
          + (h_k + 10 i_k)^2] + c_k
\end{align*}$$

and sort by powers of $s$:

$$\begin{align*}
y_k(s) = &-10^{-2k} a_k \cdot s^2 \\
         &+ 10^{-k} \cdot 2 a_k \cdot (h_k + 10 i_k) \cdot s \\
         &+ c_k - a_k \cdot (h_k + 10 i_k)^2
\end{align*}$$

The log-likelihood function is then the sum of all $y_k(s)$:

$$\begin{align*}
y(s) = &- \left( \sum_k 10^{-2k} a_k \right) \cdot s^2 \\
       &+ \left( \sum_k 10^{-k} \cdot 2 a_k \cdot (h_k + 10 i_k) \right) \cdot s \\
       &+ \left( \sum_k c_k - a_k \cdot (h_k + 10 i_k)^2 \right)
\end{align*}$$

Note that for each hand $k$, we have a separate Brillouin index $i_k$ because
each hand generates its own set of Brillouin zones.

Now we use the formula for the extremum of a parabola to find the position of
the maximum

$$\begin{align*}
\hat{s}_{i_1, ..., i_n} &= \frac{\sum_k 10^{-k} a_k \cdot (h_k + 10 i_k)}
                {\sum_k 10^{-2k} a_k}
\end{align*}$$

and the value of the maximum:

$$\begin{align*}
\hat{y}_{i_1, ..., i_n} = & \frac{\left(\sum_k 10^{-k} 2 a_k \cdot (h_k + 10 i_k)\right)^2}
                {4 \cdot \sum_k 10^{-2k} a_k} \\
                &+ \sum_k \left( c_k - a_k \cdot (h_k + 10 i_k)^2 \right)
\end{align*}$$

From the huge number of Brillouin-zone combinations, we have to find the best
one. Note that (multiple) combination are indeed relevant, as the Brillouin
zone of hand -1 may cut a Brillouin zone of hand -2 in half. Then, we have to
find the combination resulting in the higher maximum.

We could try all combinations and choose the highest one (massive combinatorial
impact). However, we can do better: We treat $\hat{y}_{i_1, ..., i_n}$ as a
continuous function of the $i_k$ (i.e., as if $i_k$ were real numbers) and use
the gradient to find the maximum.

$$\begin{align*}
\frac{\partial \hat{y}_{i_1, ..., i_n}}{\partial i_j}
    &= 2 \cdot \frac{\sum_k 10^{-k} 2 a_k \cdot (h_k + 10 i_k)}
                {4 \cdot \sum_k 10^{-2k} a_k} \cdot
                10^{-j} a_j \cdot 10 \\
      - a_j \cdot 2 \cdot (h_j + 10 i_j) \cdot 10 \\
    &= \frac{\sum_k 10^{-k} a_k \cdot (h_k + 10 i_k)}
       {\sum_k 10^{-2k} a_k} \cdot 10^{1 - j} a_j
      - 20 a_j \cdot (h_j + 10 i_j) \\
    &= 10 a_j \cdot \left(
       \left( \sum_k 10^{-2k} a_k \right)^{-1} \cdot
       \left( \sum_k 10^{-k-j} a_k \cdot \left( h_k + 10 i_k \right) \right)
       - 2 (h_j + 10 i_j) \right)
\end{align*}$$

Setting this to zero, we get the condition for the maximum:

$$\begin{align*}
\left( \sum_k 10^{-(k+j)} a_k \cdot (h_k + 10 i_k) \right)
    - 2 C (h_j + 10 i_j) = 0
\end{align*}$$

where $C = \sum_k 10^{-2k} a_k$.

$$\begin{align*}
\left( \sum_k 10^{-(k+j)} a_k \cdot h_k \right)
+ \left( \sum_k 10^{-(k+j)} a_k \cdot 10 \cdot i_k \right)
    - 2 C \cdot h_j - 2 C \cdot 10 i_j = 0
\end{align*}$$

$$\begin{align*}
10^{-j} \cdot \left( \sum_k 10^{-k} a_k \cdot i_k \right)
    - 2 C \cdot i_j
= 2 C \cdot h_j - 10^{-j-1} \left( \sum_k 10^{-k} a_k \cdot h_k \right)
\end{align*}$$

which has the form

$$\begin{align*}
A \cdot \vec{i} = \vec{b}
\end{align*}$$

where $A$ is a matrix with elements $A_{jk} = 10^{1-(k+j)} a_k$ and
$\vec{b}$ is a vector with elements $b_j = 2 C \cdot 10 h_j - \sum_k
10^{-(k+j)} a_k \cdot h_k$.

Therefore,

$$\begin{align*}
\vec{i} = A^{-1} \cdot \vec{b}
\end{align*}$$


## Viterbi Algorithm

The Viterbi algorithm is used to find the most likely sequence of states
through a Hidden Markov Model (HMM) given a sequence of observations. The state
of the HMM is not observed directly. Instead, each state produces a random
variable with a certain probability distribution. This random variable is
observed. Moreover, state transitions are associated with probabilities.

Caution:

* The Viterbi algorithm is designed for finite state machines. The state of the
  watermeter - however - is continuous.
* The algorithm (usually) works with univariate observations. Our (natural)
  observables are multivariate (one for each hand).

In the discrete case, the Viterbi algorithm tracks for each time step the
maximum possible likelihood to end in each state (think of a trellis diagram
with each step represents a column and each state a row).

Let's say we are at step t and we have determined - for each state s - the
maximum likelihood to arrive at that state. We do not store all possible paths
to arrive at that state nor do we store the likelihood for every path ending in
that state. We have already determined the best way to get to that state and
have stored only that likelihood value. => F_t(i) represents the max (log-)
likelihood to get to state i at step t.

Now, we want to determined the same for the next step t+1. This is simply:

F_{t+1}(i) = max_{j} (F_t(j) + P_transition(j->i) + P_observation(i, t+1))

How to read this: We want to find the best way to arrive at state i at step
t+1. What are the options? Well, we could have been in any state j at the
previous step t. From state j, we would have needed to, first, transition to
state i and, second, emit the observation o_{t+1}. For every starting state j,
we get a likelihood that depends on: The likelihood to have been at state j at
the previous step, the transition probability from state j to state i, and the
probability to emit the observation o_{t+1} while being in state i. After
considering all possible starting states j, we just keep the one with the best
likelihood. Of course, we have to repeat this for every target state i.

While we still have to calculate n**2 possibilities (n = number of states), the
algorithm avoids having to keep a longer history than just the previous step.


### Continuous Viterbi Algorithm

The more states we have, the more laborious the calculation becomes. For
continuous state spcae, n tends to infinity. However, I think we can get a
continuous variant of the Viterbi algorithm by using analytic distribution
*functions*.

At step t, we know the (logarithmic) distribution function f_t(x) of state x.
The distribution function must have analytic form - say a polynomial of degree
2 - so that we can store only its parameters. Provided that we can determine
the maximum of the chosen class of distributions function analytically, too,
the update rule becomes:

f_{t+1}(x) = max_{x'} (f_t(x') + P_transition(x'->x) + P_observation(x, t+1))

The result is then a new set of coefficients parameterizing the distribution
function at step t+1.


Notes:

P_transition(x'->x) should be something like log(exp(-(x - x') /
sigma_transition)) IF (x-x') > 0 ELSE -inf. This IF is a problem for the
analytic form. We could work around it by using a Gaussian (with a maximum at
some realistic positive increment). This would not forbid the watermeter from
going backwards but at least penalize negative increments. To catch outliers
(misreadings), this is may be good enough: The outlier would be penalized once
for creating a huge step forward and then again for the necessary huge step
backwards to explain the next (good) reading. Setting the estimated state to a
"good" value would avoid transition penalties and only receive one penalty for
an unlikely observation.

P_observation(x, t) should also be in the class of 2nd-grade polynomials. This
means we cannot take the state s, determine its first, second, third, ... digit
(for each hand) and then use the mean-squared deviation of each to the observed
hand position. Instead, we may have combine the hand-reading into a meter
reading first, and the use a Gaussian around this (probably with a fixed width
representing the error bar).


## Kalman Filter

* Prediction: Based on "meter cannot run backwards"
* Observation: Hand estimates

Notes:

Also relies on Gaussian distributions. Could be generalized using a particle
filter but this is probably computationally expensive (and performance is
critical as I want it to run on an ESP32).
