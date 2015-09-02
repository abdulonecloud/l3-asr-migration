from fabric.api import *
import fabric
from fabric.network import ssh
import sys

#import pudb

ssh.util.log_to_file("paramiko.log", 10)

host_list = ['1.2.3.3', '1.2.3.2', '1.2.3.5']
env.hosts = host_list
env.user = 'noiro'
env.password = 'noir0123'
env.gateway = '10.30.120.11'
#env.shell = "/bin/sh -c"

@task
def get_hostname():
    out = run("hostname")
    print out

@task
@parallel
def start_traffic(env):

    for host in host_list:
        if host != env.host_string:
#            with cd("~/dp_test_results"):
            sudo('hping3  %s --icmp --fast -q 2> sampletraffic-%s-%s.txt 1> /dev/null &' %(host,env.host_string.replace('.','_'), host.replace('.','_')), pty=False)
        

@task
@parallel
def stop_traffic():
#    with cd("~/dp_test_results"):
        sudo("kill -SIGINT `pgrep hping3`")
#    with cd("~/dp_test_results"):
        for host in host_list:
            if host != env.host_string:
                out = sudo("cat sampletraffic-%s-%s.txt | grep loss" %(env.host_string.replace('.','_'), host.replace('.','_')))
                print out

@task
@runs_once
def start_task():
    if sys.argv[1] == 'start':
         execute(start_traffic, env)
    elif sys.argv[1] == 'stop':
         execute(stop_traffic, hosts = env.hosts)
    else:
         execute(get_hostname, hosts = env.hosts)

if __name__ == '__main__':
    start_task()
