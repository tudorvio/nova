# Copyright 2015 Cloudbase Solutions Srl
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Utility class for VM related operations on Hyper-V.
"""

import re
import sys

if sys.platform == 'win32':
    import wmi

from oslo_config import cfg
from oslo_log import log as logging

from nova import exception
from nova.i18n import _, _LE
from nova.virt.hyperv import vmutils

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class ClusterUtilsBase(object):

    _MSCLUSTER_NODE = 'MSCluster_Node'
    _MSCLUSTER_RES_GROUP = 'MSCluster_ResourceGroup'
    _MSCLUSTER_RES_TYPE = 'MSCluster_ResourceType'

    _CLUSTER_RUNNING = 'OK'

    _NODE_ACTIVE = 0

    _VM_BASE_NAME = 'Virtual Machine %s'
    _VM_GROUP_TYPE = 111

    _MS_CLUSTER_NAMESPACE = '//%s/root/MSCluster'

    def __init__(self, host='.'):
        if sys.platform == 'win32':
            self._init_hyperv_conn(host)

    def _init_hyperv_conn(self, host):
        self._conn = wmi.WMI(moniker=self._MS_CLUSTER_NAMESPACE % host)
        self._cluster = self._conn.MSCluster_Cluster()[0]

        #extract this node name from cluster's path
        path = self._cluster.path_()
        self._this_node = re.search(r'\\\\(.*)\\root', path,
                                    re.IGNORECASE).group(1)

    def get_node_name(self):
        return self._this_node

    def _get_cluster_nodes(self):
        return self._cluster.associators(
            wmi_result_class=self._MSCLUSTER_NODE)

    def _get_vm_groups(self):
        resources = self._cluster.associators(
            wmi_result_class=self._MSCLUSTER_RES_GROUP)
        return (r for r in resources if
                hasattr(r, 'GroupType') and
                r.GroupType == self._VM_GROUP_TYPE)


class ClusterUtils(ClusterUtilsBase):

    _LIVE_MIGRATION_TYPE = 4

    _IGNORE_LOCKED = 1

    _DESTROY_GROUP = 1

    _FAILBACK_TRUE = 1
    _FAILBACK_WINDOW_MIN = 0
    _FAILBACK_WINDOW_MAX = 23

    def _lookup_vm_group_check(self, vm_name):
        vm = self._lookup_vm_group(vm_name)
        if not vm:
            raise exception.NotFound(_('VM not found: %s') % vm_name)
        return vm

    def _lookup_vm_group(self, vm_name):
        return self._lookup_res(self._conn.MSCluster_ResourceGroup, vm_name)

    def _lookup_vm_check(self, vm_name):
        vm = self._lookup_vm(vm_name)
        if not vm:
            raise exception.NotFound(_('VM not found: %s') % vm_name)
        return vm

    def _lookup_vm(self, vm_name):
        vm_name = self._VM_BASE_NAME % vm_name
        return self._lookup_res(self._conn.MSCluster_Resource, vm_name)

    def _lookup_res(self, resource_source, res_name):
        res = resource_source(Name=res_name)
        n = len(res)
        if n == 0:
            return None
        elif n > 1:
            raise vmutils.HyperVException(_('Duplicate resource name '
                                            'found: %s') % res_name)
        else:
            return res[0]

    def get_cluster_node_names(self):
        nodes = self._get_cluster_nodes()
        return [n.Name for n in nodes]

    def get_vm_host(self, vm_name):
        return self._lookup_vm_group_check(vm_name).OwnerNode

    def add_vm_to_cluster(self, vm_name):
        self._cluster.AddVirtualMachine(vm_name)

        vm_group = self._lookup_vm_group_check(vm_name)
        vm_group.PersistentState = True
        vm_group.AutoFailbackType = self._FAILBACK_TRUE
        vm_group.FailbackWindowStart = self._FAILBACK_WINDOW_MIN
        vm_group.FailbackWindowEnd = self._FAILBACK_WINDOW_MAX
        vm_group.Put_()

    def remove_vm_from_cluster(self, vm_name):
        vm = self._lookup_vm_group(vm_name)
        if vm:
            # or DestroyGroup?
            vm.DestroyGroup(self._DESTROY_GROUP)

    def vm_exists(self, vm_name):
        return self._lookup_vm(vm_name) is not None

    def live_migrate_vm(self, vm_name, new_host):
        self._migrate_vm(vm_name, new_host, self._LIVE_MIGRATION_TYPE)

    def _migrate_vm(self, vm_name, new_host, migration_type):
        vm_group = self._lookup_vm_group_check(vm_name)
        try:
            vm_group.MoveToNewNodeParams(self._IGNORE_LOCKED, new_host,
                                         [migration_type])
        except Exception as e:
            LOG.error(_LE('Exception during cluster live migration of %s '
                          'to %s: %s'), vm_name, new_host, e)
