### 1: Why You Die Behind Walls in Online Games [0:00](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=0s)

[0:00](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=0s) You are playing Call of Duty. You move behind a wall, but the server says you are dead. Or you are in PUBG. You shoot an enemy perfectly in the head, [music]
[0:09](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=9s) but the bullet just disappears. This isn't your internet problem. This isn't lag. This is something called tick rate. And it's one of the most important
[0:18](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=18s) technical decisions in multiplayer games. In the next 10 minutes, I'm going to show you exactly how game servers work and how companies Riot Games
[0:26](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=26s) and Epic Games use dynamic tick rates to save millions of dollars. Let's dive in.

### 2: How Multiplayer Game Servers Work [0:38](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=38s)

[0:38](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=38s) , first let's understand what a game server does. When you are playing a multiplayer game PUBG or Fortnite, you're not directly connected
[0:47](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=47s) to other players. Instead, everyone connects to a central game server. This server is running the authoritative version of the game. It's the single
[0:56](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=56s) source of truth. Now, here is something important to understand. Not all multiplayer games need the same level of precision. Think about playing chess
[1:05](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=65s) online. When you move your knight, does it matter if the server updates 10 times per second or 100 times per second? Not really. Chess is turnbased. Once you
[1:16](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=76s) make your move, nothing happens until your opponent moves. The server can take its time. Even updating once per second would be perfectly fine. But now imagine
[1:26](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=86s) Call of Duty. You are in a gunfight and enemy appears around a corner. You have maybe 200 milliseconds to react and shoot. At this moment, every millisecond
[1:37](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=97s) matters. If the server is only updating 20 times per second, that means it's processing the game world every 50 milliseconds. In that 50 milliseconds,
[1:46](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=106s) you could have already fired three bullets, but the server hasn't even registered your first shot yet. And this is why take rate exist. Here is why this
[1:56](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=116s) matters. Imagine you and I are playing against each other. On your screen, you see yourself shoot me in the head. On my screen, I move behind a wall just in
[2:05](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=125s) time. Who is right? The server decides. The server maintains the official game state. And when there's a disagreement between what your client shows and what
[2:15](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=135s) my client shows, the server's version wins. And this is called an authoritative server architecture. And it's the industry standard for
[2:23](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=143s) preventing cheating. Now, let's talk about tick rate. Take rate is how many times per second the

### 3: What Tick Rate Means [2:28](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=148s)

[2:29](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=149s) server updates the game state. Let me give you some examples to show the difference. Chess or card games, 1 to 10 hertz is more than enough. These are
[2:39](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=159s) turnbased, no realtime action. PUBG Mobile runs at 20 to 30 Hz. It's a mobile game. Needs to work on slow devices and networks. Fortnite runs at
[2:49](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=169s) 30 to 60 Hz depending on the situation. Battle royale with 100 players needs to balance performance. Call of Duty runs
[2:58](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=178s) at 60 Hz for casual matches. Fastpace, but not ultra competitive. Valerent and Counterstrike runs at 128 Hz. These are
[3:08](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=188s) competitive shooters where every millisecond counts. if a server runs at 60 Hz, that means it's processing the game world 60 times every single second.
[3:17](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=197s) At 128 Hz, it's doing that 128 times per second. Let me show you what that server is doing in each tick. Here is

### 4: Why High Tick Rates Are Expensive [3:25](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=205s)

