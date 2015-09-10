import json
import os
import re
import sys


fileid = sys.argv[1]
filedir = os.getcwd()


def get_list_of_filenames():
    file_list = []
    for file in os.listdir(filedir):
        if file.startswith("tcp") and file.endswith("%s.txt" % (fileid)):
            file_list.append(file)
    return file_list


def process_files(file_list):
    out = {}
    for file in file_list:
        out[file] = get_test_results(file)
    return out


def get_test_results(file):
    """
    For a given test output file, return a tuple of the following format
    (bandwidth_loss dict wth keys interval_time, transferred, bandwidth) 
    """
    f = open(file, 'r')

    for line in f:
        if "[ ID]" in line:
            report = f.next()
            report_data = report.split(']')[1].split('  ')
            # also want packets transmitted, packets received, % packet loss
            
            bandwidth_stats = \
                {'interval_time': str(report_data[1]),   # NOQA
                 'transferred': str(report_data[2]),   # NOQA
                 'bandwidth': str(report_data[3].replace('\n', ''))}   # NOQA
    
    test_results = {'bandwidth_stats': bandwidth_stats}

    return test_results


def main():
    file_list = get_list_of_filenames()
    script_output = process_files(file_list)
    json_output = json.JSONEncoder().encode(script_output)
    # sample output
    # {'test.txt': ({'packet_loss': '0%'},
    #               {'rtt_min': '4.3', 'rtt_avg': '5.5', 'rtt_max': '6.3'})}
    print json_output

if __name__ == '__main__':
    main()
