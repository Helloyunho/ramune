from discord import Attachment, Embed
import discord.http
import mimetypes


class Media:
    content_type: str | None
    filename: str | None
    size: int | None
    url: str
    _http: discord.http.HTTPClient

    def __init__(self, http: discord.http.HTTPClient, base: Attachment | Embed | Media):
        self._http = http
        if isinstance(base, Attachment):
            self.content_type = base.content_type
            self.filename = base.filename
            self.size = base.size
            self.url = base.url
        elif isinstance(base, Media):
            self.content_type = base.content_type
            self.filename = base.filename
            self.size = base.size
            self.url = base.url
        elif isinstance(base, Embed):
            if base.type == "image" and base.image and base.image.proxy_url:
                self.content_type = mimetypes.guess_type(base.image.proxy_url)[0]
                self.filename = base.image.proxy_url.split("/")[-1]
                self.size = None
                self.url = base.image.proxy_url
            elif base.type in ["video", "gifv"] and base.video and base.video.proxy_url:
                self.content_type = mimetypes.guess_type(base.video.proxy_url)[0]
                self.filename = base.video.proxy_url.split("/")[-1]
                self.size = None
                self.url = base.video.proxy_url
            else:
                raise ValueError("Embed does not contain a valid media type.")
        else:
            raise TypeError("Unsupported type for Media initialization.")

    async def read(self) -> bytes:
        url = self.url
        data = await self._http.get_from_cdn(url)
        return data
