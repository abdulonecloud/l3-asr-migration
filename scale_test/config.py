"""
Description: Define the Scale Test Configuration with the below global \
             parameters.
Developer: gopal@onecloudinc.com
"""

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
IMAGE_NAME = 'Cirros'
FLAVOUR_NAME = 'm1.tiny'
EXTERNAL_NETWORK = 'public'

# Floating IP Settings

FLOATING_IP_CREATION = True
FLOATING_IP_POOL = 'public'

# Cisco ASR Settings

ENABLE_ASR_VERIFICATION = False
DEPLOYMENT_ID = 'ans136'
ASR_HOST = '10.10.10.10'
ASR_USER = 'admin'
ASR_PASSWORD = 'admin'


"""
Test Configuration Ends Here with the global parameters.
"""


def print_scale_test_config():
    """
    This method is used to print the current test configuration on scale test \
    deployment initialization.
    """
    print '=' * 70
    print "    Configuration for this Scale Test"
    print '=' * 70

    print " Tenant will be created with prefix                         : " \
        + TENANT_NAME_PREFIX
    print " No of Tenants will be created                              : " \
        + str(TENANT_COUNT)
    print " Tenant base index range starts from                        : " \
        + str(TENANT_BASE_INDEX)
    print " No of Users per Tenant                                     : " \
        + str(USER_COUNT)
    print " No of Networks                                             : " \
        + str(NETWORK_COUNT)
    print " No of VMs per Network                                      : " \
        + str(VM_COUNT)
    print " Name of the External Network with be connected with Router : " \
        + EXTERNAL_NETWORK
    print " Name of the Floating IP Pool will be used for Allocation   : " \
        + FLOATING_IP_POOL
    print '=' * 70
