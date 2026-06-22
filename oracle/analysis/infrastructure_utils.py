"""Infrastructure utilities: numba, mpmath, polars, plotly, graphviz, svgwrite, timezonefinder, emoji."""
import logging
import time

logger = logging.getLogger(__name__)

# Lazy imports for infrastructure
_numba = None
_mpmath = None
_polars = None
_plotly = None
_graphviz = None
_svgwrite = None
_timezonefinder = None
_emoji = None


def get_numba():
    global _numba
    if _numba is None:
        try:
            import numba
            _numba = numba
        except ImportError:
            pass
    return _numba


def get_mpmath():
    global _mpmath
    if _mpmath is None:
        try:
            import mpmath
            _mpmath = mpmath
        except ImportError:
            pass
    return _mpmath


def get_polars():
    global _polars
    if _polars is None:
        try:
            import polars
            _polars = polars
        except ImportError:
            pass
    return _polars


def get_plotly():
    global _plotly
    if _plotly is None:
        try:
            import plotly
            _plotly = plotly
        except ImportError:
            pass
    return _plotly


def get_graphviz():
    global _graphviz
    if _graphviz is None:
        try:
            import graphviz
            _graphviz = graphviz
        except ImportError:
            pass
    return _graphviz


def get_svgwrite():
    global _svgwrite
    if _svgwrite is None:
        try:
            import svgwrite
            _svgwrite = svgwrite
        except ImportError:
            pass
    return _svgwrite


def get_timezonefinder():
    global _timezonefinder
    if _timezonefinder is None:
        try:
            from timezonefinder import TimezoneFinder
            _timezonefinder = TimezoneFinder()
        except ImportError:
            pass
    return _timezonefinder


def get_emoji():
    global _emoji
    if _emoji is None:
        try:
            import emoji
            _emoji = emoji
        except ImportError:
            pass
    return _emoji


class InfrastructureUtilities:
    """Centralized access to infrastructure libraries."""

    @staticmethod
    def fast_jit(func):
        """Compile function with numba JIT."""
        nb = get_numba()
        if nb:
            return nb.jit(func)
        return func

    @staticmethod
    def precise_calc(expression: str, precision: int = 50) -> str:
        """Evaluate expression with mpmath precision."""
        mp = get_mpmath()
        if mp:
            mp.mp.dps = precision
            return str(mp.eval(expression))
        return str(eval(expression))

    @staticmethod
    def dataframe_operation(data: dict, operation: str = "sort") -> dict:
        """Perform polars DataFrame operations."""
        pl = get_polars()
        if pl:
            df = pl.DataFrame(data)
            if operation == "sort":
                return df.sort(df.columns[0]).to_dict(as_series=False)
            elif operation == "filter":
                return df.head(100).to_dict(as_series=False)
        return data

    @staticmethod
    def create_chart(data: dict, chart_type: str = "scatter") -> dict:
        """Create plotly chart specification."""
        pio = get_plotly()
        if pio and pio.graph_objects:
            import plotly.graph_objects as go
            if chart_type == "scatter":
                fig = go.Scatter(x=data.get("x", []), y=data.get("y", []), mode="markers")
                return {"data": fig.to_plotly_json(), "type": "scatter"}
        return {"error": "plotly not available"}

    @staticmethod
    def render_graph(nodes: list, edges: list, name: str = "graph") -> str:
        """Render graph with graphviz."""
        gv = get_graphviz()
        if gv:
            dot = gv.Digraph(name=name)
            for n in nodes:
                dot.node(str(n))
            for e in edges:
                dot.edge(str(e[0]), str(e[1]))
            return dot.source
        return ""

    @staticmethod
    def create_svg(filename: str, width: int = 800, height: int = 600) -> object:
        """Create SVG drawing."""
        sw = get_svgwrite()
        if sw:
            return sw.Drawing(filename, size=(width, height))
        return None

    @staticmethod
    def find_timezone(lat: float, lon: float) -> str:
        """Find timezone from coordinates."""
        tf = get_timezonefinder()
        if tf:
            return tf.timezone_at(lat=lat, lng=lon) or "UTC"
        return "UTC"

    @staticmethod
    def process_emoji(text: str) -> dict:
        """Extract and analyze emoji from text."""
        em = get_emoji()
        if em:
            emoji_list = [c for c in text if c in em.EMOJI_DATA]
            return {
                "emoji_count": len(emoji_list),
                "emojis": emoji_list,
                "text_without_emoji": em.replace_emoji(text, replace=""),
            }
        return {"emoji_count": 0, "emojis": [], "text_without_emoji": text}


def get_infrastructure_stats() -> dict:
    """Return availability status of all infrastructure libraries."""
    return {
        "numba": get_numba() is not None,
        "mpmath": get_mpmath() is not None,
        "polars": get_polars() is not None,
        "plotly": get_plotly() is not None,
        "graphviz": get_graphviz() is not None,
        "svgwrite": get_svgwrite() is not None,
        "timezonefinder": get_timezonefinder() is not None,
        "emoji": get_emoji() is not None,
    }
