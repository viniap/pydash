# -*- coding: utf-8 -*-
"""
@author: Marcos F. Caetano (mfcaetano@unb.br) 11/03/2020

@description: PyDash Project

Everything always starts from somewhere =)
"""

from dash_client import DashClient
import json
import os
import shutil



def write_json(q0, kp, ki, kd, m, n):
    data = {
        "q0": q0,
        "kp": kp,
        "ki": ki,
        "kd": kd,
        "m": m,
        "n": n
    }

    with open('test_parameters.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)


q0s = (10, 30, 50)
kps = (0.01, 0.1, 1)
kis = (0.01, 0.1, 1)
kds = (0.01, 0.1, 1)
ms = (1, 5, 10)
ns = (1, 5, 10)
parentdir = "C:/Users/Vinícius Araújo/Documents/UnB/Transmissão de Dados/Trabalho/pydash/results/"

for q0 in q0s:
    for kp in kps:
        for ki in kis:
            for kd in kds:
                for m in ms:
                    for n in ns:
                        write_json(q0, kp, ki, kd, m, n)
                        dash_client = DashClient()
                        dash_client.run_application()
                        dir = f'q0-{q0}_kp-{kp}_ki-{ki}_kd-{kd}_m-{m}_n-{n}'.replace('.', '')
                        path = os.path.join(parentdir, dir)
                        if not os.path.isdir(path):
                            os.mkdir(path)
                        shutil.copy(os.path.join(parentdir, 'playback.png'), path)
                        shutil.copy(os.path.join(parentdir, 'playback_buffer_size.png'), path)
                        if os.path.isfile(os.path.join(parentdir, 'playback_pauses.png')):
                            shutil.copy(os.path.join(parentdir, 'playback_pauses.png'), path)
                        shutil.copy(os.path.join(parentdir, 'playback_qi.png'), path)
                        shutil.copy(os.path.join(parentdir, 'playback_quality_qi.png'), path)
                        shutil.copy(os.path.join(parentdir, 'throughput.png'), path)
