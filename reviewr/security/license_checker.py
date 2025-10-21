"""
License compliance checker for dependencies.

Provides:
- License detection
- License compatibility checking
- Policy enforcement
- SPDX license identification
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path
from enum import Enum


class LicenseCategory(Enum):
    """License categories based on permissiveness."""
    PERMISSIVE = "permissive"  # MIT, Apache, BSD
    WEAK_COPYLEFT = "weak_copyleft"  # LGPL, MPL
    STRONG_COPYLEFT = "strong_copyleft"  # GPL, AGPL
    PROPRIETARY = "proprietary"
    PUBLIC_DOMAIN = "public_domain"
    UNKNOWN = "unknown"


class LicenseRisk(Enum):
    """License risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class License:
    """A software license."""
    spdx_id: str
    name: str
    category: LicenseCategory
    is_osi_approved: bool = False
    is_fsf_approved: bool = False
    requires_attribution: bool = True
    allows_commercial: bool = True
    allows_modification: bool = True
    allows_distribution: bool = True
    requires_source_disclosure: bool = False
    requires_same_license: bool = False
    
    @property
    def is_permissive(self) -> bool:
        """Check if license is permissive."""
        return self.category == LicenseCategory.PERMISSIVE
    
    @property
    def is_copyleft(self) -> bool:
        """Check if license is copyleft."""
        return self.category in (
            LicenseCategory.WEAK_COPYLEFT,
            LicenseCategory.STRONG_COPYLEFT
        )
    
    @property
    def is_compatible_with_proprietary(self) -> bool:
        """Check if license is compatible with proprietary software."""
        return self.category in (
            LicenseCategory.PERMISSIVE,
            LicenseCategory.PUBLIC_DOMAIN
        )


@dataclass
class LicensePolicy:
    """License policy for a project."""
    name: str
    allowed_licenses: Set[str] = field(default_factory=set)
    denied_licenses: Set[str] = field(default_factory=set)
    allowed_categories: Set[LicenseCategory] = field(default_factory=set)
    denied_categories: Set[LicenseCategory] = field(default_factory=set)
    require_osi_approved: bool = False
    require_fsf_approved: bool = False
    allow_unknown: bool = False
    
    def is_license_allowed(self, license: License) -> bool:
        """Check if a license is allowed by this policy."""
        # Check explicit denials first
        if license.spdx_id in self.denied_licenses:
            return False
        
        if license.category in self.denied_categories:
            return False
        
        # Check explicit allowances
        if license.spdx_id in self.allowed_licenses:
            return True
        
        if license.category in self.allowed_categories:
            return True
        
        # Check OSI/FSF requirements
        if self.require_osi_approved and not license.is_osi_approved:
            return False
        
        if self.require_fsf_approved and not license.is_fsf_approved:
            return False
        
        # Check unknown licenses
        if license.category == LicenseCategory.UNKNOWN:
            return self.allow_unknown
        
        # Default: deny if no explicit allowance
        return False
    
    def get_risk_level(self, license: License) -> LicenseRisk:
        """Get risk level for a license."""
        if license.spdx_id in self.denied_licenses:
            return LicenseRisk.CRITICAL
        
        if license.category in self.denied_categories:
            return LicenseRisk.HIGH
        
        if license.category == LicenseCategory.UNKNOWN:
            return LicenseRisk.MEDIUM
        
        if license.category == LicenseCategory.STRONG_COPYLEFT:
            return LicenseRisk.MEDIUM
        
        return LicenseRisk.LOW


