# blockchain_pyqt.py (updated with trails + flash)
import sys
import random
import time
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QTextEdit, QSlider, QDialog
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx

# ---------------- Utilities / Blockchain primitives ----------------
def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

@dataclass
class Block:
    index: int
    prev_hash: str
    data: str
    nonce: int = 0
    timestamp: float = field(default_factory=time.time)

    def compute_hash(self) -> str:
        return sha256(f"{self.index}{self.prev_hash}{self.data}{self.nonce}{self.timestamp}")

    @property
    def hash(self) -> str:
        return self.compute_hash()

class Blockchain:
    def __init__(self, difficulty_prefix: str = "00"):
        self.chain: List[Block] = [self._create_genesis()]
        self.difficulty_prefix = difficulty_prefix

    def _create_genesis(self) -> Block:
        return Block(0, "0", "genesis", nonce=0, timestamp=time.time())

    def last_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, block: Block) -> bool:
        if block.prev_hash != self.last_block().hash:
            return False
        if not block.hash.startswith(self.difficulty_prefix):
            return False
        self.chain.append(block)
        return True

    def mine_block(self, miner_id: str, data: str = "") -> Block:
        index = self.last_block().index + 1
        prev_hash = self.last_block().hash
        nonce = 0
        while True:
            blk = Block(index=index, prev_hash=prev_hash, data=f"{data}|by:{miner_id}", nonce=nonce)
            if blk.hash.startswith(self.difficulty_prefix):
                return blk
            nonce += 1

# ---------------- Network / Node simulation ----------------
@dataclass
class Node:
    node_id: int
    neighbors: List[int] = field(default_factory=list)
    blockchain: Blockchain = field(default_factory=lambda: Blockchain("00"))

    def receive_block(self, block: Block):
        self.blockchain.add_block(block)

class NetworkSimulator:
    def __init__(self, node_count: int = 6, connectivity: float = 0.5, difficulty_prefix: str = "00"):
        self.nodes: Dict[int, Node] = {}
        self.events: List[Tuple[int, int, Block]] = []
        for i in range(node_count):
            self.nodes[i] = Node(node_id=i, neighbors=[], blockchain=Blockchain(difficulty_prefix))
        for i in range(node_count):
            for j in range(i + 1, node_count):
                if random.random() < connectivity:
                    self.nodes[i].neighbors.append(j)
                    self.nodes[j].neighbors.append(i)

    def broadcast(self, src: int, block: Block, current_step: int, max_delay: int = 3):
        for nb in self.nodes[src].neighbors:
            delay = random.randint(1, max_delay)
            self.events.append((current_step + delay, nb, block))

    def step(self, current_step: int, mining_chance: float = 0.3):
        ready = [e for e in self.events if e[0] == current_step]
        self.events = [e for e in self.events if e[0] != current_step]
        delivered = []
        for _, target, block in ready:
            self.nodes[target].receive_block(block)
            delivered.append((target, block))

        mined = []
        for nid, node in self.nodes.items():
            if random.random() < mining_chance:
                block = node.blockchain.mine_block(miner_id=str(nid), data=f"auto_step:{current_step}")
                node.blockchain.add_block(block)
                self.broadcast(nid, block, current_step)
                mined.append((nid, block))
        return mined, delivered

