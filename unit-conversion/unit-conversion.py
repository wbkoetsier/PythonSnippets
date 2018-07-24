#!/usr/bin/env python
# coding:utf-8
"""
Convert numeric values between different units of measurement
"""
from typing import Union
import pint

__all__ = ['convert']

# load the Pint registry
ureg = pint.UnitRegistry()


# on pint.test(): test fails on in place exponentiation, issue should be fixed in the to be released pint 0.9


def convert(value: Union[float, int, str], input_unit: str, output_unit: str, precision: int = -1) -> Union[float, int]:
    """Convert the given numeric value from the input unit of measurement to the output unit of measurement

    :param value: the input value as str or number
    :param input_unit: unit of measurement of the input value
    :param output_unit: unit of measurement the input value should be converted to
    :param precision: round to this many decimal places (round, not ceil), don't round if -1
    :return converted magnitude as float or int

    >>> convert('1', 'inch', 'cm')
    '2.54'
    >>> convert(2.54, 'inch', 'cm', 2)
    6.45
    >>> convert(298.15, 'K', 'degF', 0)
    77
    >>> convert(298.15, 'K', 'degC')
    25.0
    >>> convert('  12\\n', 'hPa', 'bar')
    '0.012'
    """
    # convert the value from input unit to output unit, but catch errors
    try:
        mag = ureg(f'{str(value)} * {input_unit}').to(output_unit).magnitude
        if precision < 0:
            result = mag
        elif precision == 0:
            result = int(round(mag, precision))
        else:
            result = round(mag, precision)
    except (AttributeError, ValueError):  # all pint.errors are Attr or Val errors
        raise
    if isinstance(value, str):
        # then also return a string
        return str(result)
    return result
