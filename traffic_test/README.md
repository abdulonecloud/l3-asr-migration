# datapath-traffic-test

Collection of tools and utility scripts to validate datapath traffic between endpoints governed by a contract

**Traffic Test between Local VMs on VMware:**

**Starting Traffic:**
$ python main.py --cfgfile=conf/config.ini --action=start -t sample_timestamp_name_to_track


**Stoping Traffic:**
$ python main.py --cfgfile=conf/config.ini --action=stop -t sample_timestamp_name_to_track


**Output:**

+--------------+----------+--------------+----------+---------------------+------------------+---------------+---------+---------+---------+-------------+
| src_tenant   |  src_ep  | dest_tenant  | dest_ep  | packets_transmitted | packets received | packet_loss % | rtt_min | rtt_avg | rtt_max | test_status |
+--------------+----------+--------------+----------+---------------------+------------------+---------------+---------+---------+---------+-------------+
| traffic_test | 1.1.1.16 | traffic_test | 2.2.2.6  |         164         |       164        |       0       |   0.3   |   2.9   |   5.1   |   Success   |
| traffic_test | 1.1.1.16 | traffic_test | 1.1.1.15 |         167         |       167        |       0       |   0.3   |   2.8   |   5.1   |   Success   |
| traffic_test | 1.1.1.16 | traffic_test | 2.2.2.5  |         163         |       163        |       0       |   0.4   |   2.8   |   5.1   |   Success   |
| traffic_test | 1.1.1.16 | traffic_test | 1.1.1.17 |         166         |       166        |       0       |   0.6   |   33.1  |  1004.7 |   Success   |
| traffic_test | 1.1.1.17 | traffic_test | 2.2.2.6  |         164         |       164        |       0       |   1.1   |   2.8   |   5.1   |   Success   |
| traffic_test | 1.1.1.17 | traffic_test | 1.1.1.15 |         165         |       165        |       0       |   1.1   |   3.0   |   6.2   |   Success   |
| traffic_test | 1.1.1.17 | traffic_test | 2.2.2.5  |         162         |       162        |       0       |   0.4   |   27.4  |  1003.3 |   Success   |
| traffic_test | 1.1.1.17 | traffic_test | 1.1.1.16 |         166         |       166        |       0       |   0.6   |   3.3   |   7.8   |   Success   |
| traffic_test | 2.2.2.5  | traffic_test | 1.1.1.16 |         166         |       166        |       0       |   0.4   |   2.8   |   5.2   |   Success   |
| traffic_test | 2.2.2.5  | traffic_test | 1.1.1.17 |         164         |        0         |      100      |   0.0   |   0.0   |   0.0   |    Failed   |
| traffic_test | 2.2.2.5  | traffic_test | 2.2.2.6  |         162         |       162        |       0       |   1.1   |   9.1   |  1001.1 |   Success   |
| traffic_test | 2.2.2.5  | traffic_test | 1.1.1.15 |         165         |       165        |       0       |   0.3   |   3.0   |   5.1   |   Success   |
| traffic_test | 1.1.1.15 | traffic_test | 1.1.1.17 |         165         |       165        |       0       |   1.1   |   2.9   |   5.2   |   Success   |
| traffic_test | 1.1.1.15 | traffic_test | 2.2.2.6  |         163         |       163        |       0       |   0.2   |   2.9   |   5.1   |   Success   |
| traffic_test | 1.1.1.15 | traffic_test | 2.2.2.5  |         162         |       162        |       0       |   1.1   |   3.0   |   5.2   |   Success   |
| traffic_test | 1.1.1.15 | traffic_test | 1.1.1.16 |         166         |       166        |       0       |   0.3   |   2.9   |   5.1   |   Success   |
| traffic_test | 2.2.2.6  | traffic_test | 1.1.1.16 |         168         |       168        |       0       |   1.1   |   2.9   |   7.0   |   Success   |
| traffic_test | 2.2.2.6  | traffic_test | 1.1.1.17 |         165         |        0         |      100      |   0.0   |   0.0   |   0.0   |    Failed   |
| traffic_test | 2.2.2.6  | traffic_test | 1.1.1.15 |         166         |       166        |       0       |   0.8   |   9.0   |  1003.4 |   Success   |
| traffic_test | 2.2.2.6  | traffic_test | 2.2.2.5  |         163         |       163        |       0       |   0.4   |   21.3  |  1004.6 |   Success   |
+--------------+----------+--------------+----------+---------------------+------------------+---------------+---------+---------+---------+-------------+

