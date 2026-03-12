import mpv


class VideoPlayer:
    def __init__(self, locations):
        self.locations = locations
        self.plr = mpv.MPV(config="yes", input_default_bindings=True,
                           input_vo_keyboard=True, osc=True)

        self.introPos = None
        self.outroPos = None

    def skipIntroOutro(self, _name, val):
        try:
            if val is None:
                return

            introStart, introEnd = float(self.introPos[0]), float(self.introPos[1])
            outroStart, outroEnd = float(self.outroPos[0]), float(self.outroPos[1])

            if introStart <= val <= introEnd:
                diff = introEnd - val
                self.plr.seek(diff)

            if outroStart <= val <= outroEnd:
                diff = outroEnd - val
                self.plr.seek(diff)

        except Exception as e:
            print(f"Error setting up skipping intro/outro\n{e}")
            self.plr.unobserve_property("time-pos", self.skipIntroOutro)
            return 0

    def play(self, useSub, intro, outro, skipIntroOutro):
        videoPath = str(self.locations["video"])
        subPath = str(self.locations["sub"]) if useSub else ''

        self.introPos = intro.strip("()").split(",")
        self.outroPos = outro.strip("()").split(',')

        if skipIntroOutro:
            self.plr.observe_property("time-pos", self.skipIntroOutro)

        self.plr.fullscreen = True
        self.plr.loadfile(videoPath, sub_file=subPath)
        self.plr.wait_for_playback()
        self.plr.terminate()
