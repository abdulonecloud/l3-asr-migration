L3/HA Scale Test Deployment Script V1
-------------------------------------
Developer: gopal@onecloudinc.com

Description:
------------
This script will create Tenants, Users per Tenant, Networks, Subnets, Router with External Gateway, VMS, Floating IPs based on global configuration parameters specified on the config.py file. 
For each run of Scale Test Deployment Script, a summarized result for OpenStack and ASR VRF verification should be generated that describes a pass/fail for each test milestone.


Stepts to run the scale test deployment:
========================================

Step :: 1
---------

==> Define the Scale Test Configuration for the global parameters in 'config.py' file.

# Tenant Settings
 
OS_USERNAME = 'admin'
OS_TENANT_NAME = 'admin'
OS_PASSWORD = 'admin123'
OS_AUTH_URL = 'http://10.1.25.136:5000/v2.0/'
TENANT_COUNT = 2
TENANT_NAME_PREFIX = 'tenant-test'
TENANT_BASE_INDEX = 101
USER_COUNT = 1
USER_PASSWORD = 'secret'
NETWORK_COUNT = 2
VM_COUNT = 1
EXTERNAL_NETWORK = 'public'

# Floating IP Settings

FLOATING_IP_CREATION = True
FLOATING_IP_POOL = 'public'

# Cisco ASR Settings

ENABLE_ASR_VERIFICATION = True
DEPLOYMENT_ID = 'ans136'
ASR_HOST = '10.10.10.10'
ASR_USER = 'admin'
ASR_PASSWORD = 'admin'

Note: 

- Modify your target OpenStack credentials on the above config Tenant Settings part.
- If you want to assign Floating IP for VMs during Scale Test, Enable FLOATING_IP_CREATION = True & FLOATING_IP_POOL detail on the above config Floating IP Settings part.
- If you want to do ASR VRF Verification for the OpenStack Events during Scale Test and get the consolidated verification report, Enable ENABLE_ASR_VERIFICATION = True & your Cisco ASR credentials with the OpenStack DEPLOYMENT_ID which you mentioned in 'cisco_router_plugin.ini' file from your target OpenStack Environment on the above config Cisco ASR Settings part.


Step :: 2
---------

==> Intialize the scale test deployment by running the 'initialize_deploy.py' python script.

[onecloud@localhost ]$ python initialize_deploy.py

This script will create Tenants, Users per Tenant, Networks, Subnets, Router with External Gateway, VMS, Floating IPs based on global configuration parameters specified for a single tenant.

.. image:: https://raw.githubusercontent.com/gopal1cloud/L3_ASR_scale_test/l3_asr_develop/Scale_Test_Deployment_Per_Tenant_Screenshot.png
   :alt: Scale Test Topology

Step :: 3
---------

==> Destroy the scale test deployment by running the 'destroy_deploy.py' python script.

[onecloud@localhost ]$ python destroy_deploy.py

This script will delete Tenants, Users per Tenant, Networks, Subnets, Router with External Gateway, VMS, Floating IPs based on global configuration parameters specified for a single tenant.

Thats It.


I have given the same console output in a text file named 'Sample_Scale_Test_Deployment_Console_Output.txt', 'Sample_Destroy_Scale_Test_Deployment_Console_Output.txt' and
sample openstack network topology named 'Scale_Test_Deployment_Per_Tenant_Screenshot.png' in the script folder for reference.

Thanks!!!
