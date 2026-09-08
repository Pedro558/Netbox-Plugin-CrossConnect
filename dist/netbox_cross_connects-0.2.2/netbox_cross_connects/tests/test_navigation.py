from django.test import TestCase

from netbox_cross_connects.navigation import menu_items


class CrossConnectNavigationTestCase(TestCase):
    def test_menu_items_import_and_reverse_urls(self):
        self.assertEqual(len(menu_items), 1)

        item = menu_items[0]
        self.assertEqual(item.link, 'plugins:netbox_cross_connects:crossconnect_list')
        self.assertEqual(str(item.url), '/plugins/cross-connects/cross-connects/')
        self.assertEqual(item.permissions, ['netbox_cross_connects.view_crossconnect'])
        self.assertEqual(len(item.buttons), 1)

        button = item.buttons[0]
        self.assertEqual(button.link, 'plugins:netbox_cross_connects:crossconnect_add')
        self.assertEqual(str(button.url), '/plugins/cross-connects/cross-connects/add/')
        self.assertEqual(button.permissions, ['netbox_cross_connects.add_crossconnect'])
