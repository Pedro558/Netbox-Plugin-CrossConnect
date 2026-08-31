from django.test import TestCase

from dcim.choices import InterfaceTypeChoices
from dcim.models import Cable, Interface, Region, Site
from tenancy.models import Tenant, TenantGroup
from utilities.testing import create_test_device

from netbox_cross_connects.choices import CrossConnectStatusChoices
from netbox_cross_connects.models import CrossConnect
from netbox_cross_connects.tables import CrossConnectTable, RelatedCableTable


class CrossConnectTableTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region = Region.objects.create(name='Region 1', slug='region-1')
        cls.site = Site.objects.create(name='Site 1', slug='site-1', region=cls.region)
        cls.tenant_group = TenantGroup.objects.create(name='Tenant Group 1', slug='tenant-group-1')
        cls.tenant = Tenant.objects.create(name='Tenant 1', slug='tenant-1', group=cls.tenant_group)

    def test_cross_connect_table_basic_columns(self):
        table = CrossConnectTable([])

        self.assertEqual(
            table.Meta.default_columns,
            (
                'pk',
                'cross_connect_id',
                'ritm',
                'status',
                'site',
                'tenant',
                'activation_date',
                'description',
            ),
        )

    def test_cross_connect_table_renders_basic_values(self):
        cross_connect = CrossConnect.objects.create(
            cross_connect_id='ID-RJO1-00650',
            ritm='RITM0012345',
            status=CrossConnectStatusChoices.STATUS_ACTIVE,
            site=self.site,
            tenant=self.tenant,
            description='Primary path',
        )
        table = CrossConnectTable([cross_connect])
        row = next(iter(table.rows))

        self.assertIn(cross_connect.cross_connect_id, row.get_cell('cross_connect_id'))
        self.assertEqual(row.get_cell('ritm'), cross_connect.ritm)
        self.assertIn('Active', row.get_cell('status'))
        self.assertIn(self.site.name, row.get_cell('site'))
        self.assertIn(self.tenant.name, row.get_cell('tenant'))

    def test_related_cable_table_basic_columns(self):
        table = RelatedCableTable([])

        self.assertEqual(
            table.Meta.default_columns,
            (
                'cable',
                'termination_a',
                'termination_b',
                'status',
            ),
        )

    def test_related_cable_table_renders_termination_columns(self):
        device_a = create_test_device('device-a-render', site=self.site)
        device_b = create_test_device('device-b-render', site=self.site)
        interface_a = Interface.objects.create(
            device=device_a,
            name='xe-0/0/0',
            type=InterfaceTypeChoices.TYPE_10GE_FIXED,
        )
        interface_b = Interface.objects.create(
            device=device_b,
            name='xe-0/0/1',
            type=InterfaceTypeChoices.TYPE_10GE_FIXED,
        )
        cable = Cable(a_terminations=[interface_a], b_terminations=[interface_b])
        cable.save()

        table = RelatedCableTable([cable])
        row = next(iter(table.rows))

        self.assertIn('Site 1', row.get_cell('termination_a'))
        self.assertIn('device-a-render', row.get_cell('termination_a'))
        self.assertIn('xe-0/0/0', row.get_cell('termination_a'))
        self.assertIn('Site 1', row.get_cell('termination_b'))
        self.assertIn('device-b-render', row.get_cell('termination_b'))
        self.assertIn('xe-0/0/1', row.get_cell('termination_b'))
