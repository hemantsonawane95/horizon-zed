# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from copy import deepcopy  # noqa

from django.core.urlresolvers import reverse
from django import http
from mox3.mox import IsA  # noqa
import six

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

INDEX_URL = reverse('horizon:project:access_and_security:index')


class AccessAndSecurityTests(test.TestCase):
    def setUp(self):
        super(AccessAndSecurityTests, self).setUp()

    @test.create_stubs({api.network: ('security_group_list',),
                        api.base: ('is_service_enabled',),
                        quotas: ('tenant_quota_usages',)})
    def _test_index(self):
        sec_groups = self.security_groups.list()
        quota_data = self.quota_usages.first()
        quota_data['security_groups']['available'] = 10

        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(sec_groups)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).MultipleTimes() \
            .AndReturn(quota_data)

        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/access_and_security/index.html')

        # Security groups
        sec_groups_from_ctx = res.context['security_groups_table'].data
        # Context data needs to contains all items from the test data.
        self.assertItemsEqual(sec_groups_from_ctx,
                              sec_groups)
        # Sec groups in context need to be sorted by their ``name`` attribute.
        # This assertion is somewhat weak since it's only meaningful as long as
        # the sec groups in the test data are *not* sorted by name (which is
        # the case as of the time of this addition).
        self.assertTrue(
            all([sec_groups_from_ctx[i].name <= sec_groups_from_ctx[i + 1].name
                 for i in range(len(sec_groups_from_ctx) - 1)]))

    def test_index(self):
        self._test_index()


class SecurityGroupTabTests(test.TestCase):
    def setUp(self):
        super(SecurityGroupTabTests, self).setUp()

    @test.create_stubs({api.network: ('security_group_list',),
                        quotas: ('tenant_quota_usages',),
                        api.base: ('is_service_enabled',)})
    def test_create_button_attributes(self):
        sec_groups = self.security_groups.list()
        quota_data = self.quota_usages.first()
        quota_data['security_groups']['available'] = 10

        api.network.security_group_list(
            IsA(http.HttpRequest)) \
            .AndReturn(sec_groups)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)).MultipleTimes() \
            .AndReturn(quota_data)

        api.base.is_service_enabled(
            IsA(http.HttpRequest), 'network').MultipleTimes() \
            .AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL +
                              "?tab=access_security_tabs__security_groups_tab")

        security_groups = res.context['security_groups_table'].data
        self.assertItemsEqual(security_groups, self.security_groups.list())

        create_action = self.getAndAssertTableAction(res, 'security_groups',
                                                     'create')

        self.assertEqual('Create Security Group',
                         six.text_type(create_action.verbose_name))
        self.assertIsNone(create_action.policy_rules)
        self.assertEqual(set(['ajax-modal']), set(create_action.classes))

        url = 'horizon:project:access_and_security:security_groups:create'
        self.assertEqual(url, create_action.url)

    @test.create_stubs({api.network: ('security_group_list',),
                        quotas: ('tenant_quota_usages',),
                        api.base: ('is_service_enabled',)})
    def _test_create_button_disabled_when_quota_exceeded(self,
                                                         network_enabled):
        sec_groups = self.security_groups.list()
        quota_data = self.quota_usages.first()
        quota_data['security_groups']['available'] = 0

        api.network.security_group_list(
            IsA(http.HttpRequest)) \
            .AndReturn(sec_groups)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)).MultipleTimes() \
            .AndReturn(quota_data)

        api.base.is_service_enabled(
            IsA(http.HttpRequest), 'network').MultipleTimes() \
            .AndReturn(network_enabled)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL +
                              "?tab=access_security_tabs__security_groups_tab")

        security_groups = res.context['security_groups_table'].data
        self.assertItemsEqual(security_groups, self.security_groups.list())

        create_action = self.getAndAssertTableAction(res, 'security_groups',
                                                     'create')
        self.assertIn('disabled', create_action.classes,
                      'The create button should be disabled')

    def test_create_button_disabled_when_quota_exceeded_neutron_disabled(self):
        self._test_create_button_disabled_when_quota_exceeded(False)

    def test_create_button_disabled_when_quota_exceeded_neutron_enabled(self):
        self._test_create_button_disabled_when_quota_exceeded(True)
