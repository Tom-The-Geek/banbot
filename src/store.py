import dataclasses
import json


@dataclasses.dataclass
class Link:
    channels: list[str]


class Store:
    def __init__(self, store_path: str):
        self._store_path = store_path
        self._links: list[Link] = []
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        self._loaded = True

        try:
            with open(self._store_path, "r") as f:
                self._links = []
                data = json.load(f)
                for link in map(lambda l: Link(l['channels']), data['links']):
                    self._links.append(link)
        except FileNotFoundError:
            self._save()

    def _save(self):
        if not self._loaded:
            print("[WARN] Trying to save Store before it has been loaded!")
            return
        with open(self._store_path, "w") as f:
            json.dump({
                "links": list(map(lambda l: l.__dict__, self._links)),
            }, f)

    def get_linked_channels(self, channel: str) -> list[str]:
        if not self._loaded:
            print("[WARN] Store has not been loaded yet!")
            return []

        for link in self._links:
            if channel in link.channels:
                copy = link.channels.copy()
                copy.remove(channel)
                return copy

        return []

    def link_channels(self, channel_a: str, channel_b: str):
        if not self._loaded:
            print("[WARN] Store has not been loaded yet!")
            return
        self._links.append(Link([channel_a, channel_b]))
        self._save()

    def unlink_channels(self, channel: str) -> bool:
        if not self._loaded:
            print("[WARN] Store has not been loaded yet!")
            return False

        to_remove: list[Link] = []
        removed = False
        for link in self._links:
            if channel in link.channels:
                link.channels.remove(channel)
                removed = True
                if len(link.channels) < 2:
                    to_remove.append(link)
        for link in to_remove:
            self._links.remove(link)
        self._save()
        return removed
