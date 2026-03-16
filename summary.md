## TL;DR
Here's a TL;DR summary in 4 sentences:

Online multiplayer games use a "tick rate" system to update the game state within a limited timeframe, which can lead to unexpected deaths and missed shots, despite players taking cover or making precise shots. This tick rate is directly linked to the server's update frequency, with higher tick rates providing a tighter response time but increasing the computational cost and hardware requirements. As a result, game studios must balance the need for fast and responsive gameplay with the expense of maintaining high-tick rate servers, particularly for competitive and fast-paced games. Some studios have also implemented dynamic tick rate optimization to reduce costs while maintaining gameplay performance.

## Chapter Summaries

### 1: Why You Die Behind Walls in Online Games [0:00](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=0s)
### Why You Die Behind Walls [0:00](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=0s)

1. You duck behind cover but server says you're dead
2. Perfect headshots vanish
3. Not your internet—it's tick rate
4. Tick rate is a key cost-saving lever for studios like Riot & Epic

> ⭐ Tick rate is the silent gatekeeper of every multiplayer firefight

### 2: How Multiplayer Game Servers Work [0:38](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=38s)
### 2: How Multiplayer Game Servers Work [0:38](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=38s)

1. Central authoritative server
   1. all players connect to it, not to each other
   2. holds the single source of truth for game state

2. Precision needs vary by genre
   1. turn-based (chess): 1 update/sec enough
   2. fast FPS (Call of Duty): every ms matters

3. Tick rate = updates per second
   1. 20 tick = 50 ms gap → shots can be missed
   2. higher tick reduces perceived lag

4. Authoritative server resolves conflicts
   1. when clients disagree, server version wins
   2. standard anti-cheat measure

> ⭐ Authoritative server architecture is the industry-standard method to prevent cheating in multiplayer games.

### 3: What Tick Rate Means [2:28](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=148s)
### What Tick Rate Means [2:28](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=148s)

1. Tick rate = how often server updates game state per second
2. Examples by genre
   1. Chess/card games: 1–10 Hz (turn-based, no realtime action)
   2. PUBG Mobile: 20–30 Hz (mobile, slow devices/networks)
   3. Fortnite: 30–60 Hz (100-player BR, performance balance)
   4. Call of Duty: 60 Hz (fast casual matches)
   5. Valorant/CS: 128 Hz (competitive, every ms counts)
3. 60 Hz = 60 world updates/sec; 128 Hz = 128/sec

> ⭐ Higher tick rate shrinks time between updates, tightening competitive edge

### 4: Why High Tick Rates Are Expensive [3:25](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=205s)
### 4: Why High Tick Rates Are Expensive [3:25](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=205s)

1. 128 Hz server loop
   1. 7.8 ms to process inputs, physics, broadcast
2. 100-player match = 12,800 updates/s per server
3. 100,000 global matches = 1.28 B updates/s
4. Hardware bill
   1. 600k CPU cores needed
   2. $60k/h → $525m/yr on cloud
5. Chess contrast: 1–5 Hz, one $100 server handles thousands of games

> ⭐ A shooter costs 1000× more per active user than chess because of tick-rate math.

### 5: Dynamic Tick Rate Optimization [5:26](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=326s)
### Dynamic Tick Rate Optimization [5:26](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=326s)

1. Servers adjust tick rate in real time based on match conditions
   1. Early game: 60 Hz for 100 distant players
   2. Mid game: 90 Hz in 3-4 fight zones, 60 Hz elsewhere
   3. Late game: 120 Hz for 30 players in tight circles
   4. Final circle: 128 Hz for last 10 players

2. Cost savings scale with player proximity
   1. 35-40 % average server cost reduction
   2. Tens of millions saved yearly for titles like PUBG/Fortnite

3. Implementation keeps transitions invisible
   1. Continuous metric monitoring
   2. No jarring drops mid-firefight

> ⭐ 7.8 ms precision during climax costs millions in infra yet only lasts minutes
