from datetime import date, time
from typing import Optional
from app.tools.formatters.hospital_shifts_formatter import format_hospital_shifts


# A simple mock for the HospitalShift model, matching its attributes
class MockHospitalShift:
    def __init__(
        self,
        hospital_shift_date: Optional[date],
        hospital_name: Optional[str],
        hospital_shift_start_time: Optional[time] = None,
        hospital_shift_end_time: Optional[time] = None,
        specialties: Optional[str] = None,
        address: Optional[str] = None,
        phone_number: Optional[str] = None,
    ):
        self.hospital_shift_date = hospital_shift_date
        self.hospital_name = hospital_name
        self.hospital_shift_start_time = hospital_shift_start_time
        self.hospital_shift_end_time = hospital_shift_end_time
        self.specialties = specialties
        self.address = address
        self.phone_number = phone_number


def test_format_hospital_shifts_empty():
    """Tests formatting with an empty list of shifts."""
    assert (
        format_hospital_shifts([])
        == "Δεν βρέθηκαν εφημερίες νοσοκομείων που να ταιριάζουν με τα κριτήριά σας."
    )


def test_format_hospital_shifts_single_shift_all_details():
    """Tests formatting a single shift with all details present."""
    shifts = [
        MockHospitalShift(
            hospital_shift_date=date(2023, 10, 26),
            hospital_name="Γενικό Νοσοκομείο Αθηνών",
            hospital_shift_start_time=time(8, 0),
            hospital_shift_end_time=time(16, 0),
            specialties="Καρδιολογία\nΠνευμονολογία",
            address="Λεωφόρος Αθηνών 123",
            phone_number="2101234567",
        )
    ]
    expected_output = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- 26/10/2023 ---\n"
        "- Νοσοκομείο: Γενικό Νοσοκομείο Αθηνών (Έναρξη: 08:00, Λήξη: 16:00), Ειδικότητες: Καρδιολογία, Πνευμονολογία, Διεύθυνση: Λεωφόρος Αθηνών 123, Τηλέφωνο: 2101234567"
    )
    assert format_hospital_shifts(shifts) == expected_output


def test_format_hospital_shifts_single_shift_minimal_details():
    """Tests formatting a single shift with only mandatory details and some Nones."""
    shifts = [
        MockHospitalShift(
            hospital_shift_date=date(2023, 10, 27), hospital_name="Νοσοκομείο Πόλης"
        )
    ]
    expected_output = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- 27/10/2023 ---\n"
        "- Νοσοκομείο: Νοσοκομείο Πόλης"
    )
    assert format_hospital_shifts(shifts) == expected_output


def test_format_hospital_shifts_optional_fields_none():
    """Tests formatting with various optional fields being None."""
    shifts = [
        MockHospitalShift(
            hospital_shift_date=None,  # Άγνωστη Ημερομηνία
            hospital_name=None,  # Άγνωστο Όνομα
            hospital_shift_start_time=time(9, 0),
            specialties="Γενική Ιατρική",
        )
    ]
    expected_output = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- Άγνωστη Ημερομηνία ---\n"
        "- Νοσοκομείο: Άγνωστο Όνομα (Έναρξη: 09:00), Ειδικότητες: Γενική Ιατρική"
    )
    assert format_hospital_shifts(shifts) == expected_output


def test_format_hospital_shifts_multiple_shifts_same_date():
    """Tests formatting multiple shifts on the same date, testing sorting by name."""
    shifts = [
        MockHospitalShift(
            hospital_shift_date=date(2023, 11, 1),
            hospital_name="Νοσοκομείο Β",
            specialties="Ορθοπεδική",
        ),
        MockHospitalShift(
            hospital_shift_date=date(2023, 11, 1),
            hospital_name="Νοσοκομείο Α",
            specialties="Παιδιατρική",
        ),
    ]
    expected_output = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- 01/11/2023 ---\n"
        "- Νοσοκομείο: Νοσοκομείο Α, Ειδικότητες: Παιδιατρική\n"
        "- Νοσοκομείο: Νοσοκομείο Β, Ειδικότητες: Ορθοπεδική"
    )
    assert format_hospital_shifts(shifts) == expected_output


