from django.test import TestCase

from dcim.models import Region, Site
from tenancy.models import Tenant, TenantGroup
from utilities.forms.fields import CommentField

from netbox_cross_connects.choices import CrossConnectStatusChoices
from netbox_cross_connects.forms import CrossConnectFilterForm, CrossConnectForm, CrossConnectImportForm


class CrossConnectFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region = Region.objects.create(name='Region 1', slug='region-1')
        cls.site = Site.objects.create(name='Site 1', slug='site-1', region=cls.region)
        cls.tenant_group = TenantGroup.objects.create(name='Tenant Group 1', slug='tenant-group-1')
        cls.tenant = Tenant.objects.create(name='Tenant 1', slug='tenant-1', group=cls.tenant_group)

    def test_cross_connect_form_fields_match_phase_5_scope(self):
        form = CrossConnectForm()
        expected_fields = [
            'cross_connect_id',
            'ritm',
            'status',
            'site',
            'tenant',
            'activation_date',
            'description',
            'comments',
            'tags',
        ]

        self.assertEqual(list(form.Meta.fields), expected_fields)
        self.assertEqual(list(form.fields)[:len(expected_fields)], expected_fields)
        self.assertIsInstance(form.fields['comments'], CommentField)
        self.assertNotIn('owner', form.fields)
        self.assertNotIn('owner_id', form.fields)
        self.assertNotIn('owner_group_id', form.fields)

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


class CrossConnectFilterFormTestCase(TestCase):
    def test_filter_form_fields_match_phase_5_scope(self):
        form = CrossConnectFilterForm()

        self.assertIn('q', form.fields)
        self.assertIn('status', form.fields)
        self.assertIn('site_id', form.fields)
        self.assertIn('tenant_id', form.fields)
        self.assertIn('tag', form.fields)
        self.assertNotIn('owner', form.fields)
        self.assertNotIn('owner_id', form.fields)
        self.assertNotIn('owner_group_id', form.fields)


class CrossConnectImportFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region = Region.objects.create(name='Region 1', slug='region-1')
        cls.site = Site.objects.create(name='Site 1', slug='site-1', region=cls.region)
        cls.tenant_group = TenantGroup.objects.create(name='Tenant Group 1', slug='tenant-group-1')
        cls.tenant = Tenant.objects.create(name='Tenant 1', slug='tenant-1', group=cls.tenant_group)

    def test_import_form_fields_match_phase_5_scope(self):
        form = CrossConnectImportForm()
        expected_fields = [
            'cross_connect_id',
            'ritm',
            'status',
            'site',
            'tenant',
            'activation_date',
            'last_known_path',
            'description',
            'comments',
            'tags',
        ]

        self.assertEqual(list(form.Meta.fields), expected_fields)
        self.assertEqual(list(form.fields)[:len(expected_fields)], expected_fields)
        self.assertNotIn('owner', form.fields)
        self.assertNotIn('owner_id', form.fields)
        self.assertNotIn('owner_group_id', form.fields)

    def test_import_form_is_valid(self):
        form = CrossConnectImportForm(data={
            'cross_connect_id': 'ID-RJO1-00654',
            'ritm': 'RITM0012349',
            'status': CrossConnectStatusChoices.STATUS_ACTIVE,
            'site': self.site.name,
            'tenant': self.tenant.name,
            'activation_date': '2026-05-25',
            'last_known_path': 'Panel A > Panel B',
            'description': 'Imported cross connect',
            'comments': 'Imported by tests',
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_import_form_rejects_unknown_site(self):
        form = CrossConnectImportForm(data={
            'cross_connect_id': 'ID-RJO1-00655',
            'ritm': 'RITM0012350',
            'status': CrossConnectStatusChoices.STATUS_ACTIVE,
            'site': 'Unknown Site',
            'tenant': self.tenant.name,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('site', form.errors)
