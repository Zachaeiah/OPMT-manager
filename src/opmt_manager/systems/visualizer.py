import os
import shutil
from graphviz import Digraph
from opmt_manager.domain import Operation, Task
from opmt_manager.systems.scheduler import Scheduler
from opmt_manager.Graphs.graph import Graph


def _check_graphviz() -> bool:
    if not shutil.which("dot"):
        raise RuntimeError(
            "Graphviz is not installed or not in PATH.\n"
            "Install it from https://graphviz.org/download/"
        )
    return True

# -------------------------
# NODE RENDERER
# -------------------------
class DefaultNodeRenderer:
    def __init__(self, config):
        self.config: dict = config

    def render(self, node: Task, t: dict) -> str:
        if t is None:
            return node.name

        slack: float = t["LS"] - t["ES"]

        color: str = (
            self.config["color_critical"]
            if slack <= 0
            else self.config["color_normal"]
        )

        return f"""<
        <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" BGCOLOR="{color}">
            <TR>
                <TD>{round(t["ES"],1)}</TD>
                <TD></TD>
                <TD>{round(t["EF"],1)}</TD>
            </TR>
            <TR>
                <TD COLSPAN="3">{node.name}</TD>
            </TR>
            <TR>
                <TD COLSPAN="3">{round(node.duration,1)}</TD>
            </TR>
            <TR>
                <TD>{round(t["LS"],1)}</TD>
                <TD>{round(slack,1)}</TD>
                <TD>{round(t["LF"],1)}</TD>
            </TR>
        </TABLE>>"""

# -------------------------
# GRAPH VISUALIZER
# -------------------------
class GraphVisualizer:
    def __init__(
        self,
        scheduler,            # <-- now takes Scheduler
        output_dir=None,
        config=None
    ):
        if not _check_graphviz():
            raise RuntimeError("Graphviz is required for visualization.")

        self.scheduler: Scheduler = scheduler
        self.operation: Operation = scheduler.operation
        self.graph: Graph = scheduler.graph

        # -------------------------
        # OUTPUT DIR (CWD based)
        # -------------------------
        self.output_dir: str = (
            os.path.abspath(output_dir)
            if output_dir
            else os.path.join(os.getcwd(), "diagram_renders")
        )
        os.makedirs(self.output_dir, exist_ok=True)

        # -------------------------
        # CONFIG
        # -------------------------
        self.config = {
            "skip_start_end": True,
            "show_metrics": True,
            "color_critical": "lightblue",
            "color_normal": "lightgreen",

            "graph": {
                "rankdir": "LR",
                "dpi": "300",
                "size": "12,12",
                "nodesep": "0.5",
                "ranksep": "0.75",
            },
            "node": {
                "shape": "box",
                "fontname": "Arial",
                "fontsize": "12",
            },
            "edge": {
                "color": "black",
            },

            "format": "png",
        }

        if config:
            self._deep_update(self.config, config)

        self.node_renderer: DefaultNodeRenderer = DefaultNodeRenderer({
            "color_critical": self.config["color_critical"],
            "color_normal": self.config["color_normal"]
        })

    # -------------------------
    def draw(self, filename="operation_diagram"):
        dot: Digraph = Digraph(comment="Operation Diagram", engine="dot")
        dot.attr(**self.config.get("graph", {}))

        self._add_nodes(dot)
        self._add_edges(dot)

        if self.config["show_metrics"]:
            self._add_metrics(dot)

        return self._save(dot, filename)

    # -------------------------
    def _get_timing(self, node):
        # scheduler already pushed timing onto node
        return self.operation.get_times(node.id)

    def _add_nodes(self, dot):
        for node_id, node in self.graph.node_items():
            if self._skip_node(node_id):
                continue

            timing: dict = self._get_timing(node)
            label: str = self.node_renderer.render(node, timing)

            dot.node(node_id, label, **self.config.get("node", {}))

    def _add_edges(self, dot):
        for a_id, b_id in self.graph.edges():
            if self._skip_node(a_id) or self._skip_node(b_id):
                continue

            is_critical: bool = (
                self.scheduler.is_critical(a_id)
                and self.scheduler.is_critical(b_id)
            )

            edge_cfg: dict = dict(self.config.get("edge", {}))
            if is_critical:
                edge_cfg["color"] = "red"

            dot.edge(a_id, b_id, **edge_cfg)

    def _add_metrics(self, dot):
        cycle_time: float = self.scheduler.get_cycle_time()
        efficiency: float = self.scheduler.get_process_efficiency()

        label = f"""<
        <TABLE BORDER="0">
            <TR><TD>Cycle Time:</TD><TD>{round(cycle_time,2)}</TD></TR>
            <TR><TD>Efficiency:</TD><TD>{round(100*efficiency,1)}%</TD></TR>
        </TABLE>
        >"""

        dot.attr(label=label)

    # -------------------------
    def _skip_node(self, node_id):
        if not self.config["skip_start_end"]:
            return False
        return node_id in (self.operation.start.id, self.operation.end.id)

    def _deep_update(self, base, new):
        for k, v in new.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def _save(self, dot, filename):
        path: str = os.path.join(self.output_dir, filename)
        fmt: str = self.config.get("format", "png")

        dot.render(path, format=fmt, cleanup=True)

        print(f"Diagram saved: {path}.{fmt}")
        return path