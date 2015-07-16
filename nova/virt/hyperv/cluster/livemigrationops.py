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
Management class for cluster live migration VM operations.
"""

from oslo_log import log as logging
from oslo_utils import excutils

from nova import exception
from nova.virt.hyperv.cluster import clusterutils
from nova.virt.hyperv import livemigrationops

LOG = logging.getLogger(__name__)


class ClusterLiveMigrationOps(livemigrationops.LiveMigrationOps):
    def __init__(self):
        super(ClusterLiveMigrationOps, self).__init__()
        self._clustutils = clusterutils.ClusterUtils()

    def _is_instance_clustered(self, instance_name):
        return self._clustutils.vm_exists(instance_name)

    def live_migration(self, context, instance_ref, dest, post_method,
                       recover_method, block_migration=False,
                       migrate_data=None):
        instance_name = instance_ref.name
        clustered = self._is_instance_clustered(instance_name)

        # simple live migration must be performed if:
        # destination not in the same cluster.
        # or instance is not clustered.
        if (dest not in self._clustutils.get_cluster_node_names()
                or not clustered):
            if clustered:
                # uncluster the VM before classic live migration.
                self._clustutils.remove_vm_from_cluster(instance_name)

            super(ClusterLiveMigrationOps, self).live_migration(
                context, instance_ref, dest, post_method, recover_method,
                block_migration, migrate_data)
            return
        elif self._clustutils.get_vm_host(instance_name) == dest:
            # VM is already migrated. Do nothing.
            # this can happen when the VM has been failovered.
            post_method(context, instance_ref, dest, block_migration)
            return

        # destination is in the same cluster.
        # perform a clustered live migration.
        # refactor this, in order to avoid duplicate code.
        LOG.debug("Performing clustered live_migration", instance=instance_ref)
        try:
            self._clustutils.live_migrate_vm(instance_name, dest)
        except exception.NotFound:
            with excutils.save_and_reraise_exception():
                LOG.debug("Calling live migration recover_method "
                          "for instance: %s", instance_name)
                recover_method(context, instance_ref, dest, block_migration)

        LOG.debug("Calling live migration post_method for instance: %s",
                  instance_name)
        post_method(context, instance_ref, dest, block_migration)

    def post_live_migration_at_destination(self, ctxt, instance_ref,
                                           network_info, block_migration):
        super(ClusterLiveMigrationOps,
              self).post_live_migration_at_destination(
            ctxt, instance_ref, network_info, block_migration)

        if not self._is_instance_clustered(instance_ref.name):
            self._clustutils.add_vm_to_cluster(instance_ref.name)
