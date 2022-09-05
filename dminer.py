from prettytable import PrettyTable
import xml.etree.ElementTree as ET
from termcolor import colored
from colorama import init
from pprint import pprint
from time import sleep
import subprocess
import sys
import os
import re


# Вызов nvidia-smi для получения всей информаци об видеокартах
def get_videocard():
#    print("Проверка списка видеокарт")
    res = os.system("nvidia-smi -x -q > /home/user/dminer/xml/nvidia.xml")
    if res != 0:
        print("Ошибка при выполнении команды 'nvidia-smi -x -q', проверьте её вывод. Завершение скрипта.")
        sys.exit()
    gpu_json = get_list_videocard()
    return gpu_json


# Преобразование полученного xml в json
def get_list_videocard():
    tree = ET.parse("/home/user/dminer/xml/nvidia.xml")
    root = tree.getroot()
    gpu_json['timestamp'] = root.find('timestamp').text
    gpu_json['driver_version'] = root.find('driver_version').text
    gpu_json['cuda_version'] = root.find('cuda_version').text
    gpu_json['GPU'] = {}
    gpu_all = root.findall('gpu')
    for gpu in gpu_all:
        gpu_json['GPU'][gpu.find('minor_number').text] = {
                                                  'minor_number': gpu.find('minor_number').text,
                                                  'product_name': gpu.find('product_name').text,
                                                  'vbios_version': gpu.find('vbios_version').text,
                                                  'fan_speed': gpu.find('fan_speed').text,
                                                  'performance_state': gpu.find('performance_state').text,
                                                  'fb_memory_usage': {
                                                                      'total': gpu.find('fb_memory_usage').find('total').text,
                                                                      'reserved': gpu.find('fb_memory_usage').find('reserved').text,
                                                                      'used': gpu.find('fb_memory_usage').find('used').text,
                                                                      'free': gpu.find('fb_memory_usage').find('free').text
                                                                     },
                                                  'bar1_memory_usage': {
                                                                        'total': gpu.find('bar1_memory_usage').find('total').text,
                                                                        'used': gpu.find('bar1_memory_usage').find('used').text,
                                                                        'free': gpu.find('bar1_memory_usage').find('free').text
                                                                       },
                                                  'utilization': {
                                                                  'gpu_util': gpu.find('utilization').find('gpu_util').text,
                                                                  'memory_util': gpu.find('utilization').find('memory_util').text,
                                                                 },
                                                  'temperature': {
                                                                  'gpu_temp': gpu.find('temperature').find('gpu_temp').text,
                                                                  'gpu_target_temperature': gpu.find('temperature').find('gpu_target_temperature').text,
                                                                  'gpu_temp_max_threshold': gpu.find('temperature').find('gpu_temp_max_threshold').text,
                                                                  'gpu_temp_slow_threshold': gpu.find('temperature').find('gpu_temp_slow_threshold').text,
                                                                 },
                                                  'supported_gpu_target_temp': {
                                                                                'gpu_target_temp_min': gpu.find('supported_gpu_target_temp').find('gpu_target_temp_min').text,
                                                                                'gpu_target_temp_max': gpu.find('supported_gpu_target_temp').find('gpu_target_temp_max').text,
                                                                               },
                                                  'power_readings': {
                                                                     'power_state': gpu.find('power_readings').find('power_state').text,
                                                                     'power_management': gpu.find('power_readings').find('power_management').text,
                                                                     'power_draw': gpu.find('power_readings').find('power_draw').text,
                                                                     'power_limit': gpu.find('power_readings').find('power_limit').text,
                                                                     'default_power_limit': gpu.find('power_readings').find('default_power_limit').text,
                                                                     'enforced_power_limit': gpu.find('power_readings').find('enforced_power_limit').text,
                                                                     'min_power_limit': gpu.find('power_readings').find('min_power_limit').text,
                                                                     'max_power_limit': gpu.find('power_readings').find('max_power_limit').text
                                                                    },
                                                  'clocks': {
                                                             'graphics_clock': gpu.find('clocks').find('graphics_clock').text,
                                                             'sm_clock': gpu.find('clocks').find('sm_clock').text,
                                                             'mem_clock': gpu.find('clocks').find('mem_clock').text,
                                                             'video_clock': gpu.find('clocks').find('video_clock').text
                                                            },
                                                  'processes': {
                                                                'gpu_instance_id': gpu.find('processes')[1].find('gpu_instance_id').text,
                                                                'compute_instance_id': gpu.find('processes')[1].find('compute_instance_id').text,
                                                                'pid': gpu.find('processes')[1].find('pid').text,
                                                                'type': gpu.find('processes')[1].find('type').text,
                                                                'process_name': gpu.find('processes')[1].find('process_name').text
                                                               },
                                                  }
    return gpu_json


