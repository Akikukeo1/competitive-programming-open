# AtCoder Heuristic Contest - Problem Summary & Specification

## 1. Problem Overview
The goal is to control a cleaning robot on an $N \times N$ grid to collect $M$ scattered balls and deliver each ball to its corresponding basket. The objective is to find the **shortest possible sequence of controller commands** (which includes movement, picking/dropping balls, and macro operations) that successfully places all balls into their correct baskets within a given execution limit $T$.

---

## 2. Environment & Elements

### Grid Specification
* **Size**: $N \times N$ cells. Top-left is $(0,0)$, bottom-right is $(N-1,N-1)$.
* **Walls**: The outer boundary is completely enclosed by walls. Internal walls may exist between adjacent cells.
* **Connectivity**: It is guaranteed that all cells are mutually reachable from any other cell without crossing walls (no isolated regions).

### Objects
* **Balls and Baskets**: There are $M$ distinct types of balls and $M$ corresponding types of baskets, indexed from $0$ to $M-1$.
* **Count**: Exactly 1 ball and 1 basket exist for each type $k$ ($0 \le k < M$).
* **Initial State**: Each cell contains at most one object (either a single ball or a single basket) initially. The robot starts at $(0,0)$, facing **Right**, and holding no ball. All initial positions of balls and baskets are unique.

---

## 3. Robot Operations

### Base Actions (Executes 1 action, increments simulation step)
* **`F` (Forward)**: Moves 1 cell in the current direction. If a wall blocks the path, the robot does not move and stays in place.
* **`R` (Right Turn)**: Rotates 90 degrees clockwise in place.
* **`L` (Left Turn)**: Rotates 90 degrees counter-clockwise in place.
* **`S` (Swap)**: Interchanges the ball currently held by the robot with the ball on the current cell.
    * *Empty hands & Ball on floor* $\rightarrow$ Picks up the ball; the floor becomes empty.
    * *Holding ball & Empty floor* $\rightarrow$ Places the ball on the floor; hands become empty.
    * *Holding ball & Ball on floor* $\rightarrow$ Swaps the held ball with the floor ball.
    * *Empty hands & Empty floor* $\rightarrow$ Nothing happens.
    * *(Note: Balls on basket cells can also be swapped freely).*

### Macro Commands (Controller operations)
* **`M` (Macro Record / End)**:
    * If **not** recording: Starts recording a macro.
    * If **currently** recording: Stops recording and saves/overwrites the sequence as the *latest registered macro*.
* **`P` (Playback)**:
    * Executes the *latest registered macro*. If no macro is registered, nothing happens.
    * If `P` is pressed *during* a macro recording, the previously registered macro is executed, and its expanded base actions are appended to the macro currently being recorded.

#### Macro Behavior Example:
Assuming the currently registered macro is `RFF`.
The sequence `MFPM` is entered:
1. `M`: Starts recording.
2. `F`: Executes `F`, appends `F` to the recording.
3. `P`: Plays `RFF`. Executes `R`, `F`, `F`, and appends `RFF` to the recording.
4. `M`: Stops recording.
* Resulting execution: `FRFF`
* Newly registered macro: `FRFF`

---

## 4. Constraints & Constraints Generation

### Parameter Ranges
* $10 \le N \le 20$
* $\lfloor N/2 \rfloor \le M \le 2N$
* $1 \le T \le 2N^2M$ ($T$ is the maximum allowed number of base actions after macro expansion).

### T Value Calculation (FYI)
$T$ is derived from the minimum grid-distance path length $X$ required to visit all balls and their baskets sequentially:
$$T = \text{round}\left((2X + 4M)^r \times (2N^2M)^{1-r}\right) \quad \text{where } r \sim \text{Uniform}(0,1)$$

---

## 5. Input & Output Formats

### Input Format

```
N
M
T
v_0
:
v_{N-1}
h_0
:
h_{N-2}
b_0 c_0 d_0 e_0
:
b_{M-1} c_{M-1} d_{M-1} e_{M-1}
```

* `v_i`: A string of length $N-1$ containing `0` and `1`. The $j$-th character `v_{i,j}` represents whether a wall exists (`1`) or not (`0`) between $(i,j)$ and $(i,j+1)$.
* `h_i`: A string of length $N$ containing `0` and `1`. The $j$-th character `h_{i,j}` represents whether a wall exists (`1`) or not (`0`) between $(i,j)$ and $(i+1,j)$.
* `b_k c_k d_k e_k`: Indicates that ball $k$ is initially at $(b_k, c_k)$ and basket $k$ is at $(d_k, e_k)$.

### Output Format
Print each command character (`F`, `R`, `L`, `S`, `M`, `P`) in the command sequence, one per line.
If the command sequence length is $A$, output exactly $A$ lines.

```
a_0
a_1
:
a_{A-1}
```

* **Constraint**: $A \le T$.
* **Truncation**: If the expanded base operations exceed $T$ steps, any operations from the $T+1$-th step onward will be completely ignored.

---

## 6. Scoring System

Let $A$ be the length of the output command string (where `M` and `P` each count as 1 command).
Let $V$ be the number of balls successfully placed in their correct baskets at the end of the simulation.

### Absolute Score (Lower is better)
* **If all balls are correctly placed ($V = M$)**:
  $$\text{Absolute Score} = A$$
* **If some balls are missing ($V < M$)**:
  $$\text{Absolute Score} = T \times (M - V)$$

### Relative Score
For each testcase, the score is normalized against the best participant's score:
$$\text{Relative Score} = \text{round}\left(10^9 \times \frac{\text{Minimum Absolute Score among all submissions}}{\text{Your Absolute Score}}\right)$$
The final standing is determined by the sum of relative scores across all test cases.

---

## 7. Key Optimization Challenges (For AI Agents)

1. **Pathfinding & TSP**: Compute all-pairs shortest paths using BFS (since edge weights are 1) accounting for walls. Determine the optimal order to visit balls and baskets (Pickup must precede Delivery for any type $k$).
2. **Buffer Utilization (Swap Mechanics)**: Since the robot can swap any held ball with a floor ball, it can temporarily drop a ball on an arbitrary empty cell or carry multiple balls indirectly via chained swaps to optimize transit routes.
3. **Macro Compression**: Condense long operational sequences (`F`, `R`, `L`, `S`) into highly repetitive macro blocks using `M` and `P`. This is structurally similar to finding the shortest grammar or utilizing hierarchical run-length compression.
