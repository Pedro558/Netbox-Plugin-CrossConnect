# NetBox Cross Connects

NetBox plugin for managing cross connects as operational entities above native `dcim.Cable` objects.

## Compatibility

- Plugin version: `0.1.0`
- Target NetBox version: `4.4.8`
- NetBox plugin name: `netbox_cross_connects`
- Python package name: `netbox-cross-connects`

This package does not include NetBox core patches.

## Included Migration Files

- `netbox_cross_connects/migrations/0001_initial.py`

## Install

Install the package into the NetBox virtual environment:

```bash
source /opt/netbox/venv/bin/activate
pip install ./netbox_cross_connects-0.1.0-py3-none-any.whl
```

Enable the plugin in `/opt/netbox/netbox/netbox/configuration.py`:

```python
PLUGINS = [
    'netbox_cross_connects',
]
```

If `PLUGINS` already exists, append `'netbox_cross_connects'` to the existing list.

Run the standard NetBox plugin post-install steps:

```bash
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py migrate
/opt/netbox/venv/bin/python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

## Required Custom Field

Create an object custom field:

- Name: `cross_connect`
- Object type: `dcim.Cable`
- Related object type: `netbox_cross_connects.CrossConnect`

The plugin uses this custom field to show related cables on a CrossConnect detail page and to provide native trace links from those cables.

## Upgrade

Install the new wheel over the existing package:

```bash
source /opt/netbox/venv/bin/activate
pip install --upgrade ./netbox_cross_connects-<version>-py3-none-any.whl
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py migrate
/opt/netbox/venv/bin/python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

## Uninstall

Remove the plugin from `PLUGINS`, then uninstall the Python package:

```bash
source /opt/netbox/venv/bin/activate
pip uninstall netbox-cross-connects
sudo systemctl restart netbox netbox-rq
```

## Smoke Checklist

- `python manage.py check` succeeds with the plugin enabled
- Cross Connects appears under Plugins
- CrossConnect list, detail, add, edit, delete, and import views load
- REST API endpoints under `/api/plugins/cross-connects/` work
- `dcim.Cable` custom field `cross_connect` can link a cable to a CrossConnect
- Related cables and trace links display on the CrossConnect detail page
