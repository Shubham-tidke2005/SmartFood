from math import asin, cos, radians, sin, sqrt

from django.utils import timezone

from .models import ReceiverAvailability


def normalize_area_name(value):
    return " ".join(value.strip().lower().split())


def approximate_distance_km(
    latitude_one,
    longitude_one,
    latitude_two,
    longitude_two,
):
    """
    Calculate Haversine straight-line distance.

    This is not road distance, driving time or route distance.
    """
    earth_radius_km = 6371.0088

    latitude_one = radians(float(latitude_one))
    longitude_one = radians(float(longitude_one))
    latitude_two = radians(float(latitude_two))
    longitude_two = radians(float(longitude_two))

    latitude_difference = (
        latitude_two - latitude_one
    )

    longitude_difference = (
        longitude_two - longitude_one
    )

    haversine_value = (
        sin(latitude_difference / 2) ** 2
        + cos(latitude_one)
        * cos(latitude_two)
        * sin(longitude_difference / 2) ** 2
    )

    angular_distance = 2 * asin(
        sqrt(haversine_value)
    )

    return earth_radius_km * angular_distance


def receiver_is_currently_available(receiver):
    current_datetime = timezone.localtime()
    current_weekday = current_datetime.weekday()
    current_time = current_datetime.time()

    windows = ReceiverAvailability.objects.filter(
        receiver=receiver,
        active=True,
    )

    for window in windows:
        if window.starts_at <= window.ends_at:
            if (
                window.weekday == current_weekday
                and window.starts_at
                <= current_time
                <= window.ends_at
            ):
                return True

        else:
            # Overnight window, for example 22:00-02:00.
            if (
                window.weekday == current_weekday
                and current_time >= window.starts_at
            ):
                return True

            following_day = (
                window.weekday + 1
            ) % 7

            if (
                following_day == current_weekday
                and current_time <= window.ends_at
            ):
                return True

    return False