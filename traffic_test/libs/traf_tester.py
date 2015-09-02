import fabric
from fabric.api import *
import os
import sys
import logging
import time
import re
from multiprocessing import Pool, Process, Queue
from prettytable import PrettyTable
import json

path = os.getcwd() + '/scripts'
os.path.join(path)

test_results_path = '~/dp_test_results'

logger = logging.getLogger(__name__)


def setup_env(config, endpoints):
    endpoints = endpoints
    test_results_path = config['traffic']['test_results_path']
    test_method = config['traffic']['test_method']
    delta = config['traffic']['allowed_delta_percentage']
    env.hosts = endpoints['src_eps']
    env.user = config['traffic']['remote_user']
    env.password = config['traffic']['remote_pass']
    env.skip_bad_hosts = True
    env.gateway = config['traffic']['ssh_gateway']

    logger.info("Initailized the environment with Endpoints")
    logger.info("test_results_path : %s" % (test_results_path))
    logger.info("test_method : %s" % (test_method))
    logger.info("traffic allowed delta : %s" % (delta))


def get_test_cmd(test_method):
    pass


def install_hping(environment):
    try:
        out = run("python -c 'import platform;"
                  " print platform.linux_distribution()[0]'")
        os_info = out
        logger.debug("Host %s runs %s" % (env.host_string, os_info))
        if out.return_code == 0:
            if os_info in ['CentOS',
                           'Red Hat Enterprise Linux Server',
                           'Fedora']:
                out = sudo("yum -y install hping3")
                if out.return_code == 0:
                    logger.info("Installed hping3 on %s" % (env.host_string))
            elif os_info in ['Ubuntu']:
                out = sudo("apt-get -y install hping3")
                if out.return_code == 0:
                    logger.info("Installed hping3 on %s" % (env.host_string))
        out = run("mkdir %s" % (test_results_path))
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


def pretty_table_content(config, data):
    x = PrettyTable(["src_tenant",
                     "src_ep",
                     "dest_tenant",
                     "dest_ep",
                     "packets_transmitted",
                     "packets received",
                     "packet_loss %",
                     "rtt_min",
                     "rtt_avg",
                     "rtt_max",
                     "test_status"])

    x.align["src_tenant"] = "l"  # Left align source tenant values

    # One space between column edges and contents (default)
    x.padding_width = 1
    status = None

    dest_ep_regex = ".*-*-(?P<dest_ip>[0-9]+_[0-9]+_[0-9]+_[0-9]+)-.*"
    for content in data:
        for k, v in content.items():
            src_ep = k
            src_tenant = v['src_tenant']
            dest_tenant = v['dest_tenant']
            # out = v['test_result'].split(',')
            test_result_files = v['test_result'].keys()

            for test_result_file in test_result_files:

                dest_ep_match = re.match(dest_ep_regex, test_result_file)

                dest_ep = dest_ep_match.group('dest_ip')
                packet_stats = \
                    v['test_result'][test_result_file]['packet_stats']

                packet_loss_percent = \
                    packet_stats['packet_loss']  # NOQA

                try:
                    if (packet_loss_percent <= int(config['traffic']['allowed_delta_percentage'])):  # NOQA
                            status = 'Success'
                    else:
                        status = 'Failed'
                except ValueError:
                    status = 'Failed'

                rtt_stats = v['test_result'][test_result_file]['rtt']

                x.add_row([src_tenant, src_ep,
                           dest_tenant, dest_ep.replace('_', '.'),
                           packet_stats['packets_transmitted'],
                           packet_stats['packets_received'],
                           packet_loss_percent,
                           rtt_stats['rtt_min'],
                           rtt_stats['rtt_avg'],
                           rtt_stats['rtt_max'],
                           status])
    print x


@task
@parallel
def create_test_results_directory(environment):
    try:
        run("mkdir %s" % (test_results_path))
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


@task
@parallel
def test_ping(environment, config, endpoints, contract, timestamp):
    try:
        for dest_ep in endpoints['dest_eps']:
            if dest_ep != env.host_string:
                sudo("hping3 %s --icmp --fast -q 2>"
                     " testtraffic-%s-%s-%s.txt 1> /dev/null &" %
                     (dest_ep,
                      env.host_string.replace('.', '_'),
                      dest_ep.replace('.', '_'),
                      timestamp),
                     pty=False)

    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


@task
def test_tcp(environment, endpoints, contract, timestamp):
    pass


@task
def test_udp(environment, endpoints, contract, timestamp):
    pass


def capture_output():
    pass


@task
@parallel
def stop_traffic(environment, endpoints, timestamp):
    try:
        sudo("kill -SIGINT `pgrep hping3`")
        print "dest_eps are.....", endpoints['dest_eps']
        put("scripts/get_ping_statistics.py", "get_ping_statistics.py")
        out = run("python get_ping_statistics.py %s" % (timestamp))

        out_dict = json.JSONDecoder().decode(out)

        output = {'src_tenant': endpoints['src_tenant'],
                  'dest_tenant': endpoints['dest_tenant'],
                  'test_result': out_dict}
        # print output

        return output
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


def start_task(config, endpoints_list, action, testPrefix=None):
    timestamp = testPrefix
    if not testPrefix:
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")

    output_table_data_list = []
    for endpoints in endpoints_list:
        table_data = {}
        setup_env(config, endpoints)
        execute(install_hping, env)
        if action == 'start':
            execute(create_test_results_directory, env)
            for contract in endpoints['contract']:
                if contract['protocol'] == 'icmp':
                    execute(test_ping, env, config,
                            endpoints, contract, timestamp)
                if contract['protocol'] == 'tcp':
                    execute(test_tcp, env, endpoints, contract, timestamp)
                if contract['protocol'] == 'udp':
                    execute(test_udp, env, endpoints, contract, timestamp)

        if action == 'stop':
            table_data = execute(stop_traffic, env, endpoints, timestamp)
            output_table_data_list.append(table_data)

    if output_table_data_list:
        pretty_table_content(config, output_table_data_list)
