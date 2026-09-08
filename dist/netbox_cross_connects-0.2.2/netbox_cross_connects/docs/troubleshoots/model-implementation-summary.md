# Cross Connect Model Implementation Summary

This note summarizes the main errors encountered while implementing the `CrossConnect` model, how each one was resolved, and why it happened.

## 1. Wrong Python version in the virtual environment

### Error

`RuntimeError: NetBox requires Python 3.12 or later. (Currently installed: Python 3.10.12)`

### Cause

The active virtual environment was created with Python 3.10, but the current NetBox version in this repository requires Python 3.12 or newer.

### Resolution

The old virtual environment was removed and recreated with Python 3.12. Dependencies were then reinstalled.

### Why this fixed it

NetBox validates the Python version during startup. Once the environment used Python 3.12, Django could continue bootstrapping the application.

## 2. `makemigrations` blocked by NetBox developer-mode guard

### Error

`CommandError: This command is available for development purposes only.`

### Cause

NetBox wraps Django's `makemigrations` command and only allows it when `DEVELOPER = True` in the active configuration.

### Resolution

`DEVELOPER = True` was added to `netbox/configuration.py`.

### Why this fixed it

With developer mode enabled, NetBox allows schema migration files to be generated for local development work.

## 3. `No changes detected in app 'netbox_cross_connects'`

### Error

`No changes detected in app 'netbox_cross_connects'`

### Cause

The model and related files had initially been created in the wrong directory:

- Wrong: `netbox/netbox/netbox_cross_connects`
- Correct: `netbox/netbox_cross_connects`

Django was loading the plugin package from `netbox/netbox_cross_connects`, so it could not see the model changes that were placed deeper in the tree.

### Resolution

The plugin files were moved into the actual package loaded by Django:

- `netbox/netbox_cross_connects/models.py`
- `netbox/netbox_cross_connects/choices.py`
- other plugin files and docs

### Why this fixed it

`makemigrations` only inspects models from installed Django apps. Once the model lived inside the installed plugin package, Django could detect the schema changes and generate `0001_initial.py`.

## 4. `ChoiceSet` definition error

### Error

`AssertionError: CrossConnectStatusChoices has a key defined but CHOICES is not a list`

### Cause

The plugin's `ChoiceSet` used a tuple for `CHOICES`, but NetBox requires a list when a `key` is defined.

### Resolution

`CHOICES` in `netbox/netbox_cross_connects/choices.py` was changed from a tuple to a list.

### Why this fixed it

This matches the contract enforced by `utilities.choices.ChoiceSet`, allowing the plugin module to import successfully.

## 5. Plugin URL import failure during startup

### Error

`ImportError: Module "netbox_cross_connects.api.urls" does not define a "urlpatterns" attribute/class`

### Cause

NetBox imports plugin URL modules during startup. The moved plugin still had placeholder files that did not define `urlpatterns`, so Django failed while loading plugin routes.

### Resolution

Safe empty URL lists were added for now:

- `netbox/netbox_cross_connects/api/urls.py`
- `netbox/netbox_cross_connects/urls.py`

Both files now define:

```python
urlpatterns = []
```

### Why this fixed it

The current milestone only required the model implementation, not working UI or API routes. Defining empty `urlpatterns` keeps the plugin importable until those layers are implemented later.

## 6. Duplicate plugin directories causing confusion

### Issue

Two plugin directories existed at the same time:

- Active package: `netbox/netbox_cross_connects`
- Stray duplicate: `netbox/netbox/netbox_cross_connects`

### Cause

Early edits were applied in the wrong location, which created a second copy of the plugin tree.

### Resolution

The useful files were moved into `netbox/netbox_cross_connects`, and checks confirmed Django imports the plugin from there.

### Why this matters

Keeping only one real plugin package avoids confusion during development, migrations, imports, and future debugging.

## Final state after fixes

- Django imports `netbox_cross_connects` from `netbox/netbox_cross_connects`
- The `CrossConnect` model is defined in the correct plugin package
- `0001_initial.py` was generated in `netbox/netbox_cross_connects/migrations`
- `showmigrations netbox_cross_connects` reports `0001_initial` as applied
- URL imports no longer block startup while the plugin is still model-only

## Follow-up recommendation

Remove the stray duplicate folder `netbox/netbox/netbox_cross_connects` once its contents are no longer needed, so the repository contains only the real plugin package.
