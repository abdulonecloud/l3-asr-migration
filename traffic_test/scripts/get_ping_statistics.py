import json
import os
import re
import sys


fileid = sys.argv[1]
filedir = os.getcwd()


def get_list_of_filenames():
    file_list = []
    for file in os.listdir(filedir):
        if file.endswith("%s.txt" % (fileid)):
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
    (packet_loss dict wth keys packet_loss,
     rtt dictionary with keys, rtt_min, rtt_avg, rtt_max)
    """
    f = open(file, 'r')

    rtt_regex = ".*= (?P<rtt_min>[0-9]+\.[0-9]+)/" \
                "(?P<rtt_avg>[0-9]+\.[0-9]+)/" \
                "(?P<rtt_max>[0-9]+\.[0-9]+) ms"

    packet_loss_regex = "(?P<packets_sent>[0-9]+) packets transmitted, " \
                        "(?P<packets_received>[0-9]+) packets received," \
                        " (?P<packet_loss>[0-9]+)%.*"

    for line in f:
        if "loss" in line:
            # also want packets transmitted, packets received, % packet loss
            packet_stats_match = re.match(packet_loss_regex, line)

            packet_stats = \
                {'packets_transmitted': int(packet_stats_match.group('packets_sent')),   # NOQA
                 'packets_received': int(packet_stats_match.group('packets_received')),  # NOQA
                 'packet_loss': int(packet_stats_match.group('packet_loss'))}

        if "round-trip" in line:
            match_results = re.match(rtt_regex, line)
            if (match_results is not None):
                rtt_min = match_results.group('rtt_min')
                rtt_avg = match_results.group('rtt_avg')
                rtt_max = match_results.group('rtt_max')

                rtt = {'rtt_min': rtt_min,
                       'rtt_avg': rtt_avg,
                       'rtt_max': rtt_max}

    test_results = {'packet_stats': packet_stats, 'rtt': rtt}

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
