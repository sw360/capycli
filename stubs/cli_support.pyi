import xml.etree.ElementTree as ET
from typing import List

class CliFileItemBase:
    def __init__(self) -> None:
        self.files: List[str] = []
        self.hashes: List[str] = []
        ...

    def read_files_from_element(self, element: ET.Element) -> None:
        ...


class CliCopyright(CliFileItemBase):
    def __init__(self) -> None:
        self.text: str = ""
        ...

    def read_from_element(self, element: ET.Element) -> None:
        ...


class CliExportRestriction(CliFileItemBase):
    def __init__(self) -> None:
        self.text: str = ""
        ...

    def read_from_element(self, element: ET.Element) -> None:
        ...


class CliLicense(CliFileItemBase):
    def __init__(self) -> None:
        self.license_text: str = ""
        self.type: str = ""
        self.name: str = ""
        self.spdx_identifier: str = ""
        self.acknowledgements: List[str] = []
        self.tags: List[str] = []
        ...

    def read_from_element(self, element: ET.Element) -> None:
        ...


class CliObligation:
    def __init__(self) -> None:
        ...

    def read_from_element(self, element: ET.Element) -> None:
        ...


class CliFile:
    filename: str = ""
    component: str = ""
    creator: str = ""
    date: str = ""
    baseDoc: str = ""
    toolUsed: str = ""
    componentId: str = ""
    includesAcknowledgements: bool = False
    componentSha1: str = ""
    version: str = ""

    licenses: List[CliLicense] = []
    copyrights: List[CliCopyright] = []
    obligations: List[CliObligation] = []
    tags: List[str] = []
    irrelevant_files: List[str] = []
    export_restrictions: List[CliExportRestriction] = []
    
    def __init__(self) -> None:
        ...

    def read_from_file(self, filename: str) -> None:
        ...


class LicenseTools:
    NOT_README_TAG = "NOT_README_OSS"
    NON_FUNCTIONAL_TAG = "NON_FUNCTIONAL"
    NON_USED_DUAL_LICENSE_TAG = "NOT_USED_DUAL_LICENSE"
    MANUAL_CHECK_NEEDED_TAG = "MANUAL_CHECK_NEEDED"

    def __init__(self) -> None:
        ...

    @staticmethod
    def get_global_license(clifile: CliFile) -> CliLicense:
        ...

    @staticmethod
    def get_non_global_licenses(clifile: CliFile) -> list:  # type: ignore
        ...

    @staticmethod
    def has_license(clifile: CliFile, spdx_identifier: str) -> bool:
        ...

    @staticmethod
    def is_source_code_shipping_license(spdx_identifier: str) -> bool:
        ...

    @staticmethod
    def is_multi_license(spdx_identifier: str) -> bool:
        ...

    @staticmethod
    def is_do_not_use_license(license: CliLicense) -> bool:
        ...

    @staticmethod
    def has_multi_license(clifile: CliFile) -> bool:
        ...

    @staticmethod
    def has_do_not_use_files(clifile: CliFile) -> bool:
        ...

    @staticmethod
    def has_source_code_shipping_license(clifile: CliFile) -> bool:
        ...

    @staticmethod
    def license_has_not_readme_tag(license: CliLicense) -> bool:
        ...

    @staticmethod
    def component_has_not_readme_tag(clifile: CliFile) -> bool:
        ...
