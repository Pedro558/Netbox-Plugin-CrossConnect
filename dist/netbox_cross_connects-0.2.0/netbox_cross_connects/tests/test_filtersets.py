from django.test import TestCase

from dcim.models import Region, Site
from tenancy.models import Tenant, TenantGroup
from utilities.testing import ChangeLoggedFilterSetTests

from netbox_cross_connects.choices import CrossConnectStatusChoices
from netbox_cross_connects.filtersets import CrossConnectFilterSet
from netbox_cross_connects.models import CrossConnect


class CrossConnectFilterSetTestCase(TestCase, ChangeLoggedFilterSetTests):
    queryset = CrossConnect.objects.all()
    filterset = CrossConnectFilterSet

    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(name='Region 1', slug='region-1')
        site1 = Site.objects.create(name='Site 1', slug='site-1', region=region)
        site2 = Site.objects.create(name='Site 2', slug='site-2', region=region)
        tenant_group = TenantGroup.objects.create(name='Tenant Group 1', slug='tenant-group-1')
        tenant1 = Tenant.objects.create(name='Tenant 1', slug='tenant-1', group=tenant_group)
        tenant2 = Tenant.objects.create(name='Tenant 2', slug='tenant-2', group=tenant_group)

        CrossConnect.objects.bulk_create((
            CrossConnect(
                cross_connect_id='ID-RJO1-00650',
                ritm='RITM0012345',
                status=CrossConnectStatusChoices.STATUS_ACTIVE,
                site=site1,
                tenant=tenant1,
                last_known_path='Patch panel A > Patch panel B',
                description='Primary path',
                comments='Fiber handoff in room A',
            ),
            CrossConnect(
                cross_connect_id='ID-RJO1-00651',
                ritm='RITM0012346',
                status=CrossConnectStatusChoices.STATUS_PLANNED,
                site=site2,
                tenant=tenant2,
                last_known_path='Patch panel C > Patch panel D',
                description='Secondary path',
                comments='Waiting on provider',
            ),
            CrossConnect(
                cross_connect_id='ID-RJO1-00652',
                ritm='RITM0012347',
                status=CrossConnectStatusChoices.STATUS_DECOMMISSIONING,
                site=site1,
                tenant=tenant2,
                last_known_path='Patch panel E > Patch panel F',
                description='Retiring path',
                comments='Pending removal',
            ),
        ))

    def test_q_matches_cross_connect_id(self):
        self.assertEqual(self.filterset({'q': '00650'}, self.queryset).qs.count(), 1)

    def test_q_matches_ritm(self):
        self.assertEqual(self.filterset({'q': 'RITM0012346'}, self.queryset).qs.count(), 1)

    def test_q_matches_description(self):
        self.assertEqual(self.filterset({'q': 'Primary'}, self.queryset).qs.count(), 1)

    def test_q_matches_comments(self):
        self.assertEqual(self.filterset({'q': 'provider'}, self.queryset).qs.count(), 1)

    def test_site_id(self):
        site = Site.objects.get(slug='site-1')
        self.assertEqual(self.filterset({'site_id': [site.pk]}, self.queryset).qs.count(), 2)

    def test_site(self):
        self.assertEqual(self.filterset({'site': ['site-2']}, self.queryset).qs.count(), 1)

    def test_tenant_id(self):
        tenant = Tenant.objects.get(slug='tenant-2')
        self.assertEqual(self.filterset({'tenant_id': [tenant.pk]}, self.queryset).qs.count(), 2)

    def test_tenant(self):
        self.assertEqual(self.filterset({'tenant': ['tenant-1']}, self.queryset).qs.count(), 1)

    def test_status(self):
        self.assertEqual(
            self.filterset({'status': [CrossConnectStatusChoices.STATUS_ACTIVE]}, self.queryset).qs.count(),
            1,
        )

    def test_last_known_path(self):
        self.assertEqual(self.filterset({'last_known_path__ic': 'Panel E'}, self.queryset).qs.count(), 1)
