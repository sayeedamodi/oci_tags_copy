import oci
import pandas as pd
from datetime import datetime

# ============================================================
# USER INPUT
# ============================================================
PROFILE_NAME = "DEFAULT"

REQUIRED_DEFINED_TAGS = {
    "Application": ["Application"],
    "Environment": ["Environment"]
}

# ============================================================
# OCI CLIENTS
# ============================================================
config = oci.config.from_file(profile_name=PROFILE_NAME)
identity = oci.identity.IdentityClient(config)
compute = oci.core.ComputeClient(config)
block = oci.core.BlockstorageClient(config)

TENANCY_OCID = config["tenancy"]

# ============================================================
# AUDIT LOG
# ============================================================
audit_rows = []

# ============================================================
# HELPERS
# ============================================================
def extract_defined_tags(defined_tags):
    result = {}
    for namespace, keys in REQUIRED_DEFINED_TAGS.items():
        if namespace in defined_tags:
            for key in keys:
                if key in defined_tags[namespace]:
                    result.setdefault(namespace, {})[key] = defined_tags[namespace][key]
    return result


def add_only_missing_defined_tags(existing, new):
    merged = {k: v.copy() for k, v in (existing or {}).items()}
    for namespace, tags in new.items():
        merged.setdefault(namespace, {})
        for k, v in tags.items():
            if k not in merged[namespace]:
                merged[namespace][k] = v
    return merged


def get_all_compartments():
    compartments = oci.pagination.list_call_get_all_results(
        identity.list_compartments,
        TENANCY_OCID,
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE"
    ).data

    root = identity.get_compartment(TENANCY_OCID).data
    compartments.append(root)
    return compartments


# ============================================================
# MAIN
# ============================================================
def main():
    compartments = get_all_compartments()
    print(f"Total compartments found: {len(compartments)}")

    for comp in compartments:
        print(f"\nProcessing compartment: {comp.name}")

        instances = oci.pagination.list_call_get_all_results(
            compute.list_instances,
            comp.id
        ).data

        for instance in instances:
            print(f"  Instance: {instance.display_name}")
            instance_tags = extract_defined_tags(instance.defined_tags or {})

            if not instance_tags:
                continue

            availability_domain = instance.availability_domain

            # ---------------- BOOT VOLUMES ----------------
            boot_attachments = compute.list_boot_volume_attachments(
                availability_domain,
                comp.id,
                instance_id=instance.id
            ).data

            for attach in boot_attachments:
                boot_vol = block.get_boot_volume(attach.boot_volume_id).data
                existing = boot_vol.defined_tags or {}
                updated = add_only_missing_defined_tags(existing, instance_tags)

                if updated != existing:
                    block.update_boot_volume(
                        boot_vol.id,
                        oci.core.models.UpdateBootVolumeDetails(
                            defined_tags=updated
                        )
                    )

                    audit_rows.append({
                        "Compartment": comp.name,
                        "Instance Name": instance.display_name,
                        "Instance OCID": instance.id,
                        "Resource Type": "Boot Volume",
                        "Resource Name": boot_vol.display_name,
                        "Resource OCID": boot_vol.id,
                        "Tags Added": str(instance_tags)
                    })

            # ---------------- BLOCK VOLUMES ----------------
            volume_attachments = compute.list_volume_attachments(
                compartment_id=comp.id,
                instance_id=instance.id
            ).data

            for attach in volume_attachments:
                volume = block.get_volume(attach.volume_id).data
                existing = volume.defined_tags or {}
                updated = add_only_missing_defined_tags(existing, instance_tags)

                if updated != existing:
                    block.update_volume(
                        volume.id,
                        oci.core.models.UpdateVolumeDetails(
                            defined_tags=updated
                        )
                    )

                    audit_rows.append({
                        "Compartment": comp.name,
                        "Instance Name": instance.display_name,
                        "Instance OCID": instance.id,
                        "Resource Type": "Block Volume",
                        "Resource Name": volume.display_name,
                        "Resource OCID": volume.id,
                        "Tags Added": str(instance_tags)
                    })

    # ========================================================
    # EXCEL OUTPUT
    # ========================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"oci_tag_update_{timestamp}.xlsx"

    df = pd.DataFrame(audit_rows)
    df.to_excel(file_name, index=False)

    print("\n======================================")
    print("Tagging completed successfully")
    print(f"Audit file generated: {file_name}")
    print("======================================")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    main()
