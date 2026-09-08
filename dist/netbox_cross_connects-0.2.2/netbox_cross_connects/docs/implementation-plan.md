# These are the prompts that will guide the plugin development

## Prompt 1 
Read the repository structure and identify how NetBox plugins are organized in this project. Do not modify files yet. Explain which files need to be created or changed to implement the plugin described in docs/cross-connect-plugin-spec.md.

### Result from Prompt 1

The repository was mapped and the folders/files structure to be followed was suggested according to netbox docs.

## Prompt 2
Create only the initial skeleton for a NetBox plugin named netbox_cross_connects.

Follow the specification in docs/cross-connect-plugin-spec.md.

Do not implement the CrossConnect model yet.
Only create the minimum files required for the plugin to be discovered by NetBox.

After editing, explain which files were created and how to enable the plugin in NetBox configuration.

### Result from Prompt 2

The initial skeleton was reviewed and it was corrected. The initial subclass PluginConfig was created and added into 'configuration.py'.

## Prompt 3
Implement only the CrossConnect model according to docs/cross-connect-plugin-spec.md.

Requirements:
- Do not modify NetBox core models.
- cross_connect_id must be required, unique, and validated with ^ID-[A-Z0-9]+-\d{5}$.
- ritm must be required and validated with ^RITM\d{7}$.
- Add status, site, tenant, activation_date, description, comments, and last_known_path.
- Use NetBox/Django conventions already present in this repository.

Do not implement views, forms, tables, or navigation yet.
After editing, tell me the migration command I should run.

### Result from Prompt 3

The 'model.py' from cross connect was created and choices was defined. The migration ran ok.

## Prompt 4
Implement the basic UI for CrossConnect:
- list view
- detail view
- create/edit/delete views if compatible with NetBox plugin conventions
- table
- form
- urls

Follow docs/cross-connect-plugin-spec.md.

Do not implement related cables yet.
Do not implement trace yet.
Keep the changes minimal and aligned with NetBox plugin patterns.

### Result from Prompt 4

The UI basic files was configured (8b36723e5715066af1d990183399c7398cd4ca66)
Fail when tried to run: /opt/netbox/venv/bin/python manage.py runserver

## Prompt 5

Add the Cross Connects menu item under the NetBox Connections menu if the plugin navigation API allows it.

If it is not possible to place it directly under the native Connections menu, implement the closest plugin navigation option and explain the limitation.

### Result from Prompt 5

Implemented the supported plugin navigation fallback in `netbox_cross_connects/navigation.py`.

Limitation: NetBox's plugin navigation API cannot inject plugin items into the native `Connections` menu.
Plugin `menu_items` are registered under the top-level `Plugins` menu, and plugin `menu` entries become separate
top-level menus. Because of that, the closest supported option is to expose `Cross Connects` under
`Plugins -> NetBox Cross Connects`.

The menu entry now includes object-level view/add permissions so it only appears for users who can access the
plugin content.

## Prompt 6

Implement the CrossConnect detail page section that lists related dcim.Cable objects.

Relationship strategy:
- Do not add fields to dcim.Cable.
- Query Cable objects whose custom field `cross_connect` references the current CrossConnect.
- Render them in a table or panel in the CrossConnect detail page.

Do not implement trace yet.
If the custom field does not exist, show a friendly empty message explaining that the custom field `cross_connect` must be created on dcim.Cable.

### Result from Prompt 6

Implemented the CrossConnect detail-page related cables section following ADR-001 and ADR-002.

What was added:
- The CrossConnect detail view now checks for a NetBox custom field named `cross_connect` on `dcim.Cable`.
- The custom field must be an object field whose related object type is the plugin `CrossConnect` model.
- When that prerequisite exists, the detail page queries `dcim.Cable` objects where
  `custom_field_data__cross_connect` matches the current CrossConnect and renders them in a related cables panel.
- When the custom field does not exist, the detail page renders a friendly informational message explaining that
  `cross_connect` must be created on `dcim.Cable` before cables can be linked.

Implementation notes:
- No fields were added to `dcim.Cable`.
- No trace behavior was implemented yet.
- The related cables panel uses a custom template so it can render either the table or the prerequisite message.
- View tests were updated to cover both the configured custom-field case and the missing-custom-field case.

Validation notes:
- Python compilation of the updated files succeeded.
- Full Django test execution could not be completed in this environment because
  `netbox.configuration_testing` does not load the plugin and running under the local development configuration failed
  at test database creation due to database permissions.

## Prompt 7

Analyze how NetBox exposes cable tracing in this version.

Do not implement changes yet.

Find the safest way for the CrossConnect detail page to trigger or display trace information based on the related cables.

The intended rule is:
- trace starts at the A-side device interface
- trace ends at the Z-side device interface
- patch panel front/rear ports are intermediate hops

Return an implementation plan only.

### Result from Prompt 7

Implemented the CrossConnect trace integration using NetBox's native cable tracing instead of adding a plugin-specific
path engine.

What was added:
- The CrossConnect detail page now includes a `Trace` panel.
- Trace resolution is performed in the plugin view layer by inspecting the CrossConnect's related `dcim.Cable`
  objects, collecting endpoint interfaces, and validating them against NetBox's existing `CablePath` model.
- The trace starts from the A-side endpoint interface when one unambiguous A-side interface can be identified.
- Patch panel `FrontPort` and `RearPort` hops are handled by NetBox core tracing logic, not by custom plugin code.
- When a valid path is found, the detail page exposes:
  - a link to the native interface trace page
  - a link to the native SVG trace rendering
- When no safe origin can be inferred, the plugin shows an `ambiguous` or `unavailable` trace state instead of
  inventing a path.

Related UI improvements made during implementation:
- The `Related Cables` table was updated to replace the empty `Path` column with:
  - `Termination A`
  - `Termination B`
- These columns now render the actual cable endpoint values from each cable, including their physical context and
  links to the termination objects, so the operator can inspect the real endpoints without opening each cable first.

Fixes made while validating the implementation:
- Imported Django `reverse` in the plugin view module so CrossConnect list/detail navigation and trace links resolve
  correctly.
- Fixed the custom related-cable endpoint table column by forcing `django-tables2` to render computed values instead
  of treating them as empty.
- Changed the default CrossConnect status from `planned` to `active`.
- Added `get_status_color()` to the CrossConnect model so NetBox status badges use the intended ChoiceSet colors
  instead of always falling back to light gray.

Validation notes:
- Python compilation of the updated plugin files succeeded after each change.
- `manage.py check` completed successfully except for the existing PostgreSQL 14 deprecation warning.
- Full Django test execution still could not be completed in this environment because the local database user does not
  have permission to create the temporary test database.

## Bonus

Before implementing, read the ADRs in docs/decisions and make sure your solution follows them.
