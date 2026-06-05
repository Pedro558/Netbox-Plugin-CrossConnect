from django.urls import reverse
from rest_framework import status

from dcim.models import Region, Site
from tenancy.models import Tenant, TenantGroup
from utilities.testing import APITestCase

from netbox_cross_connects.choices import CrossConnectStatusChoices
from netbox_cross_connects.models import CrossConnect


class CrossConnectAPITestCase(APITestCase):
    model = CrossConnect
    user_permissions = ()

    @classmethod
    def setUpTestData(cls):
        cls.region = Region.objects.create(name='Region 1', slug='region-1')
        cls.sites = (
            Site.objects.create(name='Site 1', slug='site-1', region=cls.region),
            Site.objects.create(name='Site 2', slug='site-2', region=cls.region),
        )
        cls.tenant_group = TenantGroup.objects.create(name='Tenant Group 1', slug='tenant-group-1')
        cls.tenants = (
            Tenant.objects.create(name='Tenant 1', slug='tenant-1', group=cls.tenant_group),
            Tenant.objects.create(name='Tenant 2', slug='tenant-2', group=cls.tenant_group),
        )

        cls.cross_connects = (
            CrossConnect.objects.create(
                cross_connect_id='ID-RJO1-00650',
                ritm='RITM0012345',
                status=CrossConnectStatusChoices.STATUS_ACTIVE,
                site=cls.sites[0],
                tenant=cls.tenants[0],
                activation_date='2026-05-20',
                last_known_path='Device A xe-0/0/0 > Device B xe-0/0/1',
                description='Primary path',
                comments='Fiber handoff in room A',
            ),
            CrossConnect.objects.create(
                cross_connect_id='ID-RJO1-00651',
                ritm='RITM0012346',
                status=CrossConnectStatusChoices.STATUS_PLANNED,
                site=cls.sites[1],
                tenant=cls.tenants[1],
                description='Secondary path',
            ),
            CrossConnect.objects.create(
                cross_connect_id='ID-RJO1-00652',
                ritm='RITM0012347',
                status=CrossConnectStatusChoices.STATUS_DECOMMISSIONING,
                site=cls.sites[0],
                tenant=cls.tenants[1],
                description='Retiring path',
            ),
        )

    def _get_detail_url(self, instance):
        return reverse('plugins-api:netbox_cross_connects-api:crossconnect-detail', kwargs={'pk': instance.pk})

    def _get_list_url(self):
        return reverse('plugins-api:netbox_cross_connects-api:crossconnect-list')

    def _add_permission(self, action):
        self.add_permissions(f'netbox_cross_connects.{action}_crossconnect')

    def _assert_count(self, query, expected_count):
        response = self.client.get(f'{self._get_list_url()}?{query}', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], expected_count)

    def test_list_endpoint(self):
        self._add_permission('view')

        response = self.client.get(self._get_list_url(), **self.header)

        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['cross_connect_id'], 'ID-RJO1-00650')

    def test_detail_endpoint(self):
        self._add_permission('view')

        response = self.client.get(self._get_detail_url(self.cross_connects[0]), **self.header)

        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['cross_connect_id'], 'ID-RJO1-00650')
        self.assertEqual(response.data['ritm'], 'RITM0012345')
        self.assertEqual(response.data['status']['value'], CrossConnectStatusChoices.STATUS_ACTIVE)
        self.assertEqual(response.data['site']['id'], self.sites[0].pk)
        self.assertEqual(response.data['tenant']['id'], self.tenants[0].pk)
        self.assertEqual(response.data['activation_date'], '2026-05-20')
        self.assertEqual(response.data['last_known_path'], 'Device A xe-0/0/0 > Device B xe-0/0/1')
        self.assertEqual(response.data['description'], 'Primary path')
        self.assertEqual(response.data['comments'], 'Fiber handoff in room A')
        self.assertIn('url', response.data)
        self.assertIn('display_url', response.data)
        self.assertIn('display', response.data)
        self.assertIn('tags', response.data)
        self.assertIn('custom_fields', response.data)
        self.assertIn('created', response.data)
        self.assertIn('last_updated', response.data)

    def test_create_endpoint(self):
        self._add_permission('add')
        data = {
            'cross_connect_id': 'ID-RJO1-00653',
            'ritm': 'RITM0012348',
            'status': CrossConnectStatusChoices.STATUS_OFFLINE,
            'site': self.sites[0].pk,
            'tenant': self.tenants[1].pk,
            'activation_date': '2026-05-21',
            'last_known_path': 'Panel A > Panel B',
            'description': 'Created through API',
            'comments': 'API create test',
        }

        response = self.client.post(self._get_list_url(), data, format='json', **self.header)

        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        cross_connect = CrossConnect.objects.get(pk=response.data['id'])
        self.assertEqual(cross_connect.cross_connect_id, data['cross_connect_id'])
        self.assertEqual(cross_connect.ritm, data['ritm'])
        self.assertEqual(cross_connect.status, data['status'])
        self.assertEqual(cross_connect.site, self.sites[0])
        self.assertEqual(cross_connect.tenant, self.tenants[1])
        self.assertEqual(str(cross_connect.activation_date), data['activation_date'])
        self.assertEqual(cross_connect.last_known_path, data['last_known_path'])
        self.assertEqual(cross_connect.description, data['description'])
        self.assertEqual(cross_connect.comments, data['comments'])

    def test_update_endpoint(self):
        self._add_permission('change')
        data = {
            'status': CrossConnectStatusChoices.STATUS_OFFLINE,
            'site': self.sites[1].pk,
            'tenant': self.tenants[1].pk,
            'description': 'Updated through API',
        }

        response = self.client.patch(self._get_detail_url(self.cross_connects[0]), data, format='json', **self.header)

        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.cross_connects[0].refresh_from_db()
        self.assertEqual(self.cross_connects[0].status, data['status'])
        self.assertEqual(self.cross_connects[0].site, self.sites[1])
        self.assertEqual(self.cross_connects[0].tenant, self.tenants[1])
        self.assertEqual(self.cross_connects[0].description, data['description'])

    def test_delete_endpoint(self):
        self._add_permission('delete')

        response = self.client.delete(self._get_detail_url(self.cross_connects[0]), **self.header)

        self.assertHttpStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CrossConnect.objects.filter(pk=self.cross_connects[0].pk).exists())

    def test_filter_by_status(self):
        self._add_permission('view')
        self._assert_count(f'status={CrossConnectStatusChoices.STATUS_ACTIVE}', 1)
        self._assert_count(
            f'status={CrossConnectStatusChoices.STATUS_ACTIVE}&status={CrossConnectStatusChoices.STATUS_PLANNED}',
            2,
        )

    def test_filter_by_site_slug(self):
        self._add_permission('view')
        self._assert_count('site=site-1', 2)
        self._assert_count('site=site-2', 1)

    def test_filter_by_site_id(self):
        self._add_permission('view')
        self._assert_count(f'site_id={self.sites[0].pk}', 2)
        self._assert_count(f'site_id={self.sites[1].pk}', 1)

    def test_filter_by_tenant_slug(self):
        self._add_permission('view')
        self._assert_count('tenant=tenant-1', 1)
        self._assert_count('tenant=tenant-2', 2)

    def test_filter_by_tenant_id(self):
        self._add_permission('view')
        self._assert_count(f'tenant_id={self.tenants[0].pk}', 1)
        self._assert_count(f'tenant_id={self.tenants[1].pk}', 2)
