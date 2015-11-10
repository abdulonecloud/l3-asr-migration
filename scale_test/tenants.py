#!/usr/bin/env python
"""
Description: This script prepares new tenant with the following properties:
1. Creates new tenant.
2. Creates new user and this user is added _member_ to tenant. \
Password is second argument of script
3. Admin user will be added to tenant with role admin
Developer: gopal@onecloudinc.com
"""

import os
from keystoneclient.v2_0 import client as ksclient
from credentials import get_credentials
from config import USER_COUNT, USER_PASSWORD

credentials = get_credentials()
keystone = ksclient.Client(**credentials)
assign_admin = True


def create_tenant(tenant_name):
    """
    This method is used to create tenant and create number of users per tenant
    """

    print "\n"
    print "=" * 50
    print "   Initiated Tenant Creation for " + tenant_name
    print "=" * 50
    print "\n"

    try:
        try:
            new_tenant = keystone.tenants.create(tenant_name=tenant_name,
                                                 description="Scale tenant \
                                                     created",
                                                 enabled=True)
        except Exception:
            new_tenant = keystone.tenants.find(name=tenant_name)
        tenant_id = new_tenant.id
        tenant_status = True
        print('   - Tenant %s created' % tenant_name)
        user_data = []
        for j in range(USER_COUNT):
            j += 1
            user_name = tenant_name + '-user-' + str(j)
            user_data.append(create_user(user_name, tenant_id))
    except Exception:
        tenant_status = False

    print "\n"
    msg = ('<== Completed Tenant Creation and Users per Tenant '
           'with _member_ role ')
    msg += 'Successfully ==>'
    print msg
    print "\n"

    tenant_data = {'tenant_name': tenant_name,
                   'tenant_id': tenant_id,
                   'status': tenant_status}
    return tenant_data


def create_user(user_name, tenant_id):
    """
    This method is to create users per Tenant
    """

    try:
        new_user = keystone.users.create(name=user_name,
                                         password=USER_PASSWORD,
                                         tenant_id=tenant_id)
    except Exception:
        new_user = keystone.users.find(name=user_name)
    print('   - Created User %s' % user_name)
    member_role = keystone.roles.find(name='_member_')
    try:
        keystone.roles.add_user_role(new_user, member_role, tenant_id)
    except Exception:
        pass
    if assign_admin:
        admin_user = keystone.users.find(name='admin')
        admin_role = keystone.roles.find(name='admin')
        try:
            keystone.roles.add_user_role(admin_user, admin_role, tenant_id)
        except Exception:
            pass
    user_data = {'name': new_user.name,
                 'id': new_user.id}
    return user_data


def delete_tenant(tenant_name):
    """
    This method is used to delete tenant and users
    """

    try:
        tenant = keystone.tenants.find(name=tenant_name)
        for j in range(USER_COUNT):
            j += 1
            user_name = tenant_name + '-user-' + str(j)
            delete_user(user_name, tenant.id)
    except Exception:
        pass
    try:
        new_tenant = keystone.tenants.find(name=tenant_name)
        new_tenant.delete()
        print('   - Deleted Tenant %s ' % tenant_name)
    except Exception:
        print("   - Tenant Not Found: %s" % tenant_name)
        pass
    return True


def delete_user(user_name, tenant_id):
    """
    This method is to delete users per Tenant
    """
    try:
        user = keystone.users.find(name=user_name)
        user.delete()
    except Exception:
        print("   - User Not Found: %s" % user_name)
        pass
    print('   - Deleted User %s' % user_name)
    return True
