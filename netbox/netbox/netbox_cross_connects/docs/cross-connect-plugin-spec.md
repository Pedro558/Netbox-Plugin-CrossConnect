# NetBox Cross Connect Plugin - Specification

## Goal

Create a NetBox plugin named `netbox_cross_connects` to represent Cross Connects as operational entities above native `dcim.Cable` objects.

The plugin must not modify NetBox core models directly.

The plugin should respect the netbox official docs, specially about plugin development and changes in core tables.

## Main entity

Model: `CrossConnect`

Fields:

- `cross_connect_id`
  - Required
  - Unique
  - Pattern: `^ID-[A-Z0-9]+-\d{5}$`
  - Example: `ID-RJO1-00650`

- `ritm`
  - Required
  - Pattern: `^RITM\d{7}$`
  - Example: `RITM0012345`

- `status`
  - Use NetBox standard status choices for now, if possible.
  - Initial statuses: planned, active, offline/decommissioning/decommissioned depending on NetBox available status choices.

- `site`
  - Required
  - Reference to `dcim.Site`.

- `tenant`
  - Required
  - Reference to `tenancy.Tenant`.

- `activation_date`
  - Optional date field.

- `description`
  - Optional text.

- `comments`
  - Optional long text.

- `last_known_path`
  - Optional long text.
  - Reserved for future disconnected workflow.

## Cable relationship strategy

Do not add a real FK to `dcim.Cable`.

Use a NetBox Custom Field of type Object on `dcim.Cable` named `cross_connect` pointing to this plugin model.

The CrossConnect detail page must show all Cable objects where the custom field `cross_connect` references the current CrossConnect.

## UI

Add a menu item under Connections:

Connections > Cross Connects

The CrossConnect detail page should show:

- Cross Connect ID
- RITM
- Status
- Site
- Tenant
- Activation Date
- Description
- Comments
- Related Cables table

## Related Cables view

Render related cables as:

Cable 1: Device_A/interface -> Patch_Panel_A/front_port
Cable 2: Patch_Panel_A/rear_port -> Patch_Panel_B/rear_port
Cable 3: Patch_Panel_B/front_port -> Device_B/interface

## Trace

Do not implement trace in the first task.

Prepare the structure so that a Trace button/action can be added later.

The trace should eventually start from the A-side device interface and end at the Z-side device interface. Patch panel front/rear ports are intermediate hops.

## Future workflow

A future version will implement status `disconnected` and populate `last_known_path` before removing/decommissioning cables.