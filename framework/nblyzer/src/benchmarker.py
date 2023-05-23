# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from collections import defaultdict
from sre_parse import fix_flags
from nblyzer import NBlyzer
from argparse import ArgumentParser
from events import RunBatchEvent
from resource_utils.rsrc_mngr import ResourceManager
from resource_utils.utils import is_script
import csv
import os
from tqdm import tqdm
import json


def benchmark(folder, analyses, level, output, filter, notebooks_to_run = None):
    nb_stats = []
    mng = ResourceManager()
    if notebooks_to_run:
        dir_list = notebooks_to_run
    else:
        dir_list = os.listdir(folder)
    stats_analysis = defaultdict(lambda: [])
    for f in tqdm(dir_list):
        if not f.endswith(".ipynb"):
            continue

        print("\nfile: " + f)
        if f in filter:
            continue

        try:
            notebook = mng.grab_local_json(folder+f)
        except FileNotFoundError:
            notebook = mng.grab_local_json(folder + "\\" + f)
        except json.decoder.JSONDecodeError:
            print("Warning decode error ")
            continue

        nblyzer = NBlyzer(level=level, filename=f)
        try:
           nblyzer.load_notebook(notebook["cells"])
        except KeyError:
            print("Warning syntax error ")
            continue
        except SyntaxError:
            print("Warning syntax error ")
            continue
        except Exception:
            print('Other')
            continue

        for start in nblyzer.notebook_IR.keys():
            nblyzer.add_analyses(analyses)

            event = RunBatchEvent(start)
            results = nblyzer.execute_event(event).dumps(True)

        for akey in nblyzer.active_analyses:
            for s in nblyzer.all_analyses[akey].stats:
                stats_analysis[akey].append(s.get_row())

        for s in stats_analysis.keys():
            with open(output + s.replace(" ", "") + ".csv", "w+") as f:
                writer = csv.writer(f)
                writer.writerow(["file name", "start cell", "execute time", "avg cell exec time", "max cell exec time", "no. of errors", "true phi rate", "no. fixedpoint", "longest fixedpoint path", "shortest fixedpoint path"])
                for rows in stats_analysis[s]:
                    writer.writerow(rows)

