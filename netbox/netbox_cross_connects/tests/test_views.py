from core.models import ObjectType
from django.test import RequestFactory, TestCase
from django.urls import reverse

from dcim.choices import InterfaceTypeChoices
from dcim.models import Cable, Interface, Region, Site
from extras.choices import CustomFieldTypeChoices
from extras.models import CustomField
from tenancy.models import Tenant, TenantGroup
from utilities.testing import create_test_device, create_test_user

from netbox_cross_connects.choices import CrossConnectStatusChoices
from netbox_cross_connects.forms import CrossConnectForm
from netbox_cross_connects.models import CrossConnect
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
        custom_field = CustomField.objects.create(
            name='cross_connect',
            type=CustomFieldTypeChoices.TYPE_OBJECT,
            related_object_type=ObjectType.objects.get_for_model(CrossConnect),
        )
        custom_field.object_types.set([ObjectType.objects.get_for_model(Cable)])
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
