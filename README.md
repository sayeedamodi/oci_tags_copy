
---

# OCI Instance to Volume Tag Sync (Safe Mode)

## Overview

This script copies selected **freeform tags** from a **single Oracle Cloud Infrastructure (OCI) Compute instance** to its:

* Boot volume
* All attached block volumes

The script is designed to be **safe by default** and will **never overwrite existing freeform tags** on volumes.
It only adds missing tags.

---

## What Problem This Solves

In OCI, tags applied to compute instances are **not automatically propagated** to:

* Boot volumes
* Block volumes

This causes issues with:

* Cost tracking
* Resource ownership
* Environment separation (dev, qa, prod)
* Audits and reporting

This script ensures volumes inherit important context from their parent instance **without destroying existing metadata** like creation dates or operational notes.

---

## Tag Behavior

The script copies **only these freeform tags** from the instance:

```
environment
application
```

Rules:

* If a tag key already exists on a volume, it is **not overwritten**
* If the tag key is missing, it is **added**
* All other freeform tags remain untouched

Example:

**Instance tags**

```
environment: dev
application: billing
```

**Volume tags before**

```
created_on: 2024-11-02
```

**Volume tags after**

```
created_on: 2024-11-02
environment: dev
application: billing
```

---

## Scope and Safety

✔ Operates on **one compartment only**
✔ Operates on **one instance only**
✔ No recursion
✔ No bulk updates
✔ No destructive operations

This makes it suitable for testing and controlled production usage.

---

## Prerequisites

* Python 3.8 or later
* OCI Python SDK

Install dependencies:

```bash
pip install oci
```

---

## OCI Configuration

The script uses the default OCI config file:

```
~/.oci/config
```

Ensure the profile used has permission to:

* Read compute instances
* Read boot volume and block volume attachments
* Update boot volumes
* Update block volumes

---

## Required Permissions (Example)

Your IAM policy should include permissions similar to:

```
Allow group <group-name> to read instances in compartment <compartment-name>
Allow group <group-name> to read volume-attachments in compartment <compartment-name>
Allow group <group-name> to manage volumes in compartment <compartment-name>
Allow group <group-name> to manage boot-volumes in compartment <compartment-name>
```

---

## Configuration

Edit the script and set the following values:

```python
COMPARTMENT_OCID = "ocid1.compartment.oc1..xxxxx"
INSTANCE_OCID = "ocid1.instance.oc1..xxxxx"
```

These define the **exact scope** of the operation.

---

## How the Script Works

1. Fetches the specified compute instance
2. Extracts only the required freeform tags (`environment`, `application`)
3. Finds the boot volume attached to the instance
4. Adds missing tags to the boot volume
5. Finds all block volumes attached to the instance
6. Adds missing tags to each block volume
7. Skips updates if no changes are required

---

## Execution

Run the script:

```bash
python tag_instance_volumes.py
```

Example output:

```
Instance: app-server-01
Tags to copy (non-overwriting): {'environment': 'dev', 'application': 'billing'}

Boot volume updated: app-server-01_boot
Block volume unchanged: data-volume-01
Block volume updated: logs-volume-01
```

---

## Error Handling

* If the instance has no matching tags, the script exits safely
* If a volume already has the tag, it is skipped
* No partial tag overwrites occur

---

## Recommended First Run

Before running in production:

1. Test with a **non-production instance**
2. Verify tag behavior in OCI Console
3. Confirm IAM permissions
4. Optionally add logging or dry-run mode

---

## Future Enhancements

This script can be extended to:

* Add a dry-run mode
* Support defined tags and namespaces
* Process multiple instances
* Process entire compartments
* Generate CSV or JSON audit logs
* Enforce allowed tag values

---

## License

Internal use. Modify and extend as needed for your OCI environment.

---

You are building this the right way.