def main():
    parser = ArgumentParser(description="NBLyzer benchmarker version 1.0 ")
    parser.add_argument("-f", "--folder",  type=str, help='Benchmark folder')
    parser.add_argument("-a", "--analyses", nargs="+", type=str, default=[], help='Analyses to perform.')
    parser.add_argument("-l", "--level", nargs="?", type=int, default=1000, help='K-depth to analyze.')
    parser.add_argument("-o", "--output",  type=str, help='Output folder')
    args = parser.parse_args()

    filter = ["nb_4357163.ipynb", "nb_4207320.ipynb", "nb_3607344.ipynb", 
               "nb_4243327.ipynb", "nb_3709448.ipynb", "nb_3607795.ipynb", 
               "nb_3917413.ipynb", "nb_3847650.ipynb", "nb_3787548.ipynb", 
               "nb_3928517.ipynb", "nb_4129718.ipynb", "nb_3907591.ipynb", 
               "nb_4111798.ipynb", "nb_3953080.ipynb", "nb_3625218.ipynb", 
               "nb_4243362.ipynb"]
    kaggle_filter = ["183.ipynb"]

    fix_filter = ["nb_3765508.ipynb", "nb_3752761.ipynb", "nb_3797858.ipynb", "nb_3953414.ipynb", 
    "nb_4066630.ipynb", "nb_4241014.ipynb", "nb_4116288.ipynb", "nb_4377349.ipynb", "nb_3953451.ipynb", 
    "nb_4126120.ipynb", "nb_4355681.ipynb", "nb_4309469.ipynb", "nb_4342687.ipynb", "nb_4063850.ipynb", 
    "nb_3851656.ipynb", "nb_3911103.ipynb", "nb_3593763.ipynb", "nb_3537417.ipynb", "nb_3556019.ipynb", 
    "nb_4036196.ipynb", "nb_3851287.ipynb", "nb_4252631.ipynb", "nb_4278445.ipynb", "nb_4171747.ipynb", 
    "nb_4090500.ipynb", "nb_4021996.ipynb", "nb_3677219.ipynb", "nb_3692862.ipynb", "nb_3528051.ipynb",
    " nb_3962897.ipynb", "nb_3962897.ipynb", "nb_3774776.ipynb", "nb_3746379.ipynb", "nb_4363714.ipynb",
    "nb_3662295.ipynb", "nb_4223490.ipynb", "nb_3985266.ipynb", "nb_4233186.ipynb", "nb_4057621.ipynb", 
    "nb_3685062.ipynb", "nb_4361427.ipynb", "nb_3771155.ipynb", "nb_3947049.ipynb", "nb_4057664.ipynb", 
    "nb_3867357.ipynb", "nb_3801249.ipynb", "nb_4032449.ipynb", "nb_4333463.ipynb", "nb_4323936.ipynb", 
    "nb_4099946.ipynb", "nb_4377464.ipynb", "nb_4284043.ipynb", "nb_3974446.ipynb", "nb_3953339.ipynb", 
    "nb_4142420.ipyn", "nb_4142420.ipynb", "nb_3570808.ipynb", "nb_4133538.ipynb", "nb_4232980.ipynb", 
    "nb_4116131.ipynb", "nb_3516916.ipynb", "nb_3823315.ipynb", "nb_4263665.ipynb", "nb_3637310.ipynb", 
    "nb_3578363.ipynb", "nb_4157381.ipynb", "nb_4241781.ipynb", "nb_3847551.ipynb", "nb_3693099.ipynb", 
    "nb_4298472.ipynb", "nb_4117189.ipynb"]

    non_type_filter = ["nb_3815515.ipynb", "nb_3721960.ipynb", "nb_4372597.ipynb", 
                       "nb_3794171.ipynb", "nb_4373776.ipynb", "nb_4159459.ipynb", 
                       "nb_4094939.ipynb", "nb_3811543.ipynb", "nb_3615481.ipynb"]

    call_value_filter = ["nb_3871856.ipynb", "nb_3677005.ipynb", "nb_3666513.ipynb"]

    name_value = ["nb_4029245.ipynb"]

    key_error_filter = ["nb_4373905.ipynb", "nb_3797472.ipynb", "nb_4225281.ipynb", 
                        "nb_3938468.ipynb", "nb_3637011.ipynb", "nb_4366894.ipynb", 
                        "nb_3556205.ipynb", "nb_3968929.ipynb", "nb_3938689.ipynb", 
                        "nb_4195848.ipynb", "nb_4377916.ipynb", "nb_3895375.ipynb", 
                        "nb_3834667.ipynb", "nb_4358502.ipynb", "nb_4342767.ipynb", 
                        "nb_4387058.ipynb", "nb_3701251.ipynb"]

    beniget_filter = ["nb_3714079.ipynb", "nb_4117445.ipynb", "nb_3595869.ipynb"]

    list_range_filter = ["nb_3701309.ipynb", "nb_3895545.ipynb", "nb_3895500.ipynb", "nb_3677040.ipynb", "nb_4111584.ipynb"]

    exit_lhs_filter = ["nb_3608760.ipynb"]

    list_id_filter = ["nb_3983247.ipynb"]

    notebooks_to_run = ["183.ipynb"]

    benchmark(args.folder, args.analyses, args.level, args.output, 
    filter+fix_filter+non_type_filter+call_value_filter+name_value+key_error_filter+beniget_filter+list_range_filter+exit_lhs_filter+list_id_filter+kaggle_filter, notebooks_to_run=None)

if __name__ == "__main__":
    main()