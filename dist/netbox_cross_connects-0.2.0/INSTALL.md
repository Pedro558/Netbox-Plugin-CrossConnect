# NetBox Cross Connects Installation Guide

This guide installs the `netbox-cross-connects` package on any NetBox environment using NetBox's standard plugin
installation flow.

## Package

Use the wheel artifact:

```text
netbox_cross_connects-0.1.0-py3-none-any.whl
```

The package targets NetBox `4.4.8`.

## 1. Copy the Package to the Target Server

From the machine where the package was built, copy the wheel to the target NetBox server:

```bash
scp /opt/netbox/dist/netbox_cross_connects-0.1.0-py3-none-any.whl user@target-server:/tmp/
```

Replace `user@target-server` with the SSH user and hostname for the target environment.

## 2. Install the Package

On the target NetBox server:

```bash
source /opt/netbox/venv/bin/activate
pip install /tmp/netbox_cross_connects-0.1.0-py3-none-any.whl
```

Confirm the package is installed:

```bash
/opt/netbox/venv/bin/pip show netbox-cross-connects
```

## 3. Enable the Plugin

Edit NetBox's `configuration.py`:

```bash
sudo nano /opt/netbox/netbox/netbox/configuration.py
```

Add the plugin:

```python
PLUGINS = [
    'netbox_cross_connects',
]
```

If `PLUGINS` already exists, do not create a second `PLUGINS` setting. Append `'netbox_cross_connects'` to the existing
list.

## 4. Run NetBox Post-Install Commands

```bash
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py migrate
/opt/netbox/venv/bin/python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

## 5. Create the Required Custom Field

In the NetBox UI, go to:

```text
Customization > Custom Fields > Add
```

Create this custom field:

```text
Name: cross_connect
Type: Object
Object type: DCIM > Cable
Related object type: NetBox Cross Connects > Cross Connect
```

This field links native `dcim.Cable` objects to CrossConnect objects.

## 6. Validate the Installation

Run:

```bash
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py check
/opt/netbox/venv/bin/pip show netbox-cross-connects
```

In the NetBox UI, verify:

```text
Plugins > NetBox Cross Connects
```

Smoke check:

- CrossConnect list page loads
- CrossConnect detail page loads
- add, edit, delete, and import views load
- REST API endpoints under `/api/plugins/cross-connects/` respond
- a `dcim.Cable` can be linked to a CrossConnect through the `cross_connect` custom field
- related cables display on the CrossConnect detail page

## Upgrade

Copy the new wheel to the target server and run:

```bash
source /opt/netbox/venv/bin/activate
pip install --upgrade /tmp/netbox_cross_connects-<version>-py3-none-any.whl
cd /opt/netbox/netbox
/opt/netbox/venv/bin/python manage.py migrate
/opt/netbox/venv/bin/python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

## Uninstall

Remove `'netbox_cross_connects'` from `PLUGINS`, then run:

```bash
source /opt/netbox/venv/bin/activate
pip uninstall netbox-cross-connects
sudo systemctl restart netbox netbox-rq
```
