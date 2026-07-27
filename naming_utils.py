from pathlib import PurePosixPath
from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunsplit


def filename_from_url(url: str, default: str = "download.xlsx") -> str:
    """Use Thorlabs' own filename for the xlsx (e.g. a_broadband_ar-coating.xlsx)
    instead of inventing a label, so downloaded files keep their default name."""
    name = PurePosixPath(urlparse(url).path).name
    return name or default


def with_graphs_tab(url: str, base_url: str = "https://www.thorlabs.com") -> str:
    """Merge tabName=Graphs into a Thorlabs product/family URL. The raw-data
    xlsx download links only render on that tab, the default Overview tab
    (or a bare pn= product-family link) has none."""
    if not url.startswith("http"):
        url = f"{base_url}{url}"

    parts = urlsplit(url)
    query_pairs = dict(parse_qsl(parts.query))
    query_pairs["tabName"] = "Graphs"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment))