# ---------------- PyQt5 App ----------------
class BlockchainWindow(QWidget):
    def __init__(self, node_count=6, connectivity=0.6, difficulty="00"):
        super().__init__()
        random.seed(1)
        self.sim = NetworkSimulator(node_count=node_count, connectivity=connectivity, difficulty_prefix=difficulty)
        self.current_step = 0
        self.mining_chance = 0.35

        self.G = nx.Graph()
        for nid, node in self.sim.nodes.items():
            self.G.add_node(nid)
            for nb in node.neighbors:
                if not self.G.has_edge(nid, nb):
                    self.G.add_edge(nid, nb)
        self.pos = nx.spring_layout(self.G, seed=42)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvas(self.fig)

        self.active_messages: List[Tuple[int, int, Block, float]] = []
        self.trails: List[Tuple[float, float, float, str]] = []  # (x, y, alpha, label)
        self.flash_nodes: Dict[int, int] = {}  # node_id -> remaining frames

        self.running = True
        self.timer_interval = 800
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.timer_interval)

        self._build_ui()
        self._draw_frame()

    # ---- UI ----
    def _build_ui(self):
        self.setWindowTitle("Blockchain Network Simulator")
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Node ID:"))
        self.node_input = QLineEdit()
        self.node_input.setFixedWidth(50)
        controls.addWidget(self.node_input)
        controls.addWidget(QLabel("Data:"))
        self.data_input = QLineEdit()
        controls.addWidget(self.data_input)
        self.add_btn = QPushButton("Add Block")
        self.add_btn.clicked.connect(self.on_add_block)
        controls.addWidget(self.add_btn)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.on_toggle_pause)
        controls.addWidget(self.pause_btn)
        self.show_btn = QPushButton("Show Chain")
        self.show_btn.clicked.connect(self.on_show_chain)
        controls.addWidget(self.show_btn)
        layout.addLayout(controls)
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("Speed"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(2000)
        self.speed_slider.setValue(self.timer_interval)
        self.speed_slider.setTickInterval(100)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        bottom.addWidget(self.speed_slider)
        self.status_label = QLabel("Step: 0")
        bottom.addWidget(self.status_label)
        layout.addLayout(bottom)
        self.setLayout(layout)
        self.resize(1000, 700)

    # ---- UI Handlers ----
    def on_add_block(self):
        try:
            node_id = int(self.node_input.text().strip())
        except ValueError:
            self.status_label.setText("Invalid node id")
            return
        if node_id not in self.sim.nodes:
            self.status_label.setText("Node id out of range")
            return
        data = self.data_input.text().strip() or "manual"
        blk = self.sim.nodes[node_id].blockchain.mine_block(str(node_id), data)
        self.sim.nodes[node_id].blockchain.add_block(blk)
        self.sim.broadcast(node_id, blk, current_step=self.current_step)
        self.flash_nodes[node_id] = 3
        self.status_label.setText(f"Added manual block to node {node_id}")

    def on_toggle_pause(self):
        self.running = not self.running
        self.pause_btn.setText("Resume" if not self.running else "Pause")

    def on_show_chain(self):
        try:
            node_id = int(self.node_input.text().strip())
        except ValueError:
            self.status_label.setText("Invalid node id")
            return
        if node_id not in self.sim.nodes:
            self.status_label.setText("Node id out of range")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Blockchain of Node {node_id}")
        dlg.resize(700, 500)
        txt = QTextEdit(dlg)
        txt.setReadOnly(True)
        s = ""
        for block in self.sim.nodes[node_id].blockchain.chain:
            s += f"Index: {block.index}\nHash: {block.hash}\nPrev: {block.prev_hash}\nData: {block.data}\n"
            s += "-" * 60 + "\n"
        txt.setText(s)
        layout = QVBoxLayout()
        layout.addWidget(txt)
        dlg.setLayout(layout)
        dlg.exec_()

    def on_speed_changed(self, value: int):
        self.timer_interval = value
        self.timer.setInterval(self.timer_interval)
        self.status_label.setText(f"Speed: {self.timer_interval} ms — Step: {self.current_step}")

    # ---- Simulation tick ----
    def _tick(self):
        if not self.running:
            self._draw_frame()
            return
        mined, delivered = self.sim.step(self.current_step, mining_chance=self.mining_chance)
        for nid, blk in mined:
            for nb in self.sim.nodes[nid].neighbors:
                self.active_messages.append((nid, nb, blk, 0.0))
            self.flash_nodes[nid] = 3
        new_msgs = []
        prog_inc = 0.25
        for (src, dst, blk, prog) in self.active_messages:
            prog += prog_inc
            if prog >= 1.0:
                self.sim.nodes[dst].receive_block(blk)
                self.flash_nodes[dst] = 3
            else:
                new_msgs.append((src, dst, blk, prog))
        self.active_messages = new_msgs
        self.current_step += 1
        self.status_label.setText(f"Step: {self.current_step}")
        self._draw_frame()

    # ---- Drawing ----
    def _draw_frame(self):
        self.ax.clear()
        lengths = {nid: len(node.blockchain.chain) for nid, node in self.sim.nodes.items()}
        node_colors = []
        for nid in self.sim.nodes:
            if nid in self.flash_nodes:
                node_colors.append("limegreen")
                self.flash_nodes[nid] -= 1
                if self.flash_nodes[nid] <= 0:
                    del self.flash_nodes[nid]
            else:
                node_colors.append("skyblue")
        nx.draw(self.G, self.pos, ax=self.ax, with_labels=True,
                node_color=node_colors, node_size=900)
        labels = {nid: f"{nid}\nlen={lengths[nid]}" for nid in self.sim.nodes}
        nx.draw_networkx_labels(self.G, self.pos, labels=labels, ax=self.ax)

        # traveling messages + trails
        new_trails = []
        for (src, dst, blk, prog) in self.active_messages:
            x = self.pos[src][0] + prog * (self.pos[dst][0] - self.pos[src][0])
            y = self.pos[src][1] + prog * (self.pos[dst][1] - self.pos[src][1])
            color = "red"
            self.ax.plot(x, y, "o", markersize=8, color=color)
            self.ax.text(x, y + 0.02, str(blk.index), fontsize=7, ha="center", color=color)
            new_trails.append((x, y, 1.0, str(blk.index)))
        decayed_trails = []
        for (x, y, alpha, txt) in self.trails + new_trails:
            if alpha > 0.1:
                self.ax.plot(x, y, "o", markersize=4, color="red", alpha=alpha*0.6)
                self.ax.text(x, y + 0.015, txt, fontsize=6, ha="center", color="red", alpha=alpha*0.6)
                decayed_trails.append((x, y, alpha*0.8, txt))
        self.trails = decayed_trails

        text_y = 1.02
        for nid in self.sim.nodes:
            short_chain = [b.data for b in self.sim.nodes[nid].blockchain.chain]
            self.ax.text(1.02, text_y, f"Node {nid}: {short_chain}", transform=self.ax.transAxes,
                         fontsize=8, verticalalignment="top")
            text_y -= 0.06
        self.ax.set_title(f"Blockchain Network — Step {self.current_step}")
        self.ax.axis("off")
        self.canvas.draw()

# ---------------- Main ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BlockchainWindow(node_count=6, connectivity=0.6, difficulty="00")
    win.show()
    sys.exit(app.exec_())
