from core.models import ObjectType
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase
from django.urls import reverse

from dcim.choices import InterfaceTypeChoices, PortTypeChoices
from dcim.models import Cable, FrontPort, Interface, PortMapping, RearPort, Region, Site
from extras.choices import CustomFieldTypeChoices
from extras.models import CustomField
from tenancy.models import Tenant, TenantGroup
from utilities.testing import create_test_device, create_test_user

from netbox_cross_connects.choices import CrossConnectStatusChoices
from netbox_cross_connects.forms import CrossConnectForm, CrossConnectImportForm
from netbox_cross_connects.models import CrossConnect
from netbox_cross_connects.tables import RelatedCableTable
from netbox_cross_connects.views import CrossConnectView


class CrossConnectViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.region = Region.objects.create(name='Region 1', slug='region-1')
        cls.site = Site.objects.create(name='Site 1', slug='site-1', region=cls.region)
        cls.tenant_group = TenantGroup.objects.create(name='Tenant Group 1', slug='tenant-group-1')
        cls.tenant = Tenant.objects.create(name='Tenant 1', slug='tenant-1', group=cls.tenant_group)
        cls.user = create_test_user('crossconnect-user', permissions=('dcim.view_cable',))

    def _create_related_cables_custom_field(self):
        custom_field = CustomField.objects.create(
            name='cross_connect',
            type=CustomFieldTypeChoices.TYPE_OBJECT,
            related_object_type=ObjectType.objects.get_for_model(CrossConnect),
        )
        custom_field.object_types.set([ObjectType.objects.get_for_model(Cable)])
        return custom_field

    def test_cross_connect_form_is_valid(self):
        form = CrossConnectForm(data={
            'cross_connect_id': 'ID-RJO1-00653',
            'ritm': 'RITM0012348',
            'status': CrossConnectStatusChoices.STATUS_ACTIVE,
            'site': self.site.pk,
            'tenant': self.tenant.pk,
            'activation_date': '2026-05-24',
            'description': 'Cross connect X',
            'comments': 'Created by tests',
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_cross_connect_import_form_is_valid(self):
        form = CrossConnectImportForm(data={
            'cross_connect_id': 'ID-RJO1-00654',
            'ritm': 'RITM0012349',
            'status': CrossConnectStatusChoices.STATUS_ACTIVE,
            'site': self.site.name,
            'tenant': self.tenant.name,
            'activation_date': '2026-05-25',
            'last_known_path': 'Panel A > Panel B',
            'description': 'Imported cross connect',
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_cross_connect_ui_routes(self):
        cross_connect = CrossConnect.objects.create(
            cross_connect_id='ID-RJO1-00652',
            ritm='RITM0012347',
            status=CrossConnectStatusChoices.STATUS_ACTIVE,
            site=self.site,
            tenant=self.tenant,
        )

        self.assertEqual(
            reverse('plugins:netbox_cross_connects:crossconnect_list'),
            '/plugins/cross-connects/cross-connects/',
        )
        self.assertEqual(
            reverse('plugins:netbox_cross_connects:crossconnect_add'),
            '/plugins/cross-connects/cross-connects/add/',
        )
        self.assertEqual(
            reverse('plugins:netbox_cross_connects:crossconnect_bulk_import'),
            '/plugins/cross-connects/cross-connects/import/',
        )
        self.assertEqual(
            reverse('plugins:netbox_cross_connects:crossconnect', kwargs={'pk': cross_connect.pk}),
            f'/plugins/cross-connects/cross-connects/{cross_connect.pk}/',
        )
        self.assertEqual(
            reverse('plugins-api:netbox_cross_connects-api:crossconnect-list'),
            '/api/plugins/cross-connects/cross-connects/',
        )

    def test_detail_view_includes_related_cables_table(self):
        cross_connect = CrossConnect.objects.create(
            cross_connect_id='ID-RJO1-00650',
            ritm='RITM0012345',
            status=CrossConnectStatusChoices.STATUS_ACTIVE,
            site=self.site,
            tenant=self.tenant,
        )
        custom_field = self._create_related_cables_custom_field()
        device_a = create_test_device('device-a', site=self.site)
        device_b = create_test_device('device-b', site=self.site)
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
        cable = Cable(
            a_terminations=[interface_a],
            b_terminations=[interface_b],
            custom_field_data={'cross_connect': cross_connect.pk},
        )
        cable.save()

        request = self.factory.get('/')
        request.user = self.user

        view = CrossConnectView()
        context = view.get_extra_context(request, cross_connect)
        table = context['related_cables_table']

        self.assertEqual(context['related_cables_custom_field'], custom_field)
        self.assertEqual(next(iter(table.rows)).record.pk, cable.pk)

    def test_related_cable_table_renders_termination_a_and_b_columns(self):
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

    def test_detail_view_resolves_native_trace_for_complete_patch_panel_path(self):
        self.user.user_permissions.add(Permission.objects.get(codename='view_interface'))

        cross_connect = CrossConnect.objects.create(
            cross_connect_id='ID-RJO1-00660',
            ritm='RITM0012360',
            status=CrossConnectStatusChoices.STATUS_ACTIVE,
            site=self.site,
            tenant=self.tenant,
        )
        self._create_related_cables_custom_field()

        device_a = create_test_device('trace-device-a', site=self.site)
        device_b = create_test_device('trace-device-b', site=self.site)
        patch_panel_1 = create_test_device('patch-panel-1', site=self.site)
        patch_panel_2 = create_test_device('patch-panel-2', site=self.site)

        interface_a = Interface.objects.create(
            device=device_a,
            name='xe-0/0/0',
            type=InterfaceTypeChoices.TYPE_10GE_FIXED,
        )
        interface_z = Interface.objects.create(
            device=device_b,
            name='xe-0/0/1',
            type=InterfaceTypeChoices.TYPE_10GE_FIXED,
        )
        front_port_1 = FrontPort.objects.create(device=patch_panel_1, name='FP1', type=PortTypeChoices.TYPE_8P8C)
        rear_port_1 = RearPort.objects.create(device=patch_panel_1, name='RP1', type=PortTypeChoices.TYPE_8P8C)
        front_port_2 = FrontPort.objects.create(device=patch_panel_2, name='FP1', type=PortTypeChoices.TYPE_8P8C)
        rear_port_2 = RearPort.objects.create(device=patch_panel_2, name='RP1', type=PortTypeChoices.TYPE_8P8C)
        PortMapping.objects.create(front_port=front_port_1, rear_port=rear_port_1)
        PortMapping.objects.create(front_port=front_port_2, rear_port=rear_port_2)

        Cable(
            a_terminations=[interface_a],
            b_terminations=[front_port_1],
            custom_field_data={'cross_connect': cross_connect.pk},
        ).save()
        Cable(
            a_terminations=[rear_port_1],
            b_terminations=[rear_port_2],
            custom_field_data={'cross_connect': cross_connect.pk},
        ).save()
        Cable(
            a_terminations=[front_port_2],
            b_terminations=[interface_z],
            custom_field_data={'cross_connect': cross_connect.pk},
        ).save()

        request = self.factory.get('/')
        request.user = self.user

        context = CrossConnectView().get_extra_context(request, cross_connect)

        self.assertEqual(context['trace_status'], 'ready')
        self.assertEqual(context['trace_origin_interface'], interface_a)
        self.assertEqual(context['trace_destination_interface'], interface_z)
        self.assertEqual(
            context['trace_url'],
            f"{reverse('dcim:interface_trace', kwargs={'pk': interface_a.pk})}?cross_connect={cross_connect.pk}",
        )
        self.assertIn(reverse('dcim-api:interface-trace', kwargs={'pk': interface_a.pk}), context['trace_svg_url'])

    def test_native_trace_view_shows_cross_connect_subtitle(self):
        self.user.user_permissions.add(Permission.objects.get(codename='view_interface'))
        self.client.force_login(self.user)

        cross_connect = CrossConnect.objects.create(
            cross_connect_id='ID-RJO1-00663',
            ritm='RITM0012363',
            status=CrossConnectStatusChoices.STATUS_ACTIVE,
            site=self.site,
            tenant=self.tenant,
        )

        device_a = create_test_device('trace-header-device-a', site=self.site)
        device_b = create_test_device('trace-header-device-b', site=self.site)
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
        Cable(a_terminations=[interface_a], b_terminations=[interface_b]).save()

        response = self.client.get(
            f"{reverse('dcim:interface_trace', kwargs={'pk': interface_a.pk})}?cross_connect={cross_connect.pk}"
        )

        self.assertContains(response, cross_connect.cross_connect_id)

    def test_bulk_import_view_creates_cross_connect(self):
        user = create_test_user('crossconnect-import-user', permissions=('netbox_cross_connects.add_crossconnect',))
        self.client.force_login(user)

        response = self.client.post(
            reverse('plugins:netbox_cross_connects:crossconnect_bulk_import'),
            {
                'data': '\n'.join((
                    'cross_connect_id,ritm,status,site,tenant,activation_date,last_known_path,description',
                    'ID-RJO1-00655,RITM0012350,active,Site 1,Tenant 1,2026-05-26,Patch panel A > Patch panel B,Imported from CSV',
                )),
                'format': 'csv',
                'csv_delimiter': 'auto',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/plugins/cross-connects/cross-connects/?modified_by_request=' + response.headers['X-Request-ID'])
        self.assertTrue(CrossConnect.objects.filter(cross_connect_id='ID-RJO1-00655').exists())

    def test_detail_view_reports_ambiguous_trace_direction_when_both_endpoints_are_a_side(self):
        self.user.user_permissions.add(Permission.objects.get(codename='view_interface'))

        cross_connect = CrossConnect.objects.create(
            cross_connect_id='ID-RJO1-00661',
            ritm='RITM0012361',
            status=CrossConnectStatusChoices.STATUS_ACTIVE,
            site=self.site,
            tenant=self.tenant,
        )
        self._create_related_cables_custom_field()

        device_a = create_test_device('ambiguous-device-a', site=self.site)
        device_z = create_test_device('ambiguous-device-z', site=self.site)
        patch_panel = create_test_device('ambiguous-patch-panel', site=self.site)

        interface_a = Interface.objects.create(
            device=device_a,
            name='xe-0/0/0',
            type=InterfaceTypeChoices.TYPE_10GE_FIXED,
        )
        interface_z = Interface.objects.create(
            device=device_z,
            name='xe-0/0/1',
            type=InterfaceTypeChoices.TYPE_10GE_FIXED,
        )
        front_port = FrontPort.objects.create(device=patch_panel, name='FP1', type=PortTypeChoices.TYPE_8P8C)
        rear_port = RearPort.objects.create(device=patch_panel, name='RP1', type=PortTypeChoices.TYPE_8P8C)
        PortMapping.objects.create(front_port=front_port, rear_port=rear_port)

        Cable(
            a_terminations=[interface_a],
            b_terminations=[rear_port],
            custom_field_data={'cross_connect': cross_connect.pk},
        ).save()
        Cable(
            a_terminations=[interface_z],
            b_terminations=[front_port],
            custom_field_data={'cross_connect': cross_connect.pk},
        ).save()

        request = self.factory.get('/')
        request.user = self.user

        context = CrossConnectView().get_extra_context(request, cross_connect)

        self.assertEqual(context['trace_status'], 'ambiguous')
        self.assertIsNone(context['trace_url'])
        self.assertCountEqual(
            [link['interface'] for link in context['trace_links']],
            [interface_a, interface_z],
        )

    def test_detail_view_rejects_trace_when_related_cables_have_more_than_two_endpoint_interfaces(self):
        self.user.user_permissions.add(Permission.objects.get(codename='view_interface'))

        cross_connect = CrossConnect.objects.create(
            cross_connect_id='ID-RJO1-00662',
            ritm='RITM0012362',
            status=CrossConnectStatusChoices.STATUS_ACTIVE,
            site=self.site,
            tenant=self.tenant,
        )
        self._create_related_cables_custom_field()

        device_a = create_test_device('invalid-device-a', site=self.site)
        device_b = create_test_device('invalid-device-b', site=self.site)
        device_c = create_test_device('invalid-device-c', site=self.site)

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
        interface_c = Interface.objects.create(
            device=device_c,
            name='xe-0/0/2',
            type=InterfaceTypeChoices.TYPE_10GE_FIXED,
        )

        Cable(
            a_terminations=[interface_a],
            b_terminations=[interface_b],
            custom_field_data={'cross_connect': cross_connect.pk},
        ).save()
        Cable(
            a_terminations=[interface_b],
            b_terminations=[interface_c],
            custom_field_data={'cross_connect': cross_connect.pk},
        ).save()

        request = self.factory.get('/')
        request.user = self.user

        context = CrossConnectView().get_extra_context(request, cross_connect)

        self.assertEqual(context['trace_status'], 'unavailable')
        self.assertIsNone(context['trace_url'])
        self.assertIn('exactly two endpoint interfaces', context['trace_message'])

    def test_detail_view_reports_missing_related_cables_custom_field(self):
        cross_connect = CrossConnect.objects.create(
            cross_connect_id='ID-RJO1-00651',
            ritm='RITM0012346',
            status=CrossConnectStatusChoices.STATUS_ACTIVE,
            site=self.site,
            tenant=self.tenant,
        )

        request = self.factory.get('/')
        request.user = self.user

        view = CrossConnectView()
        context = view.get_extra_context(request, cross_connect)

        self.assertIsNone(context['related_cables_custom_field'])
        self.assertIsNone(context['related_cables_table'])
