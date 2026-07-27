class FamilyDataUnavailableError(Exception):
    """No raw data sheets could be downloaded for this product family at all."""

    def __init__(self, family_name: str):
        self.family_name = family_name
        super().__init__(
            f"No raw data sheets are available for family '{family_name}' on Thorlabs.com."
        )


class NoSpectralDataError(Exception):
    """The workbook downloaded fine, but no wavelength-based series could be parsed from it."""

    def __init__(self, variant_name: str):
        self.variant_name = variant_name
        super().__init__(
            f"Could not find any wavelength-based data in '{variant_name}.xlsx' "
            "- its layout isn't recognized by the parser."
        )


class WavelengthOutOfRangeError(Exception):
    """The workbook parsed fine, but none of its data falls within the requested window."""

    def __init__(
        self,
        variant_name: str,
        requested_low: float,
        requested_high: float,
        available_ranges: list[tuple[str, float, float]],
    ):
        self.variant_name = variant_name
        self.requested_low = requested_low
        self.requested_high = requested_high
        self.available_ranges = available_ranges

        if available_ranges:
            ranges_text = "; ".join(
                f"{metric}: {lo:.1f}-{hi:.1f} nm" for metric, lo, hi in available_ranges
            )
        else:
            ranges_text = "no wavelength data found"

        super().__init__(
            f"Requested window {requested_low:.1f}-{requested_high:.1f} nm has no data in "
            f"'{variant_name}.xlsx'. Available range(s): {ranges_text}"
        )
