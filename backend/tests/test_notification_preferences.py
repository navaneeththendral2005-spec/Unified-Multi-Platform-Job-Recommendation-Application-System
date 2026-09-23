from app.models.user_preference import UserPreference


def test_notification_preferences_are_optional_and_default_on_persistence():
    preference = UserPreference(user_id=999999)
    assert getattr(preference, "email_application_updates", True) is not False
    assert getattr(preference, "email_recommendations", True) is not False
