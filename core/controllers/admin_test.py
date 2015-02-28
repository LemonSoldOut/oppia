# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the admin page."""

__author__ = 'Sean Lip'

from core.controllers import editor
from core.controllers import pages
from core.domain import config_domain
from core.tests import test_utils
import feconf


SITE_NAME = 'sitename.org'


class AdminIntegrationTest(test_utils.GenericTestBase):

    def setUp(self):
        """Complete the signup process for self.ADMIN_EMAIL."""
        super(AdminIntegrationTest, self).setUp()
        self.signup(self.ADMIN_EMAIL, self.ADMIN_USERNAME)
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)

    def test_admin_page(self):
        """Test that the admin page shows the expected sections."""
        self.login(self.ADMIN_EMAIL, is_super_admin=True)
        response = self.testapp.get('/admin')
        self.assertEqual(response.status_int, 200)
        response.mustcontain(
            'Performance Counters',
            'Total processing time for all JSON responses',
            'Configuration',
            'Reload a single exploration',
            'three_balls')

        self.logout()

    def test_admin_page_rights(self):
        """Test access rights to the admin page."""

        response = self.testapp.get('/admin')
        self.assertEqual(response.status_int, 302)

        # Login as a non-admin.
        self.login(self.EDITOR_EMAIL)
        response = self.testapp.get('/admin', expect_errors=True)
        self.assertEqual(response.status_int, 401)
        self.logout()

        # Login as an admin.
        self.login(self.ADMIN_EMAIL, is_super_admin=True)
        response = self.testapp.get('/admin')
        self.assertEqual(response.status_int, 200)
        self.logout()

    def test_change_configuration_property(self):
        """Test that configuration properties can be changed."""

        TEST_STRING = self.UNICODE_TEST_STRING

        self.login(self.ADMIN_EMAIL, is_super_admin=True)
        response = self.testapp.get('/admin')
        csrf_token = self.get_csrf_token_from_response(response)

        response_dict = self.get_json('/adminhandler')
        response_config_properties = response_dict['config_properties']
        self.assertDictContainsSubset({
            'value': ''
        }, response_config_properties[editor.MODERATOR_REQUEST_FORUM_URL.name])

        payload = {
            'action': 'save_config_properties',
            'new_config_property_values': {
                editor.MODERATOR_REQUEST_FORUM_URL.name: TEST_STRING
            }
        }
        self.post_json('/adminhandler', payload, csrf_token)

        response_dict = self.get_json('/adminhandler')
        response_config_properties = response_dict['config_properties']
        self.assertDictContainsSubset({
            'value': TEST_STRING
        }, response_config_properties[editor.MODERATOR_REQUEST_FORUM_URL.name])

        self.logout()

    def test_change_about_page_config_property(self):
        """Test that the correct variables show up on the about page."""
        # Navigate to the about page. The site name is not set.
        response = self.testapp.get('/about')
        self.assertIn('SITE_NAME', response.body)
        self.assertNotIn(SITE_NAME, response.body)

        self.login(self.ADMIN_EMAIL, is_super_admin=True)
        response = self.testapp.get('/admin')
        csrf_token = self.get_csrf_token_from_response(response)
        self.post_json('/adminhandler', {
            'action': 'save_config_properties',
            'new_config_property_values': {
                pages.SITE_NAME.name: SITE_NAME
            }
        }, csrf_token)
        self.logout()

        # Navigate to the splash page. The site name is set.
        response = self.testapp.get('/about')
        self.assertNotIn('SITE_NAME', response.body)
        self.assertIn(SITE_NAME, response.body)

    def test_change_rights(self):
        """Test that the correct role indicators show up on app pages."""

        BOTH_MODERATOR_AND_ADMIN_EMAIL = 'moderator.and.admin@example.com'

        self.signup(self.MODERATOR_EMAIL, self.MODERATOR_USERNAME)
        self.signup('superadmin@example.com', 'superadm1n')
        self.signup(BOTH_MODERATOR_AND_ADMIN_EMAIL, 'moderatorandadm1n')

        # Navigate to any page. The role is not set.
        self.testapp.get('/').mustcontain(no=['/moderator', '/admin'])

        # Log in as a superadmin. This gives access to /admin.
        self.login('superadmin@example.com', is_super_admin=True)
        self.testapp.get('/').mustcontain('/admin', no=['/moderator'])

        # Add a moderator, an admin, and a person with both roles, then log
        # out.
        response = self.testapp.get('/admin')
        csrf_token = self.get_csrf_token_from_response(response)
        self.post_json('/adminhandler', {
            'action': 'save_config_properties',
            'new_config_property_values': {
                config_domain.ADMIN_EMAILS.name: [
                    self.ADMIN_EMAIL, BOTH_MODERATOR_AND_ADMIN_EMAIL],
                config_domain.MODERATOR_EMAILS.name: [
                    self.MODERATOR_EMAIL, BOTH_MODERATOR_AND_ADMIN_EMAIL],
            }
        }, csrf_token)
        self.logout()

        # Log in as a moderator.
        self.login(self.MODERATOR_EMAIL)
        self.testapp.get(feconf.GALLERY_URL).mustcontain(
            '/moderator', no=['/admin'])
        self.logout()

        # Log in as an admin.
        self.login(self.ADMIN_EMAIL)
        self.testapp.get(feconf.GALLERY_URL).mustcontain(
            '/moderator', no=['/admin'])
        self.logout()

        # Log in as a both-moderator-and-admin. Only '(Admin)' is shown in the
        # navbar.
        self.login(BOTH_MODERATOR_AND_ADMIN_EMAIL)
        self.testapp.get(feconf.GALLERY_URL).mustcontain(
             '/moderator', no=['/admin'])
        self.logout()
