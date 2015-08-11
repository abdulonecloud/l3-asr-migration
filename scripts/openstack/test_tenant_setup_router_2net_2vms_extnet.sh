#!/bin/bash

# source ~/keystonerc_admin

# keystone tenant-create l3-asr-demo
TENANT=$(keystone tenant-list | awk '/l3-asr-demo/ { print $2 }')
echo $TENANT

# external network
neutron net-create exnet --tenant_id $TENANT --provider:network_type vlan --router:external True --shared --provider:physical_network phynet2 --provider:segmentation_id 599
neutron subnet-create exnet --tenant_id $TENANT --name exnet_subnet --no-gateway --disable-dhcp --allocation-pool start=99.99.1.31,end=99.99.1.50 99.99.1.0/24

# tenant networks
neutron net-create --tenant-id $TENANT net001
neutron subnet-create --tenant-id $TENANT --name subnet001 net001 10.10.1.0/24

neutron net-create --tenant-id $TENANT net002
neutron subnet-create --tenant-id $TENANT --name subnet002 net002 10.10.2.0/24

neutron net-create --tenant-id $TENANT net003
neutron subnet-create --tenant-id $TENANT --name subnet003 net003 10.10.3.0/24

#neutron net-list
neutron router-create --tenant-id $TENANT router001 
EXNET_ID=$(neutron net-list | grep exnet | awk '{print $2}'
ROUTER_ID=$(neutron router-list | grep router001 | awk '{print $2}'
neutron router-gateway-set $ROUTER_ID $EXNET_ID

# sleep 10
neutron router-interface-add router001 subnet001
neutron router-interface-add router001 subnet002

# neutron router-create --tenant-id $TENANT router002
# sleep 10
# neutron router-interface-add router002 subnet003
