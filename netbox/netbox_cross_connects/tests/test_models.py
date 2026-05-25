from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Region, Site
from tenancy.models import Tenant, TenantGroup

from netbox_cross_connects.choices import CrossConnectStatusChoices
from netbox_cross_connects.models import CrossConnect


class CrossConnectModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region = Region.objects.create(name='Region 1', slug='region-1')
        cls.site = Site.objects.create(name='Site 1', slug='site-1', region=cls.region)
        cls.tenant_group = TenantGroup.objects.create(name='Tenant Group 1', slug='tenant-group-1')
        cls.tenant = Tenant.objects.create(name='Tenant 1', slug='tenant-1', group=cls.tenant_group)

    def test_cross_connect_defaults(self):
        cross_connect = CrossConnect(
            cross_connect_id='ID-RJO1-00650',
            ritm='RITM0012345',
            site=self.site,
            tenant=self.tenant,
        )
        cross_connect.full_clean()

        self.assertEqual(cross_connect.status, CrossConnectStatusChoices.STATUS_ACTIVE)
        self.assertEqual(cross_connect.get_status_color(), 'green')
        self.assertEqual(str(cross_connect), 'ID-RJO1-00650')

    def test_cross_connect_id_validation(self):
        cross_connect = CrossConnect(
            cross_connect_id='invalid-id',
            ritm='RITM0012345',
            site=self.site,
            tenant=self.tenant,
        )

        with self.assertRaises(ValidationError) as context:
            cross_connect.full_clean()

        self.assertIn('cross_connect_id', context.exception.message_dict)

    def test_ritm_validation(self):
        cross_connect = CrossConnect(
            cross_connect_id='ID-RJO1-00650',
            ritm='RITM123',
            site=self.site,
            tenant=self.tenant,
        )

        with self.assertRaises(ValidationError) as context:
            cross_connect.full_clean()

        self.assertIn('ritm', context.exception.message_dict)
