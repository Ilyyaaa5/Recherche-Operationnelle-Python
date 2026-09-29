"""
=============================================================================
  DESKTOP APPLICATION - OPERATIONAL RESEARCH
  Networks & Telecommunications - Mohammadia School of Engineers (EMI)
  Student: Ilyas BOUJAY  |  Professor: Dr. EL MKHALET MOUNA  |  2026
=============================================================================
"""

import tkinter as tk
from tkinter import ttk
import random, math, heapq
from collections import defaultdict, deque
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import FancyArrowPatch
import numpy as np

# ── Color palette ──────────────────────────────────────────────────────────
BG_DARK      = "#0D1117"
BG_CARD      = "#161B22"
BG_PANEL     = "#1C2128"
ACCENT_BLUE  = "#2188FF"
ACCENT_GREEN = "#28A745"
ACCENT_RED   = "#DC3545"
ACCENT_GOLD  = "#F6C90E"
TEXT_WHITE   = "#E6EDF3"
TEXT_GRAY    = "#8B949E"
BORDER_COL   = "#30363D"
POPUP_BG     = "#0A0E14"

# ── Node names: A, B, …, Z, AA, AB, … ────────────────────────────────────
def node_name(i):
    if i < 26:
        return chr(65 + i)
    return chr(65 + i // 26 - 1) + chr(65 + i % 26)

# ══════════════════════════════════════════════════════════════════════════
#   SCROLLABLE POPUP — Step-by-step calculations
# ══════════════════════════════════════════════════════════════════════════

class DetailPopup(tk.Toplevel):
    def __init__(self, master, title, sections):
        super().__init__(master)
        self.title(f"Detailed Calculations – {title}")
        self.configure(bg=POPUP_BG)
        w, h = 900, 640
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(True, True)
        self._build(title, sections)

    def _build(self, title, sections):
        tk.Frame(self, bg=ACCENT_BLUE, height=4).pack(fill=tk.X)
        hdr = tk.Frame(self, bg=BG_CARD)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"  {title}  —  Step-by-step Calculations",
                 bg=BG_CARD, fg=TEXT_WHITE,
                 font=("Consolas", 12, "bold")).pack(side=tk.LEFT, padx=16, pady=10)
        tk.Button(hdr, text="X  Close", bg=ACCENT_RED, fg="white",
                  bd=0, padx=12, pady=4, cursor="hand2",
                  font=("Segoe UI", 9, "bold"),
                  command=self.destroy).pack(side=tk.RIGHT, padx=12, pady=8)
        tk.Frame(self, bg=BORDER_COL, height=1).pack(fill=tk.X)

        canv   = tk.Canvas(self, bg=POPUP_BG, bd=0, highlightthickness=0)
        scy    = ttk.Scrollbar(self, orient="vertical",   command=canv.yview)
        scx    = ttk.Scrollbar(self, orient="horizontal", command=canv.xview)
        canv.configure(yscrollcommand=scy.set, xscrollcommand=scx.set)
        scy.pack(side=tk.RIGHT,  fill=tk.Y)
        scx.pack(side=tk.BOTTOM, fill=tk.X)
        canv.pack(side=tk.LEFT,  fill=tk.BOTH, expand=True)

        inner = tk.Frame(canv, bg=POPUP_BG, padx=20, pady=14)
        wid   = canv.create_window((0, 0), window=inner, anchor="nw")
        canv.bind("<Configure>",  lambda e: canv.itemconfig(wid, width=e.width))
        inner.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
        canv.bind_all("<MouseWheel>", lambda e: canv.yview_scroll(-1*(e.delta//120), "units"))

        for (sec_title, lines) in sections:
            sec_f = tk.Frame(inner, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COL)
            sec_f.pack(fill=tk.X, pady=(10, 2))
            tk.Label(sec_f, text=f"  >>  {sec_title}", bg=BG_CARD, fg=ACCENT_GOLD,
                     font=("Consolas", 10, "bold"), anchor="w").pack(fill=tk.X, padx=8, pady=5)
            for line in lines:
                if line.startswith("Iter") or line.startswith("----"):
                    fg = ACCENT_GOLD
                    fnt = ("Consolas", 10, "bold")
                elif "|" in line:
                    fg = TEXT_WHITE
                    fnt = ("Consolas", 10)
                elif line.startswith("OK") or line.startswith("DONE"):
                    fg = ACCENT_GREEN
                    fnt = ("Consolas", 9, "bold")
                elif line.startswith("  ->") or line.startswith("  =>"):
                    fg = "#7ECFFF"
                    fnt = ("Consolas", 9)
                elif line.startswith("  ["):
                    fg = TEXT_WHITE
                    fnt = ("Consolas", 9)
                elif line.startswith("  !!"):
                    fg = ACCENT_RED
                    fnt = ("Consolas", 9, "bold")
                elif line.startswith("  //"):
                    fg = TEXT_GRAY
                    fnt = ("Consolas", 8, "italic")
                else:
                    fg = TEXT_GRAY
                    fnt = ("Consolas", 8)
                
                tk.Label(inner, text=line, bg=POPUP_BG, fg=fg, font=fnt,
                         anchor="w", justify=tk.LEFT, wraplength=1200).pack(fill=tk.X, padx=4, pady=1)

        tk.Frame(inner, bg=BORDER_COL, height=1).pack(fill=tk.X, pady=10)
        tk.Button(inner, text="X  Close", bg=ACCENT_RED, fg="white",
                  bd=0, padx=20, pady=6, cursor="hand2", font=("Segoe UI", 10, "bold"),
                  command=self.destroy).pack()

# ══════════════════════════════════════════════════════════════════════════
#   DETAIL BUILDERS
# ══════════════════════════════════════════════════════════════════════════

class DetailBuilder:
    @staticmethod
    def dijkstra(graph, n, src, dst):
        INF  = float('inf')
        dist = [INF]*n
        prev = [-1]*n
        dist[src] = 0
        unvisited = set(range(n))
        
        # --- Dijkstra Table Generation ---
        lines = []
        col_w = 12
        hdr = f"{'Iter':<5} | " + " | ".join(f"{node_name(i):^{col_w}}" for i in range(n))
        lines.append(hdr)
        lines.append("-" * len(hdr))
        
        iteration = 1
        cell_strs = ["inf"] * n
        cell_strs[src] = "0"
        
        # Row 1 (Initial state)
        row1 = [f"{iteration:<5}"]
        for i in range(n):
            row1.append(f"{cell_strs[i]:^{col_w}}")
        lines.append(" | ".join(row1))
        
        # Track finalized nodes for 'X'
        finalized = set()
        
        while unvisited:
            # Find min dist node in unvisited
            u = min(unvisited, key=lambda node: dist[node])
            if dist[u] == INF: break
            
            unvisited.remove(u)
            finalized.add(u)
            iteration += 1
            
            # Update neighbors
            for v, w in graph[u]:
                if v in unvisited:
                    if dist[u] + w < dist[v]:
                        dist[v] = dist[u] + w
                        prev[v] = u
                        val_str = "0" if dist[u]==0 else str(dist[u])
                        # Format math like: 10+28=38.B
                        cell_strs[v] = f"{val_str}+{w}={dist[v]}.{node_name(u)}"
            
            # Build display row
            row_display = [f"{iteration:<5}"]
            for i in range(n):
                if i in finalized and i != u:
                    # Crossed out nodes from past iterations
                    row_display.append(f"{'X':^{col_w}}")
                elif i == u:
                    # Node finalized in this specific iteration gets marked
                    row_display.append(f"{'X':^{col_w}}")
                else:
                    # Not finalized
                    row_display.append(f"{cell_strs[i]:^{col_w}}")
                    
                    # Clean the math for the next iteration 
                    # (turns "10+20=30.B" into "30.B" for the subsequent rows)
                    if "=" in cell_strs[i]:
                        cell_strs[i] = f"{dist[i]}.{node_name(prev[i])}"
                        
            lines.append(" | ".join(row_display))
            
        sections = []
        sections.append(("Tableau d'exécution (Méthode du cours)", lines))

        # --- Rebuild Optimal Path ---
        path = []
        cur = dst
        while cur != -1: 
            path.insert(0, cur)
            cur = prev[cur]

        SL = node_name(src)
        DL = node_name(dst)
        ol = []
        if not path or path[0] != src: 
            ol.append(f"  !! Aucun chemin trouvé de {SL} à {DL}")
        else:
            ol.append(f"  -> Chemin optimal : {' -> '.join(node_name(x) for x in path)}")
            ol.append(f"  -> Coût total     : {dist[dst]}\n")
            ol.append("  // Décomposition du chemin :")
            for a, b in zip(path[:-1], path[1:]):
                w = next((ww for vv,ww in graph[a] if vv==b), "?")
                ol.append(f"       {node_name(a)} -> {node_name(b)} :  poids = {w}")
                
        sections.append((f"Chemin optimal {SL} -> {DL}", ol))
        return sections, dist, prev, path

    @staticmethod
    def welsh_powell(adj, n):
        degrees = sorted([(len(adj[i]), i) for i in range(n)], reverse=True)
        color   = [-1]*n
        steps   = []
        
        for deg, v in degrees:
            nc = {color[u] for u in adj[v] if color[u] != -1}
            c  = 0
            while c in nc: 
                c += 1
            color[v] = c
            steps.append((v, deg, list(adj[v]), nc, c))
            
        chromatic = max(color)+1
        sections = []
        sl = ["  // Nodes sorted by descending degree:", ""]
        for deg, v in degrees:
            vois = [node_name(u) for u in adj[v]]
            sl.append(f"     {node_name(v)} :  degree = {deg}   neighbors = {{ {', '.join(vois) if vois else 'none'} }}")
            
        sections.append(("Step 1 — Sort nodes by descending degree", sl))
        cl = []
        for (v, deg, vois, nc, c) in steps:
            nc_s = "{" + ", ".join(f"C{x+1}" for x in nc) + "}" if nc else "{}"
            cl.append(f"  [{node_name(v)}]  degree={deg}  neighbor colors={nc_s}")
            cl.append(f"  ->   Smallest available color = C{c+1}  =>  {node_name(v)} <- C{c+1}\n")
            
        sections.append(("Step 2 — Color assignment (greedy)", cl))
        rl = []
        for ci in range(chromatic):
            nodes_ci = [node_name(i) for i in range(n) if color[i]==ci]
            rl.append(f"  -> Channel C{ci+1}  =>  nodes : {{ {', '.join(nodes_ci)} }}")
            
        rl.append(f"\nDONE  Chromatic number chi(G) = {chromatic}")
        sections.append(("Result — Coloring", rl))
        return sections, color, chromatic

    @staticmethod
    def kruskal(edges, n):
        parent = list(range(n))
        rank = [0]*n
        
        def find(x):
            while parent[x]!=x: 
                parent[x]=parent[parent[x]]
                x=parent[x]
            return x
            
        def union(a, b):
            ra,rb=find(a),find(b)
            if ra==rb: return False
            if rank[ra]<rank[rb]: ra,rb=rb,ra
            parent[rb]=ra
            if rank[ra]==rank[rb]: rank[ra]+=1
            return True
            
        edges_s = sorted(edges, key=lambda e: e[2])
        mst=[]
        total=0
        steps=[]
        
        for u,v,w in edges_s:
            ok = union(u,v)
            if ok: 
                mst.append((u,v,w))
                total+=w
            steps.append((u,v,w,ok,len(mst)))
            if len(mst)==n-1: break
            
        sections = []
        sl = ["  // All edges sorted by ascending weight:", ""]
        for u,v,w in edges_s: 
            sl.append(f"     {node_name(u)}-{node_name(v)}  :  weight = {w}")
            
        sections.append(("Step 1 — Sort edges by ascending weight", sl))
        al = []
        for (u,v,w,ok,cnt) in steps:
            if ok: 
                al.append(f"  -> Edge {node_name(u)}-{node_name(v)} (w={w})  ACCEPTED  (no cycle)   [MST: {cnt}/{n-1} edges]\n")
            else: 
                al.append(f"  !! Edge {node_name(u)}-{node_name(v)} (w={w})  REJECTED  (would form a cycle)\n")
                
        sections.append(("Step 2 — Build Minimum Spanning Tree", al))
        ml = []
        for u,v,w in mst: 
            ml.append(f"  -> {node_name(u)}-{node_name(v)}  :  w = {w}")
            
        ml.append(f"\nDONE  Total MST cost = {total}")
        sections.append(("Result — Minimum Spanning Tree", ml))
        return sections, mst, total

    @staticmethod
    def bellman_ford(dir_edges, n, src):
        INF = float('inf')
        dist = [INF]*n
        prev = [-1]*n
        dist[src] = 0
        history = []
        
        for it in range(n-1):
            updates = []
            any_upd = False
            for u,v,w in dir_edges:
                if dist[u]!=INF and dist[u]+w < dist[v]:
                    old=dist[v]
                    dist[v]=dist[u]+w
                    prev[v]=u
                    updates.append((u,v,w,old,dist[v],True))
                    any_upd=True
                else:
                    updates.append((u,v,w,dist[v],dist[v],False))
            history.append((it+1, updates, dist[:]))
            if not any_upd: break
            
        neg = any(dist[u]!=INF and dist[u]+w<dist[v] for u,v,w in dir_edges)
        sections = []
        il=[f"  // Source = {node_name(src)}  (directed graph)", ""]
        for i in range(n): 
            il.append(f"     d({node_name(i)}) = {'0' if i==src else 'inf'}")
            
        sections.append(("Initialisation", il))
        
        for (it, updates, snap) in history[:6]:
            itl=[]
            changed=[x for x in updates if x[5]]
            if not changed: 
                itl.append("  // No update — algorithm converged.")
            for u,v,w,old,new,_ in changed:
                old_s="inf" if old==INF else str(old)
                itl.append(f"  -> {node_name(u)}->{node_name(v)} :  d({node_name(u)})+{w} = {new}  <  {old_s}  => d({node_name(v)}) = {new}")
            row="     State: "
            for i in range(n):
                dv="inf" if snap[i]==INF else str(snap[i])
                row+=f"d({node_name(i)})={dv}  "
            itl.append(row)
            sections.append((f"Iteration {it}", itl))
            
        rl=[]
        for i in range(n):
            if i==src: continue
            dv="inf" if dist[i]==INF else str(dist[i])
            p=[]
            c=i
            while c!=-1: 
                p.insert(0,c)
                c=prev[c]
            if p and p[0]==src: 
                rl.append(f"  -> {node_name(src)}->{node_name(i)} :  cost={dv}   path={'->'.join(node_name(x) for x in p)}")
            else: 
                rl.append(f"  !! {node_name(src)}->{node_name(i)} :  unreachable")
                
        if neg: 
            rl.append("  !! NEGATIVE CYCLE DETECTED — distances unreliable!")
        else: 
            rl.append("OK   No negative cycle detected.")
            
        sections.append(("Final distances from "+node_name(src), rl))
        return sections, dist, prev, neg

    @staticmethod
    def ford_fulkerson(cap_orig, n, source, sink):
        cap = [row[:] for row in cap_orig]
        flow_mat = [[0]*n for _ in range(n)]
        INF = float('inf')
        
        def bfs(s,t,parent):
            vis=[False]*n
            q=deque([s])
            vis[s]=True
            while q:
                u=q.popleft()
                for v in range(n):
                    if not vis[v] and cap[u][v]>0:
                        q.append(v)
                        vis[v]=True
                        parent[v]=u
                        if v==t: return True
            return False
            
        max_flow=0
        aug_paths=[]
        
        while True:
            parent=[-1]*n
            if not bfs(source,sink,parent): break
            pf=INF
            s=sink
            path=[s]
            while s!=source:
                u=parent[s]
                pf=min(pf,cap[u][s])
                s=u
                path.insert(0,s)
            max_flow+=pf
            aug_paths.append((list(path),pf))
            v=sink
            while v!=source:
                u=parent[v]
                cap[u][v]-=pf
                cap[v][u]+=pf
                flow_mat[u][v]+=pf
                v=u
                
        sections=[]
        ml=["  // Capacity matrix (rows=from, cols=to):", ""]
        ml.append("         " + "   ".join(f"{node_name(j):>3}" for j in range(n)))
        for i in range(n):
            row_s="   ".join(f"{cap_orig[i][j]:>3}" for j in range(n))
            ml.append(f"     {node_name(i)} |  {row_s}")
            
        sections.append(("Capacity Matrix", ml))
        al=[]
        
        if not aug_paths: 
            al.append(f"  !! No path from {node_name(source)} to {node_name(sink)}")
            
        cumul=0
        for k,(path,pf) in enumerate(aug_paths,1):
            cumul+=pf
            al.append(f"  [{k}]  Augmenting path : {' -> '.join(node_name(x) for x in path)}")
            for a,b in zip(path[:-1],path[1:]): 
                al.append(f"         {node_name(a)}->{node_name(b)} :  capacity = {cap_orig[a][b]}")
            al.append(f"  ->   Bottleneck = {pf}   | Cumulative flow : {cumul}\n")
            
        sections.append(("Augmenting Paths (BFS)", al))
        fl=["  // Flow on each arc  (format: flow / capacity):", ""]
        
        for i in range(n):
            for j in range(n):
                if cap_orig[i][j]>0: 
                    fl.append(f"     {node_name(i)} -> {node_name(j)} :  {flow_mat[i][j]} / {cap_orig[i][j]}")
                    
        fl.append(f"\nDONE  Maximum flow S({node_name(source)}) -> T({node_name(sink)}) = {max_flow}")
        sections.append(("Flow on Each Arc (x / capacity)", fl))
        return sections, max_flow, aug_paths, flow_mat

    @staticmethod
    def north_west(cost, supply_orig, demand_orig):
        supply=supply_orig[:]
        demand=demand_orig[:]
        m,n=len(supply),len(demand)
        alloc=[[0]*n for _ in range(m)]
        steps=[]
        i,j=0,0
        
        while i<m and j<n:
            qty=min(supply[i],demand[j])
            alloc[i][j]=qty
            steps.append((i,j,qty,supply[i],demand[j]))
            supply[i]-=qty
            demand[j]-=qty
            if supply[i]==0: 
                i+=1
            else: 
                j+=1
                
        total=sum(cost[i][j]*alloc[i][j] for i in range(m) for j in range(n))
        sections=[]
        dl=["  // Supply (S) and Demand (D):", ""]
        for k in range(m): dl.append(f"     S{k+1} = {supply_orig[k]}")
        dl.append("")
        for k in range(n): dl.append(f"     D{k+1} = {demand_orig[k]}")
        sections.append(("Problem Data", dl))
        nl=["  // Start at North-West corner (S1, D1) and move right/down", ""]
        for k,(si,sj,qty,sup_b,dem_b) in enumerate(steps,1):
            nl.append(f"  [{k}]  Cell (S{si+1}, D{sj+1}) :")
            nl.append(f"  ->   Remaining supply S{si+1} = {sup_b}  |  Remaining demand D{sj+1} = {dem_b}")
            nl.append(f"  ->   Allocation = min({sup_b}, {dem_b}) = {qty}")
            nl.append(f"  ->   Cost contribution : {qty} x {cost[si][sj]} = {qty*cost[si][sj]}\n")
            
        sections.append(("North-West Corner Steps", nl))
        tl=["  // Final allocation table:", ""]
        tl.append("         "+"   ".join(f"D{j+1:>3}" for j in range(n)))
        for i in range(m):
            row_s="   ".join(f"x={alloc[i][j]},c={cost[i][j]}" if alloc[i][j]>0 else f"  -  ,c={cost[i][j]}" for j in range(n))
            tl.append(f"  S{i+1}  | {row_s}")
            
        tl.append(f"\nDONE  Total cost (basic solution) = {total}")
        sections.append(("Allocation Table & Cost", tl))
        return sections, alloc, total

    @staticmethod
    def least_cost(cost, supply_orig, demand_orig):
        supply=supply_orig[:]
        demand=demand_orig[:]
        m,n=len(supply),len(demand)
        alloc=[[0]*n for _ in range(m)]
        done_r=[False]*m
        done_c=[False]*n
        cells=sorted([(cost[i][j],i,j) for i in range(m) for j in range(n)])
        steps=[]
        
        for _,i,j in cells:
            if done_r[i] or done_c[j]: continue
            qty=min(supply[i],demand[j])
            alloc[i][j]=qty
            steps.append((i,j,cost[i][j],qty,supply[i],demand[j]))
            supply[i]-=qty
            demand[j]-=qty
            if supply[i]==0: done_r[i]=True
            if demand[j]==0: done_c[j]=True
            
        total=sum(cost[i][j]*alloc[i][j] for i in range(m) for j in range(n))
        sections=[]
        sl=["  // All cells sorted by ascending unit cost:", ""]
        for c2,i,j in cells[:14]: 
            sl.append(f"     (S{i+1}, D{j+1})  cost = {c2}")
            
        if len(cells)>14: 
            sl.append(f"     ... {len(cells)-14} more cells")
            
        sections.append(("Step 1 — Sort cells by ascending cost", sl))
        ll=[]
        for k,(si,sj,c2,qty,sup_b,dem_b) in enumerate(steps,1):
            ll.append(f"  [{k}]  Cell (S{si+1}, D{sj+1}) — unit cost = {c2}  (lowest available)")
            ll.append(f"  ->   Supply S{si+1} = {sup_b}  |  Demand D{sj+1} = {dem_b}")
            ll.append(f"  ->   Allocation = min({sup_b}, {dem_b}) = {qty}")
            ll.append(f"  ->   Partial cost : {qty} x {c2} = {qty*c2}\n")
            
        sections.append(("Step 2 — Least Cost Assignments", ll))
        rl=[f"DONE  Total cost = {total}"]
        sections.append(("Result", rl))
        return sections, alloc, total

# ══════════════════════════════════════════════════════════════════════════
#   GRAPH GENERATORS
# ══════════════════════════════════════════════════════════════════════════

def generate_undirected(n, density=0.4, max_w=20):
    adj=defaultdict(set)
    edges=[]
    graph=defaultdict(list)
    
    for i in range(n):
        for j in range(i+1,n):
            if random.random()<density:
                w=random.randint(1,max_w)
                adj[i].add(j)
                adj[j].add(i)
                edges.append((i,j,w))
                graph[i].append((j,w))
                graph[j].append((i,w))
                
    for i in range(n-1):
        if not any(v==i+1 for v,_ in graph[i]):
            w=random.randint(1,max_w)
            adj[i].add(i+1)
            adj[i+1].add(i)
            edges.append((i,i+1,w))
            graph[i].append((i+1,w))
            graph[i+1].append((i,w))
            
    return adj,edges,graph

def generate_directed(n, density=0.4, max_w=20):
    arc_set = set()
    dir_edges = []
    graph = defaultdict(list)
    
    for i in range(n):
        for j in range(i+1, n):
            if random.random() < density:
                u, v = (i, j) if random.random() < 0.5 else (j, i)
                w = random.randint(1, max_w)
                arc_set.add((u, v))
                dir_edges.append((u, v, w))
                graph[u].append((v, w))
                
    for i in range(n - 1):
        if (i, i+1) not in arc_set and (i+1, i) not in arc_set:
            w = random.randint(1, max_w)
            arc_set.add((i, i+1))
            dir_edges.append((i, i+1, w))
            graph[i].append((i+1, w))
            
    return dir_edges, graph

def generate_flow_network(n, density=0.4, max_w=50):
    arc_set = set()
    dir_edges = []
    graph = defaultdict(list)
    
    # 0 est S (que des sorties), n-1 est T (que des entrées)
    for i in range(n):
        for j in range(n):
            if i == j: continue
            if j == 0: continue # Aucun lien n'entre dans S
            if i == n - 1: continue # Aucun lien ne sort de T
            
            # i < j garantit qu'il n'y a pas de cycles et que le flux avance
            if i < j:
                if random.random() < density:
                    w = random.randint(10, max_w)
                    w = (w // 5) * 5 # Multiples de 5 pour faire plus réaliste
                    arc_set.add((i, j))
                    dir_edges.append((i, j, w))
                    graph[i].append((j, w))
                    
    # Assurer la connectivité de base depuis S et vers T
    for i in range(1, n - 1):
        if not any(v == i for u, v in arc_set):
            w = (random.randint(10, max_w)//5)*5
            arc_set.add((0, i))
            dir_edges.append((0, i, w))
            graph[0].append((i, w))
            
        if not any(u == i for u, v in arc_set):
            w = (random.randint(10, max_w)//5)*5
            arc_set.add((i, n-1))
            dir_edges.append((i, n-1, w))
            graph[i].append((n-1, w))
            
    if not arc_set: 
         dir_edges.append((0, n-1, 20))
         
    return dir_edges, graph

def get_positions(n, W=600, H=460):
    cx,cy=W/2,H/2
    r=min(cx,cy)*0.82
    return {i:(cx+r*math.cos(2*math.pi*i/n-math.pi/2), cy+r*math.sin(2*math.pi*i/n-math.pi/2)) for i in range(n)}

def get_flow_positions(n, W=600, H=460):
    """Improved flow network positioning with proper grid layout"""
    pos = {}
    pos[0] = (W*0.1, H/2)  # S at left
    
    if n > 2:
        # Calculate grid for intermediate nodes (1 to n-2)
        intermediate_count = n - 2
        cols = int(math.ceil(math.sqrt(intermediate_count)))
        rows = int(math.ceil(intermediate_count / cols))
        
        # Calculate step sizes
        x_start = W * 0.25
        x_end = W * 0.75
        x_step = (x_end - x_start) / (cols - 1) if cols > 1 else 0
        
        y_start = H * 0.15
        y_end = H * 0.85
        y_step = (y_end - y_start) / (rows - 1) if rows > 1 else 0
        
        # Position each intermediate node
        for k in range(1, n-1):
            idx = k - 1  # 0-based index for intermediate nodes
            row = idx // cols
            col = idx % cols
            
            x = x_start + col * x_step
            y = y_start + row * y_step
            
            # Add slight random offset to avoid perfect alignment (makes it more readable)
            x += random.uniform(-15, 15)
            y += random.uniform(-20, 20)
            
            # Clamp to screen boundaries
            x = max(W*0.12, min(W*0.88, x))
            y = max(H*0.1, min(H*0.9, y))
            
            pos[k] = (x, y)
    
    pos[n-1] = (W*0.9, H/2)  # T at right
    
    # Ensure all nodes have positions (fallback)
    for i in range(n):
        if i not in pos:
            pos[i] = (W/2, H/2)
    
    return pos

# ══════════════════════════════════════════════════════════════════════════
#   WELCOME PAGE
# ══════════════════════════════════════════════════════════════════════════

class WelcomePage(tk.Frame):
    def __init__(self, master, on_start):
        super().__init__(master, bg="white")
        self.pack(fill=tk.BOTH, expand=True)
        self._build(on_start)

    def _build(self, on_start):
        tk.Frame(self, bg="#1A237E", height=6).pack(fill=tk.X)
        center = tk.Frame(self, bg="white")
        center.pack(expand=True, fill=tk.BOTH, padx=80, pady=20)

        tk.Label(center, text=('"Development of a Desktop Application Integrating Graph Algorithms,\n'
                               'PCA-Based Data Analysis, and Static and Dynamic'),
                 font=("Arial",12,"bold","italic"), fg="#1A237E", bg="white", justify=tk.CENTER).pack(pady=(30,0))
        tk.Label(center, text='Transportation Algorithms in the Networks & Telecommunications Sector"',
                 font=("Arial",12,"bold","italic"), fg="#C62828", bg="white", justify=tk.CENTER).pack()

        tk.Frame(center, bg="#BDBDBD", height=1).pack(fill=tk.X, pady=20)
        tk.Label(center, text="Mohammadia School of Engineers (EMI)", font=("Arial",14,"bold"), fg="#2E7D32", bg="white").pack()
        tk.Frame(center, bg="#BDBDBD", height=1).pack(fill=tk.X, pady=20)

        boxes=tk.Frame(center, bg="white")
        boxes.pack()
        
        for text in ["Ilyas BOUJAY","Dr. EL MKHALET MOUNA"]:
            f=tk.Frame(boxes, bd=2, relief="solid", highlightbackground="#1A237E", highlightthickness=2)
            tk.Label(f, text=text, font=("Arial",11,"bold"), fg="#1A237E", bg="white", padx=28, pady=14).pack()
            f.pack(side=tk.LEFT, padx=40)

        tk.Frame(center, bg="#BDBDBD", height=1).pack(fill=tk.X, pady=24)
        btn=tk.Button(center, text="   >   START   <   ", font=("Arial",14,"bold"), fg="white", bg="#1A237E",
                      activebackground="#283593", activeforeground="white", padx=36, pady=12, bd=0, cursor="hand2", command=on_start)
        btn.pack()
        btn.bind("<Enter>", lambda e: btn.config(bg="#283593"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#1A237E"))

        tk.Frame(self, bg="#1A237E", height=6).pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(self, text="Operational Research — Networks & Telecommunications  |  EMI 2026",
                 font=("Arial",8), fg="#757575", bg="white").pack(side=tk.BOTTOM, pady=3)

# ══════════════════════════════════════════════════════════════════════════
#   MAIN PAGE
# ══════════════════════════════════════════════════════════════════════════

class MainPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG_DARK)
        self.pack(fill=tk.BOTH, expand=True)
        self._last_sections = None
        self._last_title    = ""
        self._build()

    def _build(self):
        hdr=tk.Frame(self,bg=BG_CARD,height=52)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        
        tk.Label(hdr, text="Operational Research — Networks & Telecom  |  EMI 2026",
                 bg=BG_CARD, fg=TEXT_WHITE, font=("Segoe UI",12,"bold")).pack(side=tk.LEFT,padx=18,pady=12)
        tk.Label(hdr, text="Ilyas BOUJAY  ·  Dr. EL MKHALET MOUNA",
                 bg=BG_CARD, fg=TEXT_GRAY, font=("Segoe UI",9)).pack(side=tk.RIGHT,padx=18)
        tk.Frame(self,bg=ACCENT_BLUE,height=2).pack(fill=tk.X)

        body=tk.Frame(self,bg=BG_DARK)
        body.pack(fill=tk.BOTH,expand=True,padx=14,pady=12)

        sidebar=tk.Frame(body,bg=BG_CARD,width=220, highlightthickness=1,highlightbackground=BORDER_COL)
        sidebar.pack(side=tk.LEFT,fill=tk.Y,padx=(0,12))
        sidebar.pack_propagate(False)
        tk.Label(sidebar,text="ALGORITHMS",bg=BG_CARD,fg=ACCENT_GOLD,
                 font=("Segoe UI",8,"bold")).pack(pady=(16,4),padx=12,anchor="w")

        self.content=tk.Frame(body,bg=BG_DARK)
        self.content.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)

        menus=[
            ("  Welsh-Powell",   self._open_welsh_powell),
            ("  Kruskal",        self._open_kruskal),
            ("  Dijkstra",       self._open_dijkstra),
            ("  Bellman-Ford",   self._open_bellman_ford),
            ("  Ford-Fulkerson", self._open_ford_fulkerson),
            ("—",None),
            ("  North-West",     self._open_nord_ouest),
            ("  Least Cost",     self._open_moindre_cout),
            ("—",None),
            ("  Simplex",        self._open_simplexe),
        ]
        
        for label,cmd in menus:
            if label=="—":
                tk.Frame(sidebar,bg=BORDER_COL,height=1).pack(fill=tk.X,padx=12,pady=6)
                continue
            b=tk.Button(sidebar,text=label,bg=BG_CARD,fg=TEXT_WHITE,
                        activebackground=BG_PANEL,activeforeground=ACCENT_BLUE,
                        bd=0,padx=12,pady=8,anchor="w",cursor="hand2",
                        font=("Segoe UI",10),command=cmd)
            b.pack(fill=tk.X,padx=4,pady=1)
            b.bind("<Enter>", lambda e,btn=b: btn.config(bg=BG_PANEL,fg=ACCENT_BLUE))
            b.bind("<Leave>", lambda e,btn=b: btn.config(bg=BG_CARD, fg=TEXT_WHITE))
            
        self._show_home()

    def _clear(self):
        for w in self.content.winfo_children(): 
            w.destroy()

    def _popup_btn(self, parent):
        def open_popup():
            if self._last_sections: 
                DetailPopup(self, self._last_title, self._last_sections)
        tk.Button(parent, text="  View Detailed Calculations & Interpretation",
                  bg=ACCENT_GOLD, fg="#000", bd=0, padx=14, pady=5, cursor="hand2",
                  font=("Segoe UI",10,"bold"), command=open_popup).pack(side=tk.LEFT, padx=8)

    def _show_home(self):
        self._clear()
        f=tk.Frame(self.content,bg=BG_DARK)
        f.pack(expand=True)
        tk.Label(f,text="Network & Telecom Optimization — Morocco", bg=BG_DARK,fg=TEXT_WHITE,font=("Segoe UI",15,"bold")).pack(pady=(50,8))
        tk.Label(f,text="Select an algorithm from the left menu — a calculation popup will appear after execution",
                 bg=BG_DARK,fg=TEXT_GRAY,font=("Segoe UI",10)).pack(pady=8)
                 
        cards=[
            ("Welsh-Powell","Graph coloring -> interference-free channels"),
            ("Kruskal","MST -> optimal backbone cabling"),
            ("Dijkstra","Shortest path -> IP routing"),
            ("Bellman-Ford","Directed routing + loop detection"),
            ("Ford-Fulkerson","Max flow -> network data capacity"),
            ("North-West","Transport -> initial basic solution"),
            ("Least Cost","Transport -> optimized initial solution"),
            ("Simplex","LP -> optimal bandwidth allocation"),
        ]
        
        g=tk.Frame(f,bg=BG_DARK)
        g.pack(pady=20)
        
        for idx,(alg,desc) in enumerate(cards):
            r,c=divmod(idx,4)
            card=tk.Frame(g,bg=BG_CARD,padx=14,pady=10, highlightthickness=1,highlightbackground=BORDER_COL)
            card.grid(row=r,column=c,padx=5,pady=5,sticky="nsew")
            tk.Label(card,text=alg,bg=BG_CARD,fg=ACCENT_BLUE, font=("Segoe UI",10,"bold")).pack(anchor="w")
            tk.Label(card,text=desc,bg=BG_CARD,fg=TEXT_GRAY, font=("Segoe UI",8),wraplength=145).pack(anchor="w")

    # ── Generic graph screen ──────────────────────────────────────────────
    def _graph_screen(self, title, run_fn, show_src=False, show_dst=False):
        self._clear()
        outer=tk.Frame(self.content,bg=BG_DARK)
        outer.pack(fill=tk.BOTH,expand=True)
        tk.Label(outer,text=title,bg=BG_DARK,fg=TEXT_WHITE, font=("Segoe UI",12,"bold")).pack(anchor="w",pady=(0,6))

        ctrl=tk.Frame(outer,bg=BG_CARD,highlightthickness=1,highlightbackground=BORDER_COL)
        ctrl.pack(fill=tk.X,pady=(0,8))
        row=tk.Frame(ctrl,bg=BG_CARD)
        row.pack(fill=tk.X,padx=8,pady=8)

        def lbl(t): 
            tk.Label(row,text=t,bg=BG_CARD,fg=TEXT_GRAY, font=("Segoe UI",9)).pack(side=tk.LEFT,padx=(8,2))

        lbl("Vertices (1-100):")
        n_var=tk.IntVar(value=8)
        tk.Spinbox(row,from_=3,to=100,textvariable=n_var,width=4, bg=BG_PANEL,fg=TEXT_WHITE,insertbackground=TEXT_WHITE,bd=0).pack(side=tk.LEFT)
        
        lbl("Density (10-100%):")
        d_var=tk.IntVar(value=40)
        tk.Spinbox(row,from_=10,to=100,textvariable=d_var,width=4, bg=BG_PANEL,fg=TEXT_WHITE,insertbackground=TEXT_WHITE,bd=0).pack(side=tk.LEFT)
        
        src_var=tk.IntVar(value=0)
        dst_var=tk.IntVar(value=0)
        
        if show_src:
            lbl("Source (0-n):")
            tk.Spinbox(row,from_=0,to=99,textvariable=src_var,width=3, bg=BG_PANEL,fg=TEXT_WHITE,insertbackground=TEXT_WHITE,bd=0).pack(side=tk.LEFT)
        if show_dst:
            lbl("Dest (0-n):")
            tk.Spinbox(row,from_=0,to=99,textvariable=dst_var,width=3, bg=BG_PANEL,fg=TEXT_WHITE,insertbackground=TEXT_WHITE,bd=0).pack(side=tk.LEFT)

        res_var=tk.StringVar(value="")
        tk.Label(ctrl,textvariable=res_var,bg=BG_CARD,fg=ACCENT_GREEN, font=("Segoe UI",9,"bold"),wraplength=940,justify=tk.LEFT).pack(anchor="w",padx=12,pady=(0,5))

        canvas_frame=tk.Frame(outer,bg=BG_DARK)
        canvas_frame.pack(fill=tk.BOTH,expand=True)
        current=[None, None]

        def run():
            if current[0] is not None:
                plt.close(current[0])
                current[0] = None
            for child in canvas_frame.winfo_children(): 
                child.destroy()
            current[1] = None

            n   = n_var.get()
            d   = d_var.get() / 100
            src = src_var.get() % n
            dst = dst_var.get() % n

            fig, ax = plt.subplots(figsize=(12.0, 7.2), dpi=96)
            current[0] = fig
            fig.patch.set_facecolor(BG_DARK)
            ax.set_facecolor(BG_PANEL)
            ax.set_title(title, color=TEXT_WHITE, fontsize=10, pad=6)
            for sp in ax.spines.values(): 
                sp.set_visible(False)
            ax.set_xticks([])
            ax.set_yticks([])

            txt = run_fn(ax, n, d, src, dst)
            res_var.set(txt)

            canv = FigureCanvasTkAgg(fig, master=canvas_frame)
            current[1] = canv
            canv.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            canv.draw()

        btn_row=tk.Frame(ctrl,bg=BG_CARD)
        btn_row.pack(fill=tk.X,padx=8,pady=(0,8))
        tk.Button(btn_row,text=">  Generate & Run", bg=ACCENT_BLUE,fg="white",bd=0,padx=12,pady=5, cursor="hand2",font=("Segoe UI",10,"bold"), command=run).pack(side=tk.LEFT,padx=(0,6))
        self._popup_btn(btn_row)
        run()

    def _node_sz(self, n): return max(40, 520-n*4)
    def _font_sz(self, n): return max(4,   9-n//14)

    def _draw_nodes(self, ax, n, pos, node_colors=None, labels=None):
        sz=self._node_sz(n)
        fs=self._font_sz(n)
        xs=[pos[i][0] for i in range(n)]
        ys=[pos[i][1] for i in range(n)]
        cs=node_colors if node_colors else [ACCENT_BLUE]*n
        ax.scatter(xs,ys,s=sz,c=cs,zorder=3,edgecolors=TEXT_WHITE,linewidths=0.8)
        
        if n<=80:
            for i in range(n):
                lbl2=labels[i] if labels else node_name(i)
                tc="#111" if node_colors else "white"
                ax.text(pos[i][0],pos[i][1],lbl2,color=tc,fontsize=fs, ha="center",va="center",fontweight="bold",zorder=4)

    def _draw_undirected_edges(self, ax, edges, pos, highlight=None, hl_col=ACCENT_GREEN, show_w=True, n=10):
        for u,v,w in edges:
            key=(min(u,v),max(u,v))
            in_hl=highlight and key in highlight
            c=hl_col if in_hl else BORDER_COL
            lw=2.4 if in_hl else 0.6
            ax.plot([pos[u][0],pos[v][0]],[pos[u][1],pos[v][1]], color=c,lw=lw,zorder=1)
            
            if show_w:
                mx=(pos[u][0]+pos[v][0])/2
                my=(pos[u][1]+pos[v][1])/2
                col = ACCENT_GOLD if in_hl else TEXT_GRAY
                f_weight = "bold" if in_hl else "normal"
                ax.text(mx,my,str(w),color=col, fontsize=max(5,8-n//20),ha="center",va="center",fontweight=f_weight, zorder=2)

    def _draw_directed_edges(self, ax, dir_edges, pos, highlight_path=None, show_w=True, n=10, flow_mat=None, cap_orig=None):
        """Directed edge drawing with label placed exactly on the arc midpoint."""
        all_x = [pos[i][0] for i in range(len(pos))]
        all_y = [pos[i][1] for i in range(len(pos))]
        margin = 60
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
        ax.set_aspect("equal", adjustable="datalim")
        node_r = max(12, 24 - n // 6)
        rad = 0.18  # arc curvature — must match arrowprops connectionstyle

        for u, v, w in dir_edges:
            in_path = highlight_path and (u, v) in highlight_path
            color   = ACCENT_RED if in_path else "#4A5568"
            lw      = 2.4 if in_path else 0.85
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            dx, dy  = x2 - x1, y2 - y1
            length  = math.hypot(dx, dy) or 1

            # Arrow start/end pulled back from node centres by node_r
            sx = x1 + dx / length * node_r
            sy = y1 + dy / length * node_r
            ex = x2 - dx / length * node_r
            ey = y2 - dy / length * node_r

            ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                        mutation_scale=12,
                                        connectionstyle=f"arc3,rad={rad}"),
                        zorder=2)

            if show_w:
                # ── Exact Bezier arc midpoint (t=0.5) ────────────────────────
                # matplotlib arc3 uses a quadratic Bezier whose control point is
                # offset perpendicularly from the chord midpoint by rad * chord/2.
                # We compute that same point here so the label sits ON the arc.

                # Chord vector from adjusted start to adjusted end
                cdx, cdy = ex - sx, ey - sy
                clen = math.hypot(cdx, cdy) or 1

                # Perpendicular unit vector (left-hand side of sx→ex direction)
                perp_x = -cdy / clen
                perp_y =  cdx / clen

                # Chord midpoint
                mx0 = (sx + ex) / 2
                my0 = (sy + ey) / 2

                # Control point (same formula matplotlib uses internally)
                ctrl_x = mx0 + perp_x * rad * clen / 2
                ctrl_y = my0 + perp_y * rad * clen / 2

                # Quadratic Bezier at t = 0.5  → this is the arc midpoint
                bx = 0.25 * sx + 0.5 * ctrl_x + 0.25 * ex
                by = 0.25 * sy + 0.5 * ctrl_y + 0.25 * ey

                # Tangent direction at t=0.5: derivative of B(t) = 2(1-t)(P1-P0)+2t(P2-P1)
                tan_x = (ctrl_x - sx) + (ex - ctrl_x)   # = ex - sx  (simplifies)
                tan_y = (ctrl_y - sy) + (ey - ctrl_y)
                tan_len = math.hypot(tan_x, tan_y) or 1
                # Normal to the tangent (left-hand perpendicular)
                norm_x = -tan_y / tan_len
                norm_y =  tan_x / tan_len

                # Nudge the label away from the arc line by a fixed pixel offset
                nudge = 9
                mx = bx + norm_x * nudge
                my = by + norm_y * nudge
                # ─────────────────────────────────────────────────────────────

                if flow_mat is not None and cap_orig is not None:
                    if flow_mat[u][v] > 0:
                        label = f"{flow_mat[u][v]}/{cap_orig[u][v]}"
                        fg = ACCENT_GOLD
                    else:
                        label = f"0/{cap_orig[u][v]}"
                        fg = TEXT_GRAY
                else:
                    label = str(w)
                    fg = TEXT_GRAY

                ax.text(mx, my, label, color=fg, fontsize=max(6, 8 - n // 20),
                        ha="center", va="center", zorder=3,
                        bbox=dict(boxstyle="round,pad=0.25", facecolor=BG_DARK,
                                  edgecolor=BORDER_COL, alpha=0.92, linewidth=0.5))

    def _open_welsh_powell(self):
        def run(ax,n,d,src,dst):
            adj,edges,graph=generate_undirected(n,d)
            pos=get_positions(n)
            sections,color,chromatic=DetailBuilder.welsh_powell(adj,n)
            self._last_sections=sections
            self._last_title="Welsh-Powell"
            import colorsys
            
            def _hex(ci, total):
                h = ci / max(total, 1)
                r,g,b = colorsys.hls_to_rgb(h, 0.60, 0.70)
                return "#{:02x}{:02x}{:02x}".format(int(r*255),int(g*255),int(b*255))
                
            palette_hex = [_hex(ci, chromatic) for ci in range(max(chromatic,1))]
            node_colors = [palette_hex[color[i]] for i in range(n)]
            
            for u,v,w in edges: 
                ax.plot([pos[u][0],pos[v][0]],[pos[u][1],pos[v][1]], color=BORDER_COL,lw=0.7,zorder=1)
                
            sz  = self._node_sz(n)
            fs  = self._font_sz(n)
            
            for i in range(n):
                ax.scatter(pos[i][0], pos[i][1], s=sz, c=node_colors[i], zorder=3, edgecolors=TEXT_WHITE, linewidths=0.9)
                if n <= 80: 
                    ax.text(pos[i][0], pos[i][1], node_name(i), color="white", fontsize=fs, ha="center", va="center", fontweight="bold", zorder=4)
                    
            for ci in range(min(chromatic, 10)): 
                ax.scatter([], [], c=palette_hex[ci], s=70, label=f"Channel C{ci+1}")
                
            ax.legend(loc="upper right", fontsize=7, facecolor=BG_PANEL, edgecolor=BORDER_COL, labelcolor=TEXT_WHITE, markerscale=0.9)
            return (f"OK  chi(G)={chromatic} colors | Vertices={n} | Edges={len(edges)} | Click 'View Detailed Calculations' for step-by-step")
        self._graph_screen("Welsh-Powell — Graph Coloring (RT Frequency Allocation)", run)

    def _open_kruskal(self):
        def run(ax,n,d,src,dst):
            adj,edges,graph=generate_undirected(n,d)
            pos=get_positions(n)
            sections,mst,total=DetailBuilder.kruskal(edges,n)
            self._last_sections=sections
            self._last_title="Kruskal"
            mst_set={(min(u,v),max(u,v)) for u,v,_ in mst}
            self._draw_undirected_edges(ax,edges,pos,highlight=mst_set, hl_col=ACCENT_GREEN,show_w=n<=40,n=n)
            self._draw_nodes(ax,n,pos)
            return (f"OK  MST cost={total} | {len(mst)} edges | Vertices={n} | Click 'View Detailed Calculations'")
        self._graph_screen("Kruskal — Minimum Spanning Tree (Network Backbone)", run)

    def _open_dijkstra(self):
        def run(ax,n,d,src,dst):
            adj,edges,graph=generate_undirected(n,d)
            pos=get_positions(n)
            s=min(src,n-1)
            dd=min(dst,n-1) if dst!=src else (src+1)%n
            sections,dist,prev,path=DetailBuilder.dijkstra(graph,n,s,dd)
            self._last_sections=sections
            self._last_title="Dijkstra"
            path_set={(min(a,b),max(a,b)) for a,b in zip(path[:-1],path[1:])}
            self._draw_undirected_edges(ax,edges,pos,highlight=path_set, hl_col=ACCENT_RED,show_w=n<=40,n=n)
            INF=float('inf')
            nc=[ACCENT_GREEN if i==s else ACCENT_RED if i==dd else "#FF8C00" if i in path else ACCENT_BLUE for i in range(n)]
            self._draw_nodes(ax,n,pos,node_colors=nc)
            
            if n<=55:
                for i in range(n):
                    dv=str(dist[i]) if dist[i]<INF else "inf"
                    ax.text(pos[i][0],pos[i][1]-max(14,22-n//8),f"d={dv}", color=ACCENT_GOLD,fontsize=max(4,7-n//18),ha="center")
                    
            cost=dist[dd] if dist[dd]<INF else "inf"
            return (f"OK  {node_name(s)}->{node_name(dd)}: cost={cost} | path={'->'.join(node_name(x) for x in path)} | Click 'View Detailed Calculations'")
        self._graph_screen("Dijkstra — Shortest Path (IP Routing)", run,show_src=True,show_dst=True)

    def _open_bellman_ford(self):
        def run(ax,n,d,src,dst):
            dir_edges,graph=generate_directed(n,d)
            pos=get_positions(n)
            s=min(src,n-1)
            sections,dist,prev,neg=DetailBuilder.bellman_ford(dir_edges,n,s)
            self._last_sections=sections
            self._last_title="Bellman-Ford"
            self._draw_directed_edges(ax,dir_edges,pos,show_w=n<=30,n=n)
            INF=float('inf')
            finite=[dd2 for dd2 in dist if dd2<INF]
            max_d=max(finite) if finite else 1
            cmap=plt.cm.YlOrRd
            nc=[cmap(dist[i]/max_d if dist[i]<INF else 1.0) for i in range(n)]
            self._draw_nodes(ax,n,pos,node_colors=nc)
            
            if n<=50:
                for i in range(n):
                    dv=str(dist[i]) if dist[i]<INF else "inf"
                    ax.text(pos[i][0],pos[i][1]-max(14,22-n//8),f"d={dv}", color=ACCENT_GOLD,fontsize=max(4,7-n//18),ha="center")
                    
            neg_txt="!! Negative cycle detected!" if neg else "OK  No negative cycle"
            return (f"{neg_txt} | Source={node_name(s)} | Directed graph | Vertices={n} | Click 'View Detailed Calculations'")
        self._graph_screen("Bellman-Ford — Directed Graph Routing & Cycle Detection", run,show_src=True)

    def _open_ford_fulkerson(self):
        def run(ax,n,d,src,dst):
            dir_edges,graph=generate_flow_network(n,d,max_w=50)
            pos=get_flow_positions(n)  # Using improved positioning function
            
            s_node=0
            t_node=n-1
            cap_orig=[[0]*n for _ in range(n)]
            
            for u,v,w in dir_edges: 
                cap_orig[u][v]+=w
                
            sections,max_flow,aug_paths,flow_mat=DetailBuilder.ford_fulkerson(cap_orig,n,s_node,t_node)
            self._last_sections=sections
            self._last_title="Ford-Fulkerson"
            
            # Draw edges with improved method
            self._draw_directed_edges(ax,dir_edges,pos,show_w=n<=25,n=n, 
                                      flow_mat=flow_mat,cap_orig=cap_orig)
            
            # Node colors and labels
            nc=[]
            labels=[]
            for i in range(n):
                if i==s_node:   
                    nc.append(ACCENT_RED)
                    labels.append("S")
                elif i==t_node: 
                    nc.append(ACCENT_GREEN)
                    labels.append("T")
                else:           
                    nc.append(ACCENT_BLUE)
                    labels.append(node_name(i))
                    
            self._draw_nodes(ax,n,pos,node_colors=nc,labels=labels)
            return (f"OK  Max flow S->T = {max_flow} | {len(aug_paths)} augmenting path(s) | "
                    f"Arc labels = flow/capacity | Click 'View Detailed Calculations'")
        self._graph_screen("Ford-Fulkerson — Maximum Flow (Data Network Capacity)", run)

    def _transport_screen(self, title, builder_fn):
        self._clear()
        outer=tk.Frame(self.content,bg=BG_DARK)
        outer.pack(fill=tk.BOTH,expand=True)
        tk.Label(outer,text=title,bg=BG_DARK,fg=TEXT_WHITE, font=("Segoe UI",12,"bold")).pack(anchor="w",pady=(0,6))
        
        ctrl=tk.Frame(outer,bg=BG_CARD,highlightthickness=1,highlightbackground=BORDER_COL)
        ctrl.pack(fill=tk.X,pady=(0,8))
        row=tk.Frame(ctrl,bg=BG_CARD)
        row.pack(fill=tk.X,padx=8,pady=8)
        
        def lbl(t): 
            tk.Label(row,text=t,bg=BG_CARD,fg=TEXT_GRAY, font=("Segoe UI",9)).pack(side=tk.LEFT,padx=(8,2))
            
        lbl("Sources (m):")
        m_var=tk.IntVar(value=3)
        tk.Spinbox(row,from_=2,to=8,textvariable=m_var,width=3, bg=BG_PANEL,fg=TEXT_WHITE,bd=0).pack(side=tk.LEFT)
        
        lbl("Destinations (n):")
        n_var=tk.IntVar(value=4)
        tk.Spinbox(row,from_=2,to=8,textvariable=n_var,width=3, bg=BG_PANEL,fg=TEXT_WHITE,bd=0).pack(side=tk.LEFT)
        
        res_frame=tk.Frame(outer,bg=BG_DARK)
        res_frame.pack(fill=tk.BOTH,expand=True)

        def run():
            m=m_var.get()
            n=n_var.get()
            total_s=random.randint(80,160)
            supply=[random.randint(8,50) for _ in range(m-1)]
            supply.append(max(total_s-sum(supply),5))
            demand=[random.randint(8,50) for _ in range(n-1)]
            demand.append(max(sum(supply)-sum(demand),5))
            cost=[[random.randint(1,20) for _ in range(n)] for _ in range(m)]
            
            sections,alloc,total=builder_fn(cost,supply,demand)
            self._last_sections=sections
            self._last_title=title
            
            for w2 in res_frame.winfo_children(): 
                w2.destroy()
                
            info=tk.Frame(res_frame,bg=BG_DARK)
            info.pack(pady=8,anchor="w",padx=8)
            tk.Label(info,text="Cost & Allocation Table  (green = allocated cell)", bg=BG_DARK,fg=ACCENT_GOLD, font=("Segoe UI",10,"bold")).grid(row=0,column=0,columnspan=n+2,pady=(0,6),sticky="w")
            
            for j in range(n):
                tk.Label(info,text=f"D{j+1}",bg=BG_CARD,fg=ACCENT_BLUE, font=("Segoe UI",9,"bold"),width=12,padx=4).grid(row=1,column=j+1,padx=1,pady=1)
                
            tk.Label(info,text="Supply",bg=BG_CARD,fg=TEXT_GRAY, font=("Segoe UI",9,"bold"),width=7).grid(row=1,column=n+1,padx=1,pady=1)
            
            for i in range(m):
                tk.Label(info,text=f"S{i+1}",bg=BG_CARD,fg=ACCENT_BLUE, font=("Segoe UI",9,"bold"),width=5,padx=4).grid(row=i+2,column=0,padx=1,pady=1)
                for j in range(n):
                    bg2="#1a472a" if alloc[i][j]>0 else BG_PANEL
                    fg2="#69ff47" if alloc[i][j]>0 else TEXT_GRAY
                    tk.Label(info,text=f"c={cost[i][j]}\nx={alloc[i][j]}", bg=bg2,fg=fg2,font=("Consolas",8), width=12,padx=4,pady=3).grid(row=i+2,column=j+1,padx=1,pady=1)
                tk.Label(info,text=str(supply[i]),bg=BG_CARD,fg=TEXT_GRAY, font=("Segoe UI",9),width=7).grid(row=i+2,column=n+1,padx=1,pady=1)
                
            tk.Label(info,text="Demand",bg=BG_CARD,fg=TEXT_GRAY, font=("Segoe UI",9,"bold")).grid(row=m+2,column=0,padx=1,pady=1)
            
            for j in range(n): 
                tk.Label(info,text=str(demand[j]),bg=BG_CARD,fg=TEXT_GRAY, font=("Segoe UI",9)).grid(row=m+2,column=j+1,padx=1,pady=1)
                
            tk.Label(res_frame, text=f"OK   Total Cost = {total}  | Click 'View Detailed Calculations'", bg=BG_DARK,fg=ACCENT_GREEN, font=("Segoe UI",10,"bold")).pack(pady=8,anchor="w",padx=8)

        btn_row=tk.Frame(ctrl,bg=BG_CARD)
        btn_row.pack(fill=tk.X,padx=8,pady=(0,8))
        tk.Button(btn_row,text=">  Generate & Solve", bg=ACCENT_BLUE,fg="white",bd=0,padx=12,pady=5, cursor="hand2",font=("Segoe UI",10,"bold"), command=run).pack(side=tk.LEFT,padx=(0,6))
        self._popup_btn(btn_row)
        run()

    def _open_nord_ouest(self):
        self._transport_screen("North-West Corner — Initial Transportation Solution", lambda cost,s,d: DetailBuilder.north_west(cost,s,d))

    def _open_moindre_cout(self):
        self._transport_screen("Least Cost — Optimized Initial Transportation Solution", lambda cost,s,d: DetailBuilder.least_cost(cost,s,d))

    # ══════════════════════════════════════════════════════════════════
    #   SIMPLEX
    # ══════════════════════════════════════════════════════════════════
    def _open_simplexe(self):
        self._clear()
        outer = tk.Frame(self.content, bg=BG_DARK)
        outer.pack(fill=tk.BOTH, expand=True)

        tk.Label(outer, text="Simplex — Maximisation with 2 Variables (B/R Basis Method)",
                 bg=BG_DARK, fg=TEXT_WHITE, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 4))

        coef_f = tk.Frame(outer, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COL)
        coef_f.pack(fill=tk.X, pady=(0, 6))

        tk.Label(coef_f, text="  Problem parameters  (x1 and x2 are fixed)",
                 bg=BG_CARD, fg=ACCENT_GOLD, font=("Consolas", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 2))

        def _entry(parent, width=5, default=""):
            e = tk.Entry(parent, width=width, bg=BG_PANEL, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, bd=1,
                         relief="flat", font=("Consolas", 10, "bold"), justify="center")
            e.insert(0, default)
            return e

        row1 = tk.Frame(coef_f, bg=BG_CARD)
        row1.pack(anchor="w", padx=14, pady=3)
        tk.Label(row1, text="Z_max =", bg=BG_CARD, fg=TEXT_WHITE, font=("Consolas", 10, "bold")).pack(side=tk.LEFT)
        A_e = _entry(row1, 4, "5")
        A_e.pack(side=tk.LEFT, padx=2)
        tk.Label(row1, text="· x1  +", bg=BG_CARD, fg=TEXT_GRAY, font=("Consolas", 10)).pack(side=tk.LEFT)
        B_e = _entry(row1, 4, "4")
        B_e.pack(side=tk.LEFT, padx=2)
        tk.Label(row1, text="· x2", bg=BG_CARD, fg=TEXT_GRAY, font=("Consolas", 10)).pack(side=tk.LEFT)

        row2 = tk.Frame(coef_f, bg=BG_CARD)
        row2.pack(anchor="w", padx=14, pady=3)
        tk.Label(row2, text="C1 :", bg=BG_CARD, fg=TEXT_GRAY, font=("Consolas", 10)).pack(side=tk.LEFT, padx=(0, 4))
        a1_e = _entry(row2, 4, "6")
        a1_e.pack(side=tk.LEFT, padx=2)
        tk.Label(row2, text="· x1  +", bg=BG_CARD, fg=TEXT_GRAY, font=("Consolas", 10)).pack(side=tk.LEFT)
        b1_e = _entry(row2, 4, "4")
        b1_e.pack(side=tk.LEFT, padx=2)
        tk.Label(row2, text="· x2  ≤", bg=BG_CARD, fg=TEXT_GRAY, font=("Consolas", 10)).pack(side=tk.LEFT)
        c1_e = _entry(row2, 5, "24")
        c1_e.pack(side=tk.LEFT, padx=2)

        row3 = tk.Frame(coef_f, bg=BG_CARD)
        row3.pack(anchor="w", padx=14, pady=3)
        tk.Label(row3, text="C2 :", bg=BG_CARD, fg=TEXT_GRAY, font=("Consolas", 10)).pack(side=tk.LEFT, padx=(0, 4))
        a2_e = _entry(row3, 4, "1")
        a2_e.pack(side=tk.LEFT, padx=2)
        tk.Label(row3, text="· x1  +", bg=BG_CARD, fg=TEXT_GRAY, font=("Consolas", 10)).pack(side=tk.LEFT)
        b2_e = _entry(row3, 4, "2")
        b2_e.pack(side=tk.LEFT, padx=2)
        tk.Label(row3, text="· x2  ≤", bg=BG_CARD, fg=TEXT_GRAY, font=("Consolas", 10)).pack(side=tk.LEFT)
        c2_e = _entry(row3, 5, "6")
        c2_e.pack(side=tk.LEFT, padx=2)
        
        tk.Label(coef_f, text="  x1, x2 ≥ 0", bg=BG_CARD, fg=TEXT_GRAY, font=("Consolas", 9)).pack(anchor="w", padx=14, pady=(0, 6))

        res_canvas = tk.Canvas(outer, bg=BG_DARK, bd=0, highlightthickness=0)
        vbar = ttk.Scrollbar(outer, orient="vertical", command=res_canvas.yview)
        res_canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        res_canvas.pack(fill=tk.BOTH, expand=True)
        
        res_inner = tk.Frame(res_canvas, bg=BG_DARK)
        res_wid = res_canvas.create_window((0, 0), window=res_inner, anchor="nw")
        
        res_canvas.bind("<Configure>", lambda e: res_canvas.itemconfig(res_wid, width=e.width))
        res_inner.bind("<Configure>", lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
        res_canvas.bind_all("<MouseWheel>", lambda e: res_canvas.yview_scroll(-1*(e.delta//120), "units"))

        COL_HEAD = "#1C2A3A"
        COL_PIVOT_COL = "#2d2200"
        COL_PIVOT_ROW = "#1e1035"
        COL_PIVOT_CELL = "#7a3800"

        def _clear_results():
            for w in res_inner.winfo_children(): 
                w.destroy()

        def _section_lbl(parent, text, color=ACCENT_GOLD):
            tk.Label(parent, text=text, bg=BG_DARK, fg=color, font=("Consolas", 10, "bold"), anchor="w").pack(fill=tk.X, padx=8, pady=(10, 2))

        def _draw_system(parent, A_val, B_val, a1_val, b1_val, c1_val, a2_val, b2_val, c2_val):
            f = tk.Frame(parent, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COL)
            f.pack(fill=tk.X, padx=8, pady=4)
            tk.Label(f, text="  Linear Programme — System", bg=BG_CARD, fg=ACCENT_GOLD, font=("Consolas", 9, "bold")).pack(anchor="w", padx=8, pady=(4, 0))
            
            lines = [
                f"  ⎧  Z_max  =  {A_val} x₁  +  {B_val} x₂",
                f"  ⎨  {a1_val} x₁  +  {b1_val} x₂  ≤  {c1_val}     (C1)",
                f"  ⎩  {a2_val} x₁  +  {b2_val} x₂  ≤  {c2_val}     (C2)",
                 "       x₁, x₂  ≥  0",
            ]
            
            for ln in lines: 
                tk.Label(f, text=ln, bg=BG_CARD, fg=TEXT_WHITE, font=("Consolas", 11), anchor="w").pack(fill=tk.X, padx=12, pady=1)
                
            tk.Label(f, text="", bg=BG_CARD).pack(pady=2)

        def _draw_simplex_table(parent, tab, basis, allvars, pivot_col=None, pivot_row=None, label="Tableau", min_R_col=None, max_xi_col=None):
            m = len(tab) - 1
            N = len(tab[0]) - 1
            outer_f = tk.Frame(parent, bg=BG_DARK)
            outer_f.pack(padx=8, pady=4, anchor="w")
            
            tk.Label(outer_f, text=f"  {label}", bg=BG_DARK, fg=ACCENT_GOLD, font=("Consolas", 9, "bold")).pack(anchor="w")

            legend_f = tk.Frame(outer_f, bg=BG_DARK)
            legend_f.pack(anchor="w")
            
            if max_xi_col is not None:
                tk.Label(legend_f, text=f"  ⬤ Circled column ({allvars[max_xi_col]}) = maximum xi → enters B", bg=BG_DARK, fg=ACCENT_GOLD, font=("Consolas", 8)).pack(anchor="w")
                
            if pivot_row is not None:
                tk.Label(legend_f, text=f"  ⬤ Circled row ({allvars[basis[pivot_row]]}) = minimum R → leaves B", bg=BG_DARK, fg="#C084FC", font=("Consolas", 8)).pack(anchor="w")

            tbl_f = tk.Frame(outer_f, bg=BG_DARK)
            tbl_f.pack(anchor="w")
            CW = 7
            
            def cell(row, col, text, bg, fg=TEXT_WHITE, bold=False, border_color=None):
                bd_w   = 2 if border_color else 0
                hl     = border_color or BG_DARK
                f2 = tk.Frame(tbl_f, bg=hl, padx=1, pady=1)
                f2.grid(row=row, column=col, padx=1, pady=1)
                tk.Label(f2, text=text, bg=bg, fg=fg, font=("Consolas", 9, "bold" if bold else "normal"), width=CW, anchor="center", padx=4, pady=3).pack()

            # Headers exactly matching photo
            cell(0, 0, "", COL_HEAD, ACCENT_GOLD, bold=True)
            for j in range(N):
                bg_h = COL_PIVOT_COL if j == max_xi_col else COL_HEAD
                fg_h = ACCENT_GOLD if j == max_xi_col else TEXT_GRAY
                cell(0, j+1, allvars[j], bg_h, fg_h, bold=(j == max_xi_col))
                
            cell(0, N+1, "B", COL_HEAD, TEXT_GRAY, bold=True)
            cell(0, N+2, "R", COL_HEAD, TEXT_GRAY, bold=True)

            for i in range(m):
                bv = allvars[basis[i]]
                is_pr = (i == pivot_row)
                row_bg = COL_PIVOT_ROW if is_pr else BG_PANEL
                row_fg = "#C084FC" if is_pr else TEXT_WHITE
                border = "#C084FC" if is_pr else None
                cell(i+1, 0, bv, row_bg, row_fg, bold=is_pr, border_color=border)
                
                for j in range(N):
                    is_pc = (j == max_xi_col)
                    is_pivot = is_pr and is_pc
                    
                    if is_pivot: 
                        bg2 = COL_PIVOT_CELL
                        fg2 = ACCENT_GOLD
                        bd2 = ACCENT_GOLD
                    elif is_pc: 
                        bg2 = COL_PIVOT_COL
                        fg2 = TEXT_WHITE
                        bd2 = None
                    elif is_pr: 
                        bg2 = COL_PIVOT_ROW
                        fg2 = "#C084FC"
                        bd2 = "#C084FC"
                    else: 
                        bg2 = BG_PANEL
                        fg2 = TEXT_WHITE
                        bd2 = None
                        
                    cell(i+1, j+1, f"{tab[i][j]:.3f}", bg2, fg2, bold=is_pivot, border_color=bd2)
                
                rhs_bg = COL_PIVOT_ROW if is_pr else BG_PANEL
                rhs_fg = "#C084FC" if is_pr else TEXT_WHITE
                cell(i+1, N+1, f"{tab[i][-1]:.3f}", rhs_bg, rhs_fg, bold=is_pr, border_color=border)
                
                if max_xi_col is not None and tab[i][max_xi_col] > 1e-9:
                    ratio = tab[i][-1] / tab[i][max_xi_col]
                    is_min = (i == pivot_row)
                    r_bg = "#1a472a" if is_min else BG_PANEL
                    r_fg = "#69ff47" if is_min else TEXT_GRAY
                    cell(i+1, N+2, f"{ratio:.3f}", r_bg, r_fg, bold=is_min, border_color="#28A745" if is_min else None)
                else:
                    cell(i+1, N+2, "—", BG_PANEL, TEXT_GRAY)

            z_i = m + 1
            cell(z_i, 0, "Z", COL_HEAD, ACCENT_BLUE, bold=True)
            for j in range(N):
                is_pc = (j == max_xi_col)
                bg2 = COL_PIVOT_COL if is_pc else BG_PANEL
                fg2 = ACCENT_GOLD if is_pc else (ACCENT_GREEN if tab[-1][j] <= 1e-9 else ACCENT_RED)
                cell(z_i, j+1, f"{tab[-1][j]:.3f}", bg2, fg2, bold=is_pc)
            
            # Negate RHS for correctly displaying Z value
            cell(z_i, N+1, f"{-tab[-1][-1]:.3f}", BG_PANEL, ACCENT_GOLD, bold=True)
            cell(z_i, N+2, "", BG_PANEL, TEXT_GRAY)

        def run():
            try:
                A_val  = float(A_e.get())
                B_val  = float(B_e.get())
                a1_val = float(a1_e.get())
                b1_val = float(b1_e.get())
                c1_val = float(c1_e.get())
                a2_val = float(a2_e.get())
                b2_val = float(b2_e.get())
                c2_val = float(c2_e.get())
            except ValueError:
                _clear_results()
                tk.Label(res_inner, text="!! Please enter valid numeric coefficients.", bg=BG_DARK, fg=ACCENT_RED, font=("Consolas", 10)).pack(padx=10, pady=10)
                return

            _clear_results()
            _draw_system(res_inner, A_val, B_val, a1_val, b1_val, c1_val, a2_val, b2_val, c2_val)

            allvars = ["x1", "x2", "e1", "e2"]
            n_vars = 2
            n_slack = 2
            N = 4
            c_obj = [A_val, B_val]

            # INITIAL TABLEAU — Z row initialized with positive coefficients (A, B)
            tab = [
                [a1_val, b1_val, 1.0, 0.0, c1_val],
                [a2_val, b2_val, 0.0, 1.0, c2_val],
                [A_val,  B_val,  0.0, 0.0, 0.0],
            ]
            m = 2
            basis = [2, 3]

            import copy
            _section_lbl(res_inner, "  ► Initialisation")
            
            # Entering variable logic for maximization with positive Cj - Zj
            pc_0 = max(range(N), key=lambda j: tab[2][j])
            
            if tab[2][pc_0] > 1e-9:
                entering_0 = pc_0
                ratios_0 = [(tab[i][-1]/tab[i][entering_0], i) for i in range(m) if tab[i][entering_0] > 1e-9]
                pivot_row_0 = min(ratios_0)[1] if ratios_0 else None
            else:
                entering_0 = None
                pivot_row_0 = None

            _draw_simplex_table(res_inner, copy.deepcopy(tab), list(basis), allvars,
                                pivot_col=pivot_row_0, pivot_row=pivot_row_0,
                                label="Initial Tableau", max_xi_col=entering_0, min_R_col=pivot_row_0)

            iteration = 0
            while iteration < 20:
                iteration += 1
                pc = max(range(N), key=lambda j: tab[2][j])
                if tab[2][pc] <= 1e-9: break

                entering_var = allvars[pc]
                ratios = [(tab[i][-1] / tab[i][pc], i) for i in range(m) if tab[i][pc] > 1e-9]
                
                if not ratios:
                    tk.Label(res_inner, text="  !! Problem is unbounded.", bg=BG_DARK, fg=ACCENT_RED, font=("Consolas", 10)).pack(anchor="w", padx=10)
                    return

                theta_min, pr = min(ratios)
                leaving_var = allvars[basis[pr]]

                tab_before = copy.deepcopy(tab)
                basis_before = list(basis)

                piv = tab[pr][pc]
                tab[pr] = [x / piv for x in tab[pr]]
                for i in range(m + 1):
                    if i != pr:
                        k = tab[i][pc]
                        tab[i] = [tab[i][c] - k * tab[pr][c] for c in range(N+1)]
                basis[pr] = pc

                tab_after = copy.deepcopy(tab)
                basis_after = list(basis)

                next_pc = max(range(N), key=lambda j: tab[2][j])
                if tab[2][next_pc] <= 1e-9: 
                    next_pc = None

                _section_lbl(res_inner, f"  ► Iteration {iteration}:  {leaving_var} leaves B  →  {entering_var} enters B", color="#7ECFFF")

                _draw_simplex_table(res_inner, tab_before, basis_before, allvars,
                                    pivot_col=pc, pivot_row=pr, label=f"Before actualisation", max_xi_col=pc, min_R_col=pr)

                ops_f = tk.Frame(res_inner, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COL)
                ops_f.pack(fill=tk.X, padx=8, pady=2)
                
                tk.Label(ops_f, text=f"  Row operations  (pivot element = {tab_before[pr][pc]:.4f}):", bg=BG_CARD, fg=ACCENT_GOLD, font=("Consolas", 9, "bold")).pack(anchor="w", padx=8, pady=3)
                piv_el = tab_before[pr][pc]
                
                tk.Label(ops_f, text=f"    {allvars[basis_before[pr]]}  ←  {allvars[basis_before[pr]]} / {piv_el:.4f}", bg=BG_CARD, fg=TEXT_WHITE, font=("Consolas", 9)).pack(anchor="w", padx=12)
                
                for i in range(m):
                    if i != pr:
                        k = tab_before[i][pc]
                        if abs(k) > 1e-12:
                            sign = "−" if k > 0 else "+"
                            tk.Label(ops_f, text=f"    {allvars[basis_before[i]]}  ←  {allvars[basis_before[i]]} {sign} {abs(k):.4f} × {entering_var}", bg=BG_CARD, fg=TEXT_WHITE, font=("Consolas", 9)).pack(anchor="w", padx=12)
                            
                k_z = tab_before[2][pc]
                if abs(k_z) > 1e-12:
                    sign = "−" if k_z > 0 else "+"
                    tk.Label(ops_f, text=f"    Z  ←  Z {sign} {abs(k_z):.4f} × {entering_var}", bg=BG_CARD, fg="#7ECFFF", font=("Consolas", 9)).pack(anchor="w", padx=12)
                    
                tk.Label(ops_f, text="", bg=BG_CARD).pack(pady=1)

                _draw_simplex_table(res_inner, tab_after, basis_after, allvars,
                                    pivot_col=None, pivot_row=None, label=f"After actualisation", max_xi_col=next_pc, min_R_col=None)

            x1_val = x2_val = 0.0
            for j in range(n_vars):
                col = [tab[i][j] for i in range(m)]
                if col.count(1) == 1 and col.count(0) == m - 1:
                    if j == 0: x1_val = tab[col.index(1)][-1]
                    if j == 1: x2_val = tab[col.index(1)][-1]
                    
            z_opt = -tab[2][-1]

            res_f = tk.Frame(res_inner, bg="#0d2b1e", highlightthickness=2, highlightbackground=ACCENT_GREEN)
            res_f.pack(fill=tk.X, padx=8, pady=8)
            
            tk.Label(res_f, text=f"  ✔  OPTIMAL SOLUTION FOUND", bg="#0d2b1e", fg=ACCENT_GREEN, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
            tk.Label(res_f, text=(f"  ⎧  Z* =  {z_opt:.4f}\n  ⎨  x1  =  {x1_val:.4f}\n  ⎩  x2  =  {x2_val:.4f}"), bg="#0d2b1e", fg=TEXT_WHITE, font=("Consolas", 12, "bold"), justify=tk.LEFT).pack(anchor="w", padx=20, pady=(2, 8))
            tk.Label(res_f, text="  All Z-row coefficients ≤ 0  →  no further improvement possible.", bg="#0d2b1e", fg=TEXT_GRAY, font=("Consolas", 9)).pack(anchor="w", padx=12, pady=(0, 8))

        btn_row = tk.Frame(coef_f, bg=BG_CARD)
        btn_row.pack(anchor="w", padx=10, pady=(4, 8))
        tk.Button(btn_row, text=">  Solve Simplex", bg=ACCENT_BLUE, fg="white", bd=0, padx=14, pady=5, cursor="hand2", font=("Segoe UI", 10, "bold"), command=run).pack(side=tk.LEFT)
        run()

# ══════════════════════════════════════════════════════════════════════════
#   APPLICATION
# ══════════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Operational Research — Networks & Telecom | Ilyas BOUJAY | EMI 2026")
        try:    
            self.state("zoomed")
        except: 
            self.attributes("-zoomed", True)
        self.configure(bg="white")
        self.resizable(True, True)
        self._page=None
        self._show_welcome()

    def _show_welcome(self):
        if self._page: self._page.destroy()
        self._page=WelcomePage(self,on_start=self._launch)

    def _launch(self):
        if self._page: self._page.destroy()
        self._page=MainPage(self)

if __name__=="__main__":
    App().mainloop()