import httpx
from selectolax.lexbor import LexborHTMLParser
from typing import TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from selectolax.lexbor import LexborNode


class FirmwareInfo(TypedDict):
    version: str
    details: str


URL = "https://www.playstation.com/en-us/support/hardware/{model}/system-software-info/"
client = httpx.AsyncClient(timeout=10.0)


async def fetch_ps4_html() -> LexborHTMLParser:
    response = await client.get(URL.format(model="ps4"))
    response.raise_for_status()
    return LexborHTMLParser(response.text)


async def fetch_ps5_html() -> LexborHTMLParser:
    response = await client.get(URL.format(model="ps5"))
    response.raise_for_status()
    return LexborHTMLParser(response.text)


def make_markdown_from_list(node: "LexborNode") -> str:
    markdown = ""
    for child in node.iter():
        if child.tag == "li":
            markdown += "- "
            for li_child in child.iter(include_text=True):
                if li_child.tag == "strong":
                    markdown += f"**{li_child.text()}**"
                elif li_child.tag == "ul":
                    markdown = markdown[:-2] + "\n  "
                    markdown += "  ".join(
                        make_markdown_from_list(li_child).splitlines()
                    )
                elif li_child.is_text_node:
                    markdown += li_child.text()
            markdown += "\n"
    return markdown


async def parse_html(html: LexborHTMLParser) -> FirmwareInfo:
    nodes = list(
        html.css_first(
            "#gdk__content > div > div > div > div > div:nth-child(2) > section > div > div > div > div > div.body-text-block.txt-block-paragraph > div > div"
        ).iter()
    )
    version = nodes[0].text().strip()[len("Version: ") :]
    # recursively get unordered list text and convert it to markdown
    details = make_markdown_from_list(nodes[1])
    return {"version": version, "details": details}
