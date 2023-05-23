# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import time
import statistics

class Stats:
    def __init__(self, start_cell = 0, filename = ""):
        # raw
        self.k_depths = []
        self.errors = []
        self.fps = []
        self.cell_times = []
        self.phi_true = 0
        self.phi_false = 0
        self.total_prop = 0
        self.execute_time = 0

        #internals
        self.start_time = 0
        self.start_cell = start_cell
        self.filename = filename

    def log_fp(self, K):
        self.fps.append(K)

    def log_start(self):
        self.start_time = time.time()

    def log_phi(self, branch: bool):
        if branch:
            self.phi_true = self.phi_true + 1
        else:
            self.phi_false = self.phi_false + 1

    def log_end(self):
        self.execute_time =  time.time() - self.start_time 

    def log_error(self, K):
        self.errors.append(K)

    def get_row(self):
        t_extime = self.execute_time
        t_cell_extime_avg = statistics.mean(self.cell_times) if len(self.cell_times) > 0 else -1
        t_cell_extime_max = max(self.cell_times) if len(self.cell_times) > 0 else -1
        phi_rate = -1 if (self.phi_false + self.phi_true) == 0 else self.phi_true / (self.phi_false + self.phi_true)
        min_fps = min(self.fps) if len(self.fps) > 0 else -1
        max_fps =  max(self.fps) if len(self.fps) > 0 else -1
        return [self.filename, self.start_cell, f'{t_extime:.20f}', t_cell_extime_avg, t_cell_extime_max, len(self.errors), phi_rate, len(self.fps), min_fps, max_fps]

    def write_row_to_file(self):
        t_extime = self.execute_time
        t_cell_extime_avg = statistics.mean(self.cell_times)
        t_cell_extime_max = max(self.cell_times)

        print(t_extime + "\t" + t_cell_extime_avg + "\t" + t_cell_extime_max + "\t")






