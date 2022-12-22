# pylint: disable=invalid-name
"""Nautobot signal handler functions for panorama_sync."""
import os

from django.apps import apps as global_apps
from nautobot.extras.choices import CustomFieldTypeChoices, RelationshipTypeChoices
from nautobot.core.settings_funcs import is_truthy


def nautobot_database_ready_callback(apps=global_apps, **kwargs):  # pylint: disable=too-many-locals
    """Callback function for post_migrate() -- create CustomField & Relationship records."""
    CustomField = apps.get_model("extras", "CustomField")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Relationship = apps.get_model("extras", "Relationship")
    Site = apps.get_model("dcim", "Site")
    Device = apps.get_model("dcim", "Device")
    DeviceType = apps.get_model("dcim", "DeviceType")
    DeviceRole = apps.get_model("dcim", "DeviceRole")
    Manufacturer = apps.get_model("dcim", "Manufacturer")
    Platform = apps.get_model("dcim", "Platform")
    Status = apps.get_model("extras", "Status")
    Secret = apps.get_model("extras", "Secret")
    Job = apps.get_model("extras", "Job")
    SecretsGroup = apps.get_model("extras", "SecretsGroup")
    SecretsGroupAssociation = apps.get_model("extras", "SecretsGroupAssociation")
    ComplianceFeature = apps.get_model("nautobot_golden_config", "ComplianceFeature")
    ComplianceRule = apps.get_model("nautobot_golden_config", "ComplianceRule")
    AddressObjectGroup = apps.get_model("nautobot_firewall_models", "AddressObjectGroup")
    Application = apps.get_model("nautobot_firewall_models", "ApplicationObject")
    ControlPlaneSystem = apps.get_model("nautobot_ssot_panorama", "ControlPlaneSystem")
    site, _ = Site.objects.get_or_create(
        name="Panorama Staging", slug="panorama-staging", status=Status.objects.get(slug="staging")
    )
    palo, _ = Manufacturer.objects.get_or_create(name="Palo Alto", slug="palo-alto")
    platform, _ = Platform.objects.get_or_create(name="Palo Alto Panos", slug="paloalto-panos", manufacturer=palo)
    device_role, _ = DeviceRole.objects.get_or_create(name="Panorama Staging", slug="panorama-staging")
    device_type, _ = DeviceType.objects.get_or_create(
        model="Panorama Staging", slug="panorama-staging", manufacturer=palo
    )
    Job.objects.all().update(enabled=True)

    panorama, _ = Device.objects.get_or_create(
        name="NTC Demo Panorama",
        device_role=device_role,
        device_type=device_type,
        site=site,
        status=Status.objects.get(slug="active"),
        platform=platform,
    )
    pano_user, _ = Secret.objects.get_or_create(
        name="Panorama Username",
        slug="panorama-username",
        provider="environment-variable",
        parameters={"variable": "NAUTOBOT_PANORAMA_USER"},
    )
    pano_pass, _ = Secret.objects.get_or_create(
        name="Panorama Password",
        slug="panorama-password",
        provider="environment-variable",
        parameters={"variable": "NAUTOBOT_PANORAMA_PWD"},
    )
    secret_group, _ = SecretsGroup.objects.get_or_create(
        name="NTC Demo Panorama Credentials", slug="ntc-demo-panorama-credentials"
    )
    SecretsGroupAssociation.objects.get_or_create(
        access_type="HTTP(S)", secret_type="password", group_id=secret_group.id, secret_id=pano_pass.id
    )
    SecretsGroupAssociation.objects.get_or_create(
        access_type="HTTP(S)", secret_type="username", group_id=secret_group.id, secret_id=pano_user.id
    )
    ControlPlaneSystem.objects.get_or_create(
        name="NTC Demo Panorama",
        verify_ssl=is_truthy(os.getenv("NAUTOBOT_PANORAMA_VERIFY", True)),
        port=int(os.getenv("NAUTOBOT_PANORAMA_PORT", 443)),
        device=panorama,
        fqdn_or_ip=os.getenv("NAUTOBOT_PANORAMA_URL"),
        secrets_group=secret_group,
    )

    for name, slug in {
        "Address Objects": "addressobject",
        "Address Groups": "addressgroup",
        "Application Objects": "application",
        "Application Groups": "applicationgroup",
        "Device Groups": "devicegroup",
        "Dynamic User Groups": "userobjectgroup",
        "Firewall Settings": "firewall",
        "Policies": "policy",
        "Policy Rules": "policyrule",
        "Serivce Objects": "serviceobject",
        "Service Groups": "servicegroup",
        "Vsys Settings": "vsys",
        "Zones": "zone",
    }.items():
        feature, _ = ComplianceFeature.objects.get_or_create(name=name, slug=slug)
        ComplianceRule.objects.get_or_create(
            platform=platform, feature=feature, config_type="json", config_ordered=False
        )

    custom_field, _ = CustomField.objects.get_or_create(
        type=CustomFieldTypeChoices.TYPE_TEXT,
        name="group-type",
        slug="group-type",
        defaults={
            "label": "ObjectGroup is static or dynamic",
        },
    )
    custom_field.content_types.set([ContentType.objects.get_for_model(AddressObjectGroup)])

    custom_field, _ = CustomField.objects.get_or_create(
        type=CustomFieldTypeChoices.TYPE_TEXT,
        name="application-type",
        slug="application-type",
        defaults={
            "label": "Application is object or container",
        },
    )
    custom_field.content_types.set([ContentType.objects.get_for_model(Application)])

    custom_field, _ = CustomField.objects.get_or_create(
        type=CustomFieldTypeChoices.TYPE_TEXT,
        name="dynamic-address-group-filter",
        slug="dynamic-address-group-filter",
        defaults={
            "label": "Dynamic AddressObjectGroup filter",
        },
    )
    custom_field.content_types.set([ContentType.objects.get_for_model(AddressObjectGroup)])

    # add Application -> Application Relationship
    relationship_dict = {
        "name": "Application Container",
        "slug": "application_container",
        "type": RelationshipTypeChoices.TYPE_MANY_TO_MANY_SYMMETRIC,
        "source_type": ContentType.objects.get_for_model(Application),
        "source_label": "Container Application Object",
        "destination_type": ContentType.objects.get_for_model(Application),
        "destination_label": "Child Applications",
    }
    Relationship.objects.get_or_create(name=relationship_dict["name"], defaults=relationship_dict)