[3:26](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=206s) a simplified game server tick loop. It first process all player inputs received since last. It does the antiget check, update your play state, and then run
[3:35](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=215s) physics simulation. 128 hertz is 7.8 milliseconds per tick. It checks the collisions and interactions and update game logic. And
[3:46](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=226s) finally, broadcast updates to all the players. But higher trick rates are expensive. Really expensive. Let me break down the
[3:55](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=235s) numbers for you. At 128 Hz with 100 players per match, each server is processing 12,800 updates every single
[4:04](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=244s) second. Now imagine you are running a game PUBG with 100,000 concurrent matches happening globally. That's 1.28 billion updates per second across your
[4:14](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=254s) entire system. Each game server needs somewhere between 4 to 8 CPU cores just to handle this load. for 100,000 matches, you need about 600,000 CPU
[4:25](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=265s) cores running simultaneously. On cloud providers AWS or Google Cloud, each CPU core cost roughly 10 cents per hour.
[4:34](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=274s) do the math. That's $60,000 per hour just for the compute power. And that's $1.44 million per day. Over $525 million
[4:45](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=285s) per year. And that is just for the server compute cost. And this is why game companies are obsessed with optimization. Every millisecond of
[4:54](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=294s) processing time, every bite of bandwidth, it all adds up to massive cost at scale. Now compare this to something online chess. Chess
[5:03](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=303s) websites probably run their game servers at just one to five updates per second. A single server that cost maybe $100 per month can handle thousands of concurrent
[5:12](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=312s) chess games because there is little computation happening. The same workload would cost you $100,000 per month for a competitive shooter game. That's a
[5:21](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=321s) thousand times more expensive. , here is where it gets really clever. Modern

### 5: Dynamic Tick Rate Optimization [5:26](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=326s)

[5:26](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=326s) games use dynamic tick rates that adjust based on what's happening in the match. This is production level optimization that saves millions while
[5:35](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=335s) preserving gameplay quality. Let me explain how this works with a practical example from Battle Royale games PUBG. The mass starts with 100 players
[5:44](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=344s) scattered across a huge map. Most players are looting buildings, running across open fields. They are far apart and not actively fighting. Do you really
[5:54](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=354s) need 128 Hz precision when the nearest enemy is 500 m away? Probably not. Here is how the server adjusts in real time.
[6:03](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=363s) In the early game, first 5 minutes, you have 100 players spread across the map, mostly looting. The server runs at 60 Hz. This is perfectly fine because
[6:13](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=373s) players are far apart and there is minimal combat. Your cost are at the baseline level. By midame, 5 to 15 minutes in, players are converging. The
[6:24](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=384s) first circle is closing. The server is smart. It detects three to four fight zones based on gunfire and player density. Those specific zones get bumped
[6:33](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=393s) to 90 Hz while the rest of the map stays at 60 Hz. Your cost increase by about 30% but only for the areas that need it.
[6:42](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=402s) In the late game, 50 to 20 minutes, you have maybe 30 players left in increasingly tight circles with constant combat. The server detects this high
[6:51](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=411s) player density and increases to 120 Hz. Now your cost are 80% higher than baseline. But the match is almost over. it's only for a few minutes. Finally,
[7:01](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=421s) the final circle. The last 5 minutes of the match. You have say 10 players in a tiny circle where every single shot matters. The server goes full 128 Hz for
[7:10](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=430s) maximum precision. Cost are at 100%. But this is the climax of the match and it only lasts a few minutes. When you calculate the weighted average, you're
[7:19](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=439s) saving approximately 35 to 40% on server cost. while maintaining competitive precision exactly when it matters most. At the scale of games PUBG or
[7:29](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=449s) Fortnite with millions of concurrent players, this saves tens of millions of dollars every single year. The implementation is elegant. The
[7:38](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=458s) server continuously monitors several metrics. The key is making transition smooth players don't notice a change. You never want to suddenly drop from 128
[7:47](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=467s) Hz to 60 Hz in the middle of a firefight. the next time you're playing and something feels off, you'll know exactly what's happening behind the
[7:55](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=475s) scenes. Those 7.8 millconds of precision, that's the result of thousands of engineering hours and millions of dollars in infrastructure.
[8:04](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=484s) And if you want to learn more about multiplayer game architecture, do check out my links in the description. And if you are preparing for system design interviews, this deep technical
[8:12](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=492s) knowledge is exactly what distinguishes senior engineers from everyone else. Thanks for watching and I'll see you in the next video.
[8:25](https://www.youtube.com/watch?v=NVIsNDFnvOU&t=505s) [music]