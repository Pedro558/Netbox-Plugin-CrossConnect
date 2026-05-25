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

## Prompt 5

Add the Cross Connects menu item under the NetBox Connections menu if the plugin navigation API allows it.

If it is not possible to place it directly under the native Connections menu, implement the closest plugin navigation option and explain the limitation.

### Result from Prompt 5

## Prompt 6

Implement the CrossConnect detail page section that lists related dcim.Cable objects.

Relationship strategy:
- Do not add fields to dcim.Cable.
- Query Cable objects whose custom field `cross_connect` references the current CrossConnect.
- Render them in a table or panel in the CrossConnect detail page.

Do not implement trace yet.
If the custom field does not exist, show a friendly empty message explaining that the custom field `cross_connect` must be created on dcim.Cable.

### Result from Prompt 6

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

## Bonus

Before implementing, read the ADRs in docs/decisions and make sure your solution follows them.

