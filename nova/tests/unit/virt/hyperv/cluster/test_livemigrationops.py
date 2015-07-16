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

import mock

from nova.tests.unit import fake_instance
from nova.tests.unit.virt.hyperv import test_base
from nova.virt.hyperv.cluster import livemigrationops
from nova.virt.hyperv import vmutils


class LiveMigrationOpsTestCase(test_base.HyperVBaseTestCase):
    """Unit tests for the Hyper-V ClusterLiveMigrationOps class."""

    @mock.patch('nova.virt.hyperv.cluster.clusterutils.ClusterUtils')
    def setUp(self, mock_clusterutils):
        super(LiveMigrationOpsTestCase, self).setUp()
        self.context = mock.sentinel.context
        self._livemigrops = livemigrationops.ClusterLiveMigrationOps()
        self._livemigrops._livemigrutils = mock.MagicMock()
        self._livemigrops._clustutils = mock.MagicMock()

    @mock.patch('nova.virt.hyperv.vmops.VMOps.copy_vm_console_logs')
    @mock.patch('nova.virt.hyperv.vmops.VMOps.copy_vm_dvd_disks')
    def _test_live_migration(self, mock_get_vm_dvd_paths,
                             mock_copy_logs, side_effect):
        mock_instance = fake_instance.fake_instance_obj(self.context)
        mock_post_method = mock.MagicMock()
        mock_recover = mock.MagicMock()
        fake_dest = mock.sentinel.DESTINATION
        self._livemigrops._livemigrutils.live_migrate_vm.side_effect = [
            side_effect]
        if side_effect is vmutils.HyperVException:
            self.assertRaises(vmutils.HyperVException,
                              self._livemigrops.live_migration,
                              self.context, mock_instance, fake_dest,
                              mock_post_method, mock_recover, False, None)
            mock_recover.assert_called_once_with(self.context, mock_instance,
                                                 fake_dest, False)
        else:
            self._livemigrops.live_migration(context=self.context,
                                             instance_ref=mock_instance,
                                             dest=fake_dest,
                                             post_method=mock_post_method,
                                             recover_method=mock_recover)

            mock_copy_logs.assert_called_once_with(mock_instance.name,
                                                   fake_dest)
            mock_live_migr = self._livemigrops._livemigrutils.live_migrate_vm
            mock_live_migr.assert_called_once_with(mock_instance.name,
                                                   fake_dest)
            mock_post_method.assert_called_once_with(self.context, 
                mock_instance, fake_dest, False)

    def test_live_migration(self):
        self._test_live_migration(side_effect=None)

    def test_live_migration_exception(self):
        self._test_live_migration(side_effect=vmutils.HyperVException)

    @mock.patch('nova.virt.hyperv.livemigrationops.LiveMigrationOps.'
                       'live_migration')
    def test_live_migration_unclustered_dest(self,
                                             mock_parent_live_migration):
        mock_instance = fake_instance.fake_instance_obj(self.context)
        mock_post = mock.MagicMock()
        mock_recover = mock.MagicMock()
        fake_dest = mock.sentinel.DESTINATION
        self._livemigrops._clustutils.get_cluster_node_names.return_value = []

        self._livemigrops.live_migration(context=self.context,
                                         instance_ref=mock_instance,
                                         dest=fake_dest,
                                         post_method=mock_post,
                                         recover_method=mock_recover)

        mock_remove_vm = self._livemigrops._clustutils.remove_vm_from_cluster
        mock_remove_vm.assert_called_once_with(mock_instance.name)
        mock_parent_live_migration.assert_called_once_with(
            self.context, mock_instance, fake_dest, mock_post, mock_recover,
            False, None)

    def test_live_migration_clustered_dest(self):
        mock_instance = fake_instance.fake_instance_obj(self.context)
        mock_post = mock.MagicMock()
        mock_recover = mock.MagicMock()

        fake_dest = mock.sentinel.DESTINATION
        self._livemigrops._clustutils.get_vm_host.return_value = fake_dest
        self._livemigrops._clustutils.get_cluster_node_names.return_value = [
            fake_dest]

        self._livemigrops.live_migration(context=self.context,
                                         instance_ref=mock_instance,
                                         dest=fake_dest,
                                         post_method=mock_post,
                                         recover_method=mock_recover)

        mock_post.assert_called_once_with(
            self.context, mock_instance, fake_dest, False)

    @mock.patch.object(livemigrationops.ClusterLiveMigrationOps,
                       '_is_instance_clustered')
    @mock.patch('nova.virt.hyperv.livemigrationops.LiveMigrationOps.'
                'post_live_migration_at_destination')
    def test_post_live_migration_at_dest(self,
                                         mock_parent_post_live_migr_at_dest,
                                         mock_is_clustered):
        mock_instance = fake_instance.fake_instance_obj(self.context)
        mock_network_info = mock.sentinel.netinfo
        mock_block_migration = mock.sentinel.block_migr
        mock_is_clustered.return_value = False

        self._livemigrops.post_live_migration_at_destination(
            ctxt=self.context, instance_ref=mock_instance,
            network_info=mock_network_info,
            block_migration=mock_block_migration)

        mock_parent_post_live_migr_at_dest.assert_called_once_with(
            self.context, mock_instance, mock_network_info,
            mock_block_migration)
        mock_add_vm = self._livemigrops._clustutils.add_vm_to_cluster
        mock_add_vm.assert_called_once_with(mock_instance.name)