def test_format_hospital_shifts_multiple_dates():
    """Tests formatting shifts on multiple dates, testing date grouping and sorting."""
    shifts = [
        MockHospitalShift(
            hospital_shift_date=date(2023, 11, 2),
            hospital_name="Νοσοκομείο Γ",
            specialties="Δερματολογία",
        ),
        MockHospitalShift(
            hospital_shift_date=date(2023, 11, 1),
            hospital_name="Νοσοκομείο Α",
            specialties="Παιδιατρική",
        ),
    ]
    expected_output = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- 01/11/2023 ---\n"
        "- Νοσοκομείο: Νοσοκομείο Α, Ειδικότητες: Παιδιατρική\n"
        "\n--- 02/11/2023 ---\n"
        "- Νοσοκομείο: Νοσοκομείο Γ, Ειδικότητες: Δερματολογία"
    )
    assert format_hospital_shifts(shifts) == expected_output


def test_format_hospital_shifts_with_start_time_only():
    shifts = [
        MockHospitalShift(
            hospital_shift_date=date(2023, 10, 26),
            hospital_name="Νοσοκομείο Α",
            hospital_shift_start_time=time(8, 0),
        )
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- 26/10/2023 ---\n"
        "- Νοσοκομείο: Νοσοκομείο Α (Έναρξη: 08:00)"
    )
    assert format_hospital_shifts(shifts) == expected


def test_format_hospital_shifts_with_end_time_only():
    shifts = [
        MockHospitalShift(
            hospital_shift_date=date(2023, 10, 26),
            hospital_name="Νοσοκομείο Β",
            hospital_shift_end_time=time(16, 0),
        )
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- 26/10/2023 ---\n"
        "- Νοσοκομείο: Νοσοκομείο Β (Λήξη: 16:00)"
    )
    assert format_hospital_shifts(shifts) == expected


def test_format_hospital_shifts_no_specialties_address_phone():
    shifts = [
        MockHospitalShift(
            hospital_shift_date=date(2023, 10, 26),
            hospital_name="Νοσοκομείο Γ",
            hospital_shift_start_time=time(9, 0),
            hospital_shift_end_time=time(17, 0),
        )
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- 26/10/2023 ---\n"
        "- Νοσοκομείο: Νοσοκομείο Γ (Έναρξη: 09:00, Λήξη: 17:00)"
    )
    assert format_hospital_shifts(shifts) == expected


def test_format_hospital_shifts_multiline_specialties():
    """Tests formatting with multi-line specialties string."""
    shifts = [
        MockHospitalShift(
            hospital_shift_date=date(2023, 10, 26),
            hospital_name="Νοσοκομείο Δ",
            specialties="Καρδιολογία\nΧειρουργική\nΟφθαλμολογία",
        )
    ]
    expected_output = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- 26/10/2023 ---\n"
        "- Νοσοκομείο: Νοσοκομείο Δ, Ειδικότητες: Καρδιολογία, Χειρουργική, Οφθαλμολογία"
    )
    assert format_hospital_shifts(shifts) == expected_output


def test_format_hospital_shifts_single_line_specialties():
    """Tests formatting with single-line specialties string."""
    shifts = [
        MockHospitalShift(
            hospital_shift_date=date(2023, 10, 26),
            hospital_name="Νοσοκομείο Ε",
            specialties="Παθολογία",
        )
    ]
    expected_output = (
        "Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:\n"
        "\n--- 26/10/2023 ---\n"
        "- Νοσοκομείο: Νοσοκομείο Ε, Ειδικότητες: Παθολογία"
    )
    assert format_hospital_shifts(shifts) == expected_output
