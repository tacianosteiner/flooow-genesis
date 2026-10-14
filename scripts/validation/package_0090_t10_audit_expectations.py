"""Reuse accepted TEST activation/audit qualification without READY or S04."""
from pathlib import Path
import package_0090_source_closure as q
import package_0090_t10_expectations as expectations
import package_0090_authorized_s04 as accepted


def qualify(sql,run,container,folder,record,fixture,runtime_work):
    for module in [expectations,accepted]:
        record['recipe_hashes'][Path(module.__file__).name]=q.sha(Path(module.__file__).read_bytes())
    expectations.qualify(sql,run,container,folder,record,fixture,runtime_work)
    accepted.qualify(sql,run,container,folder,record,fixture,runtime_work)