def count_lines(file, chunk_size=1<<13):
    return sum(chunk.count('\n')
            for chunk in iter(lambda: file.read(chunk_size), ''))


def read_log_trex(gpu_json):
    f = open('/var/log/miner/t-rex/t-rex.log')
    log = ""
    res = ""
    if ('number_line_log_trex' in gpu_json) == False:
        gpu_json['number_line_log_trex'] = 0
    for i, line in enumerate(f):
        if i > gpu_json['number_line_log_trex']:
            gpu_json['number_line_log_trex'] = i
            match_hash = re.findall('GPU #.*: .* - .* MH', str(line))
            if len(match_hash) > 0:
                match_number_gpu = re.findall('#.*:', str(match_hash))[0][1:-1]
                match_speed_hash = re.findall(' - .* MH', str(match_hash))[0][3:] + "/s"
                gpu_json['GPU'][match_number_gpu]['speed_log_hash'] = match_speed_hash

    for line in f:
        log += line
    log_split = log.split("\n")
    logs = log_split[-15:]
    for l in logs:
       res += f"{l}\n"
    return res, gpu_json


def read_log_gminer(gpu_json):
    f = open('/var/log/miner/gminer/gminer.log')
    log = ""
    res = ""
    if ('number_line_log_gminer' in gpu_json) == False:
        gpu_json['number_line_log_gminer'] = 0
    for i, line in enumerate(f):
        if i > gpu_json['number_line_log_gminer']:
            gpu_json['number_line_log_gminer'] = i
            # match_hash = re.findall('GPU #.*: .* - .* MH', str(line))
            # |  0    1060  26.27 MH/s  0/0/0    N/A    96 W  273.65 KH/W |
            match_hash = re.findall('\|.*MH', str(line))
            if len(match_hash) > 0:
                # match_number_gpu = re.findall('#.*:', str(match_hash))[0][1:-1]
                # match_speed_hash = re.findall(' - .* MH', str(match_hash))[0][3:] + "/s"
                match_hash = match_hash[0].split()
                # print(match_hash)
                try:
                    match_number_gpu = match_hash[1]
                    match_speed_hash = f"{match_hash[3]} {match_hash[4]}/s"
                    gpu_json['GPU'][match_number_gpu]['speed_log_hash'] = match_speed_hash
                except:
                    pass

    for line in f:
        log += line
    log_split = log.split("\n")
    logs = log_split[-15:]
    for l in logs:
       res += f"{l}\n"
    return res, gpu_json


def screen(gpu_json, log_trex, log_gminer):
    os.system("clear")

    print(f"DIx Miner v0.510    Время: {gpu_json['timestamp']}    Версия драйвера: {gpu_json['driver_version']}    Версия CUDA: {gpu_json['cuda_version']}")

    td = [
          '№',
          'Карта',
#          'vbios_version',
#          'fan_speed',
#          'fb_memory_usage_total',
#          'fb_memory_usage_reserved',
          'Исп RAM',
#          'fb_memory_usage_free',
          'GPU %',
          'RAM %',
          't',
#          'gpu_target_temperature',
#          'gpu_temp_max_threshold',
#          'gpu_temp_slow_threshold',
#          'gpu_target_temp_min',
#          'gpu_target_temp_max',
          'Hz Граф',
#          'sm Част',
          'Hz RAM',
          'Hz GPU',
          'Майнер',
          'PS',
#          'power_management',
          'Power',
          'Limit',
        #   'default_power_limit',
        #   'enforced_power_limit',
        #   'min_power_limit',
        #   'max_power_limit',
          'SHash',
         ]

    table = PrettyTable(td)
    table.align['Карта'] = "l"
    table.align['Power'] = "r"
    table.align['Limit'] = "r"

    for gpu in gpu_json['GPU']:
        minor_number = gpu_json['GPU'][gpu]['minor_number']
        product_name = gpu_json['GPU'][gpu]['product_name'][15:]
        # product_name = gpu_json['GPU'][gpu]['product_name']
        # vbios_version = gpu_json['GPU'][gpu]['vbios_version']
        # fan_speed = gpu_json['GPU'][gpu]['fan_speed']
        # fb_memory_usage_total = gpu_json['GPU'][gpu]['fb_memory_usage']['total']
        # fb_memory_usage_reserved = gpu_json['GPU'][gpu]['fb_memory_usage']['reserved']
        fb_memory_usage_used = gpu_json['GPU'][gpu]['fb_memory_usage']['used']
        # fb_memory_usage_free = gpu_json['GPU'][gpu]['fb_memory_usage']['free']
        gpu_util = gpu_json['GPU'][gpu]['utilization']['gpu_util']
        memory_util = gpu_json['GPU'][gpu]['utilization']['memory_util']
        gpu_temp = gpu_json['GPU'][gpu]['temperature']['gpu_temp']
        # gpu_target_temperature = gpu_json['GPU'][gpu]['temperature']['gpu_target_temperature']
        # gpu_temp_max_threshold = gpu_json['GPU'][gpu]['temperature']['gpu_temp_max_threshold']
        # gpu_temp_slow_threshold = gpu_json['GPU'][gpu]['temperature']['gpu_temp_slow_threshold']
        # gpu_target_temp_min = gpu_json['GPU'][gpu]['supported_gpu_target_temp']['gpu_target_temp_min']
        # gpu_target_temp_max = gpu_json['GPU'][gpu]['supported_gpu_target_temp']['gpu_target_temp_max']
        graphics_clock = gpu_json['GPU'][gpu]['clocks']['graphics_clock']
