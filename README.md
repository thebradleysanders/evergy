# ⚡Evergy Integration for Home Assistant - WORK IN PROGRESS
# Status: Work in progress, still in dev.

A simple utility that you can use to login to your Evergy account and retrieve you meter readings.

> **Note: This is an unofficial utility that uses Evergy's non-public API.**

> Previously known as "KCPL"

## Usage
sensor:
  - platform: evergy
    username: !secret evergy_username
    password: !secret evergy_password


### Output
The last element from the `get_usage()` will be the latest data. The `usage` is in kilowatt-hours. I believe the `peakDateTime` is the
time during that day when your usage was the highest and the `peakDemand` is how many kilowatts you were drawing at that time.
```text
Latest data:
{
    'period': 'Saturday',
    'billStart': '0001-01-01T00:00:00',
    'billEnd': '0001-01-01T00:00:00',
    'billDate': '2021-09-18T00:00:00',
    'date': '9/18/2021',
    'usage': 14.7756,
    'demand': 3.7992,
    'avgDemand': 0.0,
    'peakDemand': 3.7992,
    'peakDateTime': '12:45 p.m.',
    'maxTemp': 71.0,
    'minTemp': 71.0,
    'avgTemp': 71.0,
    'cost': 18.5748, 
    'isPartial': False
}
```

## Home Assistant Integration
There isn't currently an Home Assistant integration that uses this library. Checkout [this thread to see how others have used it in Home Assistant](https://github.com/lawrencefoley/evergy/issues/8#issuecomment-902181182).
If you want to use this in a HA integration, please do and I'll link it here!

## Related Projects
- [KC Water](https://github.com/patrickjmcd/kcwater): A similar project developed by [Patrick McDonagh](https://github.com/patrickjmcd). Check it out!
- [KS_Gas](https://github.com/thebradleysanders/Kansas_Gas_Home_Assistant): A Home Assistant Integration for Kansas Gas

