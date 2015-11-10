"""
Description: This script is to map the environment variables to credentials \
             dict based on the client service API
Developer: gopal@onecloudinc.com
"""

from config import OS_USERNAME, OS_TENANT_NAME, OS_PASSWORD, OS_AUTH_URL


def get_credentials():
    """
    This method is used for authorization with keystone clients
    """

    data = {}
    data['username'] = OS_USERNAME
    data['password'] = OS_PASSWORD
    data['auth_url'] = OS_AUTH_URL
    data['tenant_name'] = OS_TENANT_NAME
    return data


def get_nova_credentials():
    """
    This method is used for authorization with nova clients
    """

    data = {}
    data['username'] = OS_USERNAME
    data['api_key'] = OS_PASSWORD
    data['auth_url'] = OS_AUTH_URL
    data['project_id'] = OS_TENANT_NAME
    return data


def get_tenant_nova_credentials(tenant_name):
    """
    This method is used for tenant authorization with nova clients
    """

    data = {}
    data['username'] = OS_USERNAME
    data['api_key'] = OS_PASSWORD
    data['auth_url'] = OS_AUTH_URL
    data['project_id'] = tenant_name
    return data