#        sm_clock = gpu_json['GPU'][gpu]['clocks']['sm_clock']
        mem_clock = gpu_json['GPU'][gpu]['clocks']['mem_clock']
        video_clock = gpu_json['GPU'][gpu]['clocks']['video_clock']
        process_name = gpu_json['GPU'][gpu]['processes']['process_name']
        if "rex" in process_name:
            trex = True
            process_name = "T-Rex"
        else:
            trex = False
        if "gminer" in process_name:
            gminer = True
            process_name = "GMiner"
        else:
            gminer = False
        power_state = gpu_json['GPU'][gpu]['power_readings']['power_state']
#        power_management = gpu_json['GPU'][gpu]['power_readings']['power_management']
        power_draw = gpu_json['GPU'][gpu]['power_readings']['power_draw']
        power_limit = gpu_json['GPU'][gpu]['power_readings']['power_limit']
#        default_power_limit = gpu_json['GPU'][gpu]['power_readings']['default_power_limit']
#        enforced_power_limit = gpu_json['GPU'][gpu]['power_readings']['enforced_power_limit']
#        min_power_limit = gpu_json['GPU'][gpu]['power_readings']['min_power_limit']
#        max_power_limit = gpu_json['GPU'][gpu]['power_readings']['max_power_limit']
        speed_log_hash = gpu_json['GPU'][gpu]['speed_log_hash']

        th = [
              minor_number,
              product_name,
#              vbios_version,
#              fan_speed,
#              fb_memory_usage_total,
#              fb_memory_usage_reserved,
              fb_memory_usage_used,
#              fb_memory_usage_free,
              gpu_util, memory_util,
              gpu_temp,
#              gpu_target_temperature,
#              gpu_temp_max_threshold,
#              gpu_temp_slow_threshold,
#              gpu_target_temp_min,
#              gpu_target_temp_max,
              graphics_clock,
#              sm_clock,
              mem_clock,
              video_clock,
              process_name,
              power_state,
#              power_management,
              power_draw,
              power_limit,
#              default_power_limit,
#              enforced_power_limit,
#              min_power_limit,
#              max_power_limit,
              speed_log_hash
             ]
        table.add_row(th)

    print(table)

    if trex == True and gminer == True:
        td_log = ['T-Rex', 'GMiner']
    elif trex == True:
        td_log = ['T-Rex']
    elif gminer == True:
        td_log = ['GMiner']
    table_log = PrettyTable(td_log)
    if trex == True and gminer == True:
        th_log = [log_trex, log_gminer]
    elif trex == True:
        th_log = [log_trex]
    elif gminer == True:
        th_log = [log_gminer]
    table_log.add_row(th_log)
    if trex == True and gminer == True:
        table_log.align['T-Rex'] = "l"
        table_log.align['GMiner'] = "l"
    elif trex == True:
        table_log.align['T-Rex'] = "l"
    elif gminer == True:
        table_log.align['GMiner'] = "l"

    print(table_log)
        

gpu_json = {}

while True:
    gpu_json = get_videocard()
    log_trex, gpu_json = read_log_trex(gpu_json)
    log_gminer = read_log_gminer(gpu_json)
    screen(gpu_json, log_trex, log_gminer)
    sleep(10)
