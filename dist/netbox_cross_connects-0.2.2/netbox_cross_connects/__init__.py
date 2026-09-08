from netbox.plugins import PluginConfig


class NetBoxCrossConnectsConfig(PluginConfig):
    name = 'netbox_cross_connects'
    verbose_name = 'NetBox Cross Connects'
    description = 'NetBox plugin for managing cross connects.'
    version = '0.2.2'
    author = 'Pedro Afonso'
    base_url = 'cross-connects'
    min_version = '4.4.8'

    def ready(self):
        super().ready()

        import dcim.forms
        import dcim.forms.connections
        from dcim.forms.model_forms import CableForm

        CableForm.base_fields['label'].required = True

        original_get_cable_form = dcim.forms.connections.get_cable_form

        def get_cable_form_with_required_label(*args, **kwargs):
            form = original_get_cable_form(*args, **kwargs)
            form.base_fields['label'].required = True
            return form

        dcim.forms.connections.get_cable_form = get_cable_form_with_required_label
        dcim.forms.get_cable_form = get_cable_form_with_required_label


config = NetBoxCrossConnectsConfig
