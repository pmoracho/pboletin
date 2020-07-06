from configparser import ConfigParser
import numpy as np


class Config:

    def __init__(self, file=None):

        self.file = file
        self.config = ConfigParser()
        if self.file:
            self._load()

    def set_file(self, file):

        self.file = file
        if self.file:
            self._load()

    def _load(self):
        self.config.read(self.file)
        self.__dict__.update(dict(self.config.items("GLOBAL")))

        # lista
        for e in ["imgext"]:
            self.__dict__[e] = self.__dict__[e].split(',')

        # lista in
        for e in ["remove_pixels"]:
            self.__dict__[e] = list(map(int, self.__dict__[e].split(',')))

        # np.array
        for e in ["linecolor_from", "linecolor_to"]:
            self.__dict__[e] = np.array(list(map(int, self.__dict__[e].split(','))))

        # floatr
        for e in ["line_rho"]:
            self.__dict__[e] = float(self.__dict__[e])

        # int
        for e in ["resolution", "artifact_min_size",
                  "ignore_first_pages", "ignore_last_pages",
                  "max_area", "min_area", "jpg_compression", "h_line_gap", "v_line_gap", "line_min_length",
                  "line_max_gap", "line_thres", "theta"]:
            self.__dict__[e] = int(self.__dict__[e])

        # booleano
        for e in ["save_process_files", "export_logos"]:
            self.__dict__[e] = True if self.__dict__[e] == "True" else False

        self.compensation = self.resolution/300

    def __str__(self):

        parametros = (
            "line_min_length              : {0}".format(int(self.line_min_length*self.compensation)),
            "line_max_gap                 : {0}".format(int(self.line_max_gap*self.compensation)),
            "theta                        : {0}".format(int(self.theta)),
            "line_thres                   : {0}".format(int(self.line_thres*self.compensation)),
            "line_rho                     : {0}".format(self.line_rho),
            "resolution                   : {0}".format(self.resolution)
            )

        return "\n".join(parametros)