class LicenseChecker:
    """Checker for license compliance."""
    
    # Common licenses with their properties
    KNOWN_LICENSES = {
        "MIT": License(
            spdx_id="MIT",
            name="MIT License",
            category=LicenseCategory.PERMISSIVE,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=False,
            requires_same_license=False
        ),
        "Apache-2.0": License(
            spdx_id="Apache-2.0",
            name="Apache License 2.0",
            category=LicenseCategory.PERMISSIVE,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=False,
            requires_same_license=False
        ),
        "BSD-3-Clause": License(
            spdx_id="BSD-3-Clause",
            name="BSD 3-Clause License",
            category=LicenseCategory.PERMISSIVE,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=False,
            requires_same_license=False
        ),
        "BSD-2-Clause": License(
            spdx_id="BSD-2-Clause",
            name="BSD 2-Clause License",
            category=LicenseCategory.PERMISSIVE,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=False,
            requires_same_license=False
        ),
        "ISC": License(
            spdx_id="ISC",
            name="ISC License",
            category=LicenseCategory.PERMISSIVE,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=False,
            requires_same_license=False
        ),
        "GPL-3.0": License(
            spdx_id="GPL-3.0",
            name="GNU General Public License v3.0",
            category=LicenseCategory.STRONG_COPYLEFT,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=True,
            requires_same_license=True,
            allows_commercial=True
        ),
        "GPL-2.0": License(
            spdx_id="GPL-2.0",
            name="GNU General Public License v2.0",
            category=LicenseCategory.STRONG_COPYLEFT,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=True,
            requires_same_license=True,
            allows_commercial=True
        ),
        "LGPL-3.0": License(
            spdx_id="LGPL-3.0",
            name="GNU Lesser General Public License v3.0",
            category=LicenseCategory.WEAK_COPYLEFT,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=True,
            requires_same_license=False,
            allows_commercial=True
        ),
        "LGPL-2.1": License(
            spdx_id="LGPL-2.1",
            name="GNU Lesser General Public License v2.1",
            category=LicenseCategory.WEAK_COPYLEFT,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=True,
            requires_same_license=False,
            allows_commercial=True
        ),
        "MPL-2.0": License(
            spdx_id="MPL-2.0",
            name="Mozilla Public License 2.0",
            category=LicenseCategory.WEAK_COPYLEFT,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=True,
            requires_same_license=False,
            allows_commercial=True
        ),
        "AGPL-3.0": License(
            spdx_id="AGPL-3.0",
            name="GNU Affero General Public License v3.0",
            category=LicenseCategory.STRONG_COPYLEFT,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_source_disclosure=True,
            requires_same_license=True,
            allows_commercial=True
        ),
        "Unlicense": License(
            spdx_id="Unlicense",
            name="The Unlicense",
            category=LicenseCategory.PUBLIC_DOMAIN,
            is_osi_approved=True,
            is_fsf_approved=True,
            requires_attribution=False,
            requires_source_disclosure=False,
            requires_same_license=False
        ),
        "CC0-1.0": License(
            spdx_id="CC0-1.0",
            name="Creative Commons Zero v1.0 Universal",
            category=LicenseCategory.PUBLIC_DOMAIN,
            is_osi_approved=False,
            is_fsf_approved=True,
            requires_attribution=False,
            requires_source_disclosure=False,
            requires_same_license=False
        ),
    }
    
    # Predefined policies
    PERMISSIVE_POLICY = LicensePolicy(
        name="Permissive",
        allowed_categories={
            LicenseCategory.PERMISSIVE,
            LicenseCategory.PUBLIC_DOMAIN
        },
        denied_categories={
            LicenseCategory.STRONG_COPYLEFT,
            LicenseCategory.PROPRIETARY
        },
        require_osi_approved=True,
        allow_unknown=False
    )
    
    COPYLEFT_FRIENDLY_POLICY = LicensePolicy(
        name="Copyleft Friendly",
        allowed_categories={
            LicenseCategory.PERMISSIVE,
            LicenseCategory.WEAK_COPYLEFT,
            LicenseCategory.STRONG_COPYLEFT,
            LicenseCategory.PUBLIC_DOMAIN
        },
        denied_categories={
            LicenseCategory.PROPRIETARY
        },
        require_osi_approved=True,
        allow_unknown=False
    )
    
    def __init__(self, policy: Optional[LicensePolicy] = None):
        """
        Initialize license checker.
        
        Args:
            policy: License policy to enforce (defaults to PERMISSIVE_POLICY)
        """
        self.policy = policy or self.PERMISSIVE_POLICY
    
    def identify_license(self, license_text: str) -> Optional[License]:
        """
        Identify a license from its text.
        
        Args:
            license_text: License text content
            
        Returns:
            Identified license or None
        """
        license_text = license_text.lower()
        
        # Check for common license identifiers
        if "mit license" in license_text:
            return self.KNOWN_LICENSES["MIT"]
        elif "apache license" in license_text and "version 2.0" in license_text:
            return self.KNOWN_LICENSES["Apache-2.0"]
        elif "bsd" in license_text and "3-clause" in license_text:
            return self.KNOWN_LICENSES["BSD-3-Clause"]
        elif "bsd" in license_text and "2-clause" in license_text:
            return self.KNOWN_LICENSES["BSD-2-Clause"]
        elif "isc license" in license_text:
            return self.KNOWN_LICENSES["ISC"]
        elif "gnu general public license" in license_text and "version 3" in license_text:
            return self.KNOWN_LICENSES["GPL-3.0"]
        elif "gnu general public license" in license_text and "version 2" in license_text:
            return self.KNOWN_LICENSES["GPL-2.0"]
        elif "gnu lesser general public license" in license_text and "version 3" in license_text:
            return self.KNOWN_LICENSES["LGPL-3.0"]
        elif "gnu lesser general public license" in license_text and "version 2.1" in license_text:
            return self.KNOWN_LICENSES["LGPL-2.1"]
        elif "mozilla public license" in license_text and "version 2.0" in license_text:
            return self.KNOWN_LICENSES["MPL-2.0"]
        elif "gnu affero general public license" in license_text:
            return self.KNOWN_LICENSES["AGPL-3.0"]
        elif "unlicense" in license_text:
            return self.KNOWN_LICENSES["Unlicense"]
        elif "creative commons zero" in license_text:
            return self.KNOWN_LICENSES["CC0-1.0"]
        
        return None
    
    def get_license_by_spdx(self, spdx_id: str) -> Optional[License]:
        """Get license by SPDX identifier."""
        return self.KNOWN_LICENSES.get(spdx_id)
    
    def check_compliance(self, licenses: List[License]) -> Dict[str, Any]:
        """
        Check license compliance for a list of licenses.
        
        Args:
            licenses: List of licenses to check
            
        Returns:
            Compliance report
        """
        violations = []
        warnings = []
        
        for license in licenses:
            if not self.policy.is_license_allowed(license):
                risk = self.policy.get_risk_level(license)
                
                if risk in (LicenseRisk.CRITICAL, LicenseRisk.HIGH):
                    violations.append({
                        "license": license.spdx_id,
                        "name": license.name,
                        "risk": risk.value,
                        "reason": f"License {license.spdx_id} is not allowed by policy"
                    })
                else:
                    warnings.append({
                        "license": license.spdx_id,
                        "name": license.name,
                        "risk": risk.value,
                        "reason": f"License {license.spdx_id} requires review"
                    })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "total_licenses": len(licenses),
            "policy": self.policy.name
        }

