# Openstack environment config

keystone_auth_url='http://10.30.120.50:5000/v2.0'
keystone_user='admin'
keystone_password='noir0123'
keystone_tenant_name='admin'

# Traffic test config

allowed_delta_percentage = 3
test_results_path = '~/dp_test_results'
ssh_gateway = '192.168.61.2'
number_of_workers = 10
remote_user = 'root'
remote_pass = 'root123'
test_method = 'hping'
