from ._apis import Globals, Default, Log


class YAPIEngine:
    def __init__(self, raw):
        self.string: Default.string = raw.string
        self.onClicked: Default.onClicked = raw.clicked
        self.LOG: Log = raw
        # ---
        self.globals: Globals = raw.API_G
