"""Guide profile management services."""
from typing import Optional, List, Dict, Any
from django.contrib.auth import get_user_model
from django.db import transaction

from ..models import GuideProfile

User = get_user_model()


def create_guide_profile(
    user: User,
    business_location,
    license_number: str = '',
    years_of_experience: int = 0,
    languages_spoken: List[str] = None,
    specializations: List[str] = None,
    hourly_rate: Optional[float] = None,
    bio: str = '',
    verification_document: Optional[str] = None
) -> GuideProfile:
    """Create a new guide profile for a user.

    Args:
        user: The user to create a guide profile for
        business_location: The business location for the guide
        license_number: Guide's license number
        years_of_experience: Years of experience as a guide
        languages_spoken: List of language codes the guide speaks
        specializations: List of guide's specialization areas
        hourly_rate: Guide's hourly rate
        bio: Guide's biography
        verification_document: Path to verification document

    Returns:
        The created guide profile
    """
    if languages_spoken is None:
        languages_spoken = []
    if specializations is None:
        specializations = []

    profile = GuideProfile.objects.create(
        user=user,
        business_location=business_location,
        license_number=license_number,
        years_of_experience=years_of_experience,
        languages_spoken=languages_spoken,
        specializations=specializations,
        hourly_rate=hourly_rate,
        bio=bio,
        verification_document=verification_document
    )
    return profile


def update_guide_profile(
    profile: GuideProfile,
    data: Dict[str, Any]
) -> GuideProfile:
    """Update an existing guide profile.

    Args:
        profile: The guide profile to update
        data: Dictionary containing the fields to update

    Returns:
        The updated guide profile
    """
    for field, value in data.items():
        setattr(profile, field, value)
    profile.save()
    return profile


def verify_guide_profile(
    profile: GuideProfile,
    verified: bool = True
) -> GuideProfile:
    """Update the verification status of a guide profile.

    Args:
        profile: The guide profile to verify/unverify
        verified: Whether to verify or unverify the profile

    Returns:
        The updated guide profile
    """
    profile.is_verified = verified
    profile.save()
    return profile


def get_guide_profile(user: User) -> Optional[GuideProfile]:
    """Get a user's guide profile if it exists.

    Args:
        user: The user to get the guide profile for

    Returns:
        The guide profile if it exists, None otherwise
    """
    try:
        return user.guide_profile
    except GuideProfile.DoesNotExist:
        return None


def get_verified_guides() -> List[GuideProfile]:
    """Get all verified guide profiles.

    Returns:
        List of verified guide profiles
    """
    return GuideProfile.objects.filter(is_verified=True) 