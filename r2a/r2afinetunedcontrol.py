# -*- coding: utf-8 -*-
"""
@author: Vinícius A. Peres (viniperes@aluno.unb.br) 03/04/2021

@description: PyDash Project

An implementation of a Fine-Tuned Control-Theoretic Approach for DASH.

The quality list is obtained with the parameter of handle_xml_response() 
method and the choice is made inside of handle_segment_size_request(), before 
sending the message down.

In this algorithm the quality choice is made using control-theoretic approach.
"""

# https://jckantor.github.io/CBE30338/04.01-Implementing_PID_Control_with_Python_Yield_Statement.html
# https://onion.io/2bt-pid-control-python/
# https://pypi.org/project/simple-pid/
# http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/

from player.parser import *
from r2a.ir2a import IR2A
from time import perf_counter
from typing import Tuple
from simple_pid import PID
import json
import os


class R2AFineTunedControl(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []
        self.previous_error = 0
        self.error_sum = 0
        self.previous_time = 0
        self.request_time = 0
        self.average_download_rate = []
        self.chunk_size = 0
        self.x = 1
        self.de = 1
        self.previous_levels = []
        self.l_plus_counter = 0
        self.l_minus_counter = 0
        self.previous_buffer_time = self.whiteboard.get_amount_video_to_play()
        with open('C:/Users/Vinícius Araújo/Documents/UnB/Transmissão de Dados/Trabalho/pydash/test_parameters.json') as json_file:
            self.data = json.load(json_file)
        self.q0 = self.data['q0']
        self.pid = PID(0.01, 0.01, 0.01, setpoint=self.q0)

    def handle_xml_request(self, msg):
        self.request_time = perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        download_time = perf_counter() - self.request_time
        self.average_download_rate.append(msg.get_bit_length()/download_time)
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        output = self.control_system(self.q0)
        level = self.state_machine(output[0], output[1])
        self.previous_levels.append(level)
        # time to define the segment quality choose to make the request
        msg.add_quality_id(level)
        self.request_time = perf_counter()
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        download_time = perf_counter() - self.request_time
        self.average_download_rate.append(msg.get_bit_length() / download_time)
        self.previous_buffer_time = self.whiteboard.get_amount_video_to_play()
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

    def pid_controller(self, error: float) -> float:
        """
        A method that implements the PID controller.

        Args:
            error (float): Set-point - measurement.
        Returns:
            out (float): Key order to sort.
        """

        kp = self.data['kp']
        ki = self.data['ki']
        kd = self.data['kd']

        print('************************** CONSTANTES **************************')
        print(f'Kp = {kp}')
        print(f'Ki = {ki}')
        print(f'Kd = {kd}')
        print('************************** CONSTANTES **************************')

        current_time = perf_counter()

        p = kp * error
        i = self.error_sum + (ki * error * (current_time - self.previous_time))
        d = kd * (error - self.previous_error) / (current_time - self.previous_time)

        self.previous_error = error
        self.previous_time = current_time
        self.error_sum = i

        return p+i+d

    def control_system(self, ref: int) -> Tuple[float, float]:
        """
        A method that implements the control system.

        Args:
            ref (int): reference variable.
        Returns:
            out (Tuple[float,float]): Key order to sort.
        """

        aux = self.average_download_rate[-1] / self.de
        buffer_time = self.whiteboard.get_amount_video_to_play()
        output1 = self.pid(buffer_time)
        output2 = self.pid_controller(ref - buffer_time)
        calc_level = (-aux * (1 / self.x)) * output1 + aux
        print('**************************************')
        print(output1)
        print(output2)
        print('**************************************')
        sel_level = min(self.qi, key=lambda x: abs(x - calc_level))

        return buffer_time, sel_level

    def state_machine(self, buffer_time: float, sel_level: float) -> float:

        q_max = 55
        q_min = 5
        m = self.data['m']
        n = self.data['n']

        print('************************** MN **************************')
        print(f'M = {m}')
        print(f'N = {n}')
        print('************************** MN **************************')

        if buffer_time < q_min:
            return self.qi[0]
        elif buffer_time > q_max:
            change_time = perf_counter()
            threshold = self.previous_buffer_time + self.x - (sel_level * self.x)/self.average_download_rate[-1] - q_max
            current_time = perf_counter()
            while (current_time - change_time) <= threshold:
                current_time = perf_counter()
            return sel_level
        else:
            if sel_level > self.previous_levels[-1]:
                self.l_minus_counter = 0
                self.l_plus_counter = self.l_plus_counter + 1
                if self.l_plus_counter >= m:
                    return sel_level
                else:
                    return self.previous_levels[-1]
            elif sel_level < self.previous_levels[-1]:
                self.l_plus_counter = 0
                self.l_minus_counter = self.l_minus_counter + 1
                if self.l_minus_counter >= n:
                    return sel_level
                else:
                    return self.previous_levels[-1]
            else:
                return self.previous_levels[-1]

