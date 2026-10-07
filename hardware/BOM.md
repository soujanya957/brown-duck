# Bill of materials

Generated from [`BOM.csv`](BOM.csv) by `python hardware/make_bom_md.py`. Edit the CSV, not this file.
Source: the [official Open Duck Mini v2 BOM spreadsheet](https://docs.google.com/spreadsheets/d/1gq4iWWHEJVgAA_eemkTEsshXqrYlFxXAPwO515KpCJc),
plus items the [assembly guide](../Open_Duck_Mini/docs/assembly_guide.md) needs but the sheet leaves out.

| | EUR |
|---|---:|
| **Robot total** | **398.10** |
| Expression package (optional) | 14.24 |
| Robot + expression package | 412.34 |

Prices are **upstream EU prices** (mostly amazon.fr / AliExpress) from the spreadsheet, per unit unless noted. **Shipping, tax and US prices are extra**: fill in `us_source` as you find US sellers.
Not priced yet: M3 screws (assorted lengths, incl. M3x10), Hook-up wire, Blue Loctite 243 threadlocker, Soldering iron + basic electronics tools.

| Category | Part | Qty | Unit € | Line € | Notes | US source | Status |
|---|---|---:|---:|---:|---|---|---|
| Power | 18650 cell (high discharge, e.g. Molicel P30B 3000 mAh 30 A) | 2 | 5 | 10.00 | beefiest cells you can find |  | to-order |
| Power | 2S 18650 cell holder | 1 | 4.99 | 4.99 |  |  | to-order |
| Power | 2S BMS | 1 | 8.40 | 8.40 |  |  | to-order |
| Power | 5V regulator (UBEC) | 1 | 4 | 4.00 | powers the Pi |  | to-order |
| Power | Small power switch | 1 | 4.49 | 4.49 |  |  | to-order |
| Power | USB-C charger | 1 | 9.99 | 9.99 |  |  | to-order |
| Power | 2.1 mm barrel jack | 2 | 1 | 2.00 |  |  | to-order |
| Power | XT30 connector pair | 1 | 8 | 8.00 | price is for a bundle; only one pair needed |  | to-order |
| Control | Feetech STS3215 7.4V ("19 kg·cm", STS3215-C001) | 14 | 14 | 196.00 | NOT the 12V version |  | to-order |
| Control | Waveshare Bus Servo Adapter (A) | 1 | 5 | 5.00 |  |  | to-order |
| Control | Raspberry Pi Zero 2W | 1 | 26.08 | 26.08 |  |  | to-order |
| Control | microSD card | 1 | 10 | 10.00 |  |  | to-order |
| Control | BNO055 IMU | 1 | 40 | 40.00 | cheaper clones exist, untested |  | to-order |
| Control | Foot contact switches (SS-10) | 4 | 1 | 4.00 |  |  | to-order |
| Control | 9g servos | 2 | 3.33 | 6.66 | antennas only, optional |  | to-order |
| Misc | M3 heat-set inserts | 1 kit | 5.99 | 5.99 |  |  | to-order |
| Misc | PLA | ~500 g | 20 | 20.00 | price is for the lot |  | to-order |
| Misc | TPU | small | 0 | 0.00 | foot soles |  | to-order |
| Misc | Cable sheath | 1 | 9 | 9.00 |  |  | to-order |
| Misc | Micro-USB to USB-C cable, 15 cm | 1 | 7 | 7.00 | Pi <-> servo board |  | to-order |
| Misc | Micro-USB to USB-C cable, 50 cm | 1 | 6 | 6.00 | Pi <-> servo board |  | to-order |
| Misc | Bearing | 3 | 3.50 | 10.50 | in the official spreadsheet; trunk_bottom + head (assembly guide) |  | to-order |
| Misc | M3 screws (assorted lengths, incl. M3x10) | TBD |  |  | not in spreadsheet; assembly guide: count TBD |  | to-order |
| Misc | Hook-up wire | some |  |  | not in spreadsheet; required by assembly guide |  | to-order |
| Tools | Blue Loctite 243 threadlocker | 1 |  |  | not in spreadsheet; metal-to-metal servo screws only |  | to-order |
| Tools | Soldering iron + basic electronics tools | 1 |  |  | not in spreadsheet; borrow from the lab if possible |  | to-order |
| Expression (optional) | Projector reflector | 1 | 2 | 2.00 | official 'expression package' |  | to-order |
| Expression (optional) | Speaker | 1 | 6 | 6.00 | official 'expression package' |  | to-order |
| Expression (optional) | MAX98357A amplifier | 1 | 5 | 5.00 | official 'expression package'; sold in 2-packs |  | to-order |
| Expression (optional) | LEDs (eyes + projector) | 3 | 0.20 | 0.60 | sold in packs of ~50 |  | to-order |
| Expression (optional) | Eye diffusers | 4 | 0.16 | 0.64 | sold in packs of ~60 |  | to-order |
