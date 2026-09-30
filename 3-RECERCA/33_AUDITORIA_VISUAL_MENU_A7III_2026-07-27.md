# Auditoria visual del menú de l'A7III — 27 de juliol de 2026

## 1. Abast i criteri d'evidència

Auditoria de les vint fotografies `IMG_2441.HEIC`–`IMG_2460.HEIC`
facilitades per Pere Guerra. Representen l'estat visible de la Sony A7III
en el moment de fer les fotografies.

Una fila de menú amb valor visible acredita aquell valor. Una entrada que
només obre un submenú **no acredita** els valors interiors. Per tant, aquest
lot és un bon snapshot de vint pantalles, però no és encara una captura
exhaustiva de tot el menú ni permet validar per si sol
`--confirm-manual-checklist`.

La comparació s'ha fet contra
`controller/CHECKLIST_CAMP_A7III_AP130.md` i s'ha complementat amb el
preflight físic:

`controller/runs/20260727T232930_candidate_a7m3_ap130_short_hybrid_5x3_then_9x1_preflight`

## 2. Resultat executiu

No s'ha trobat **cap divergència demostrada** entre els valors visibles i
el perfil A7III + AP130GTX + QUADCC.

Queden acreditats visualment:

- `File Format = RAW & JPEG`;
- `RAW File Type = Uncompressed`;
- `JPEG Quality = Standard`;
- `JPEG Image Size = S: 6.0M`;
- `Aspect Ratio = 3:2`;
- `Drive Mode = Single Shooting`;
- `Focus Mode = Manual Focus`;
- `ISO = ISO 100`;
- `Auto Review = Off`;
- `Pwr Save Start Time = 30 Min`;
- `USB Connection = PC Remote`;
- `USB Power Supply = On`.

El preflight físic també va acreditar per PTP `M`, `ISO 100`, `1/8000`,
`Single Shot`, `RAW+JPEG (Std)`, `Sensor Crop = Off`,
`DRange Optimizer = Off`, `capturetarget = card+sdram`, cua `d215 = 0`,
model i sèrie correctes i bateria al 73%.

## 3. Inventari literal per fotografia

| Evidència | Pantalla | Valors visibles | Estat respecte del perfil |
|---|---|---|---|
| `IMG_2441.HEIC` | Camera Settings1 · Quality/Image Size1 · 1/14 | `File Format = RAW & JPEG`; `RAW File Type = Uncompressed`; `JPEG Quality = Standard`; `JPEG Image Size = S: 6.0M`; `Aspect Ratio = 3:2`; `APS-C/Super 35mm` | Els cinc valors explícits són correctes. `APS-C/Super 35mm` és un submenú i no acredita els valors interiors. |
| `IMG_2442.HEIC` | Camera Settings1 · Shoot Mode/Drive1 · 3/14 | `Scene Selection = —`; `Drive Mode = Single Shooting`; `Bracket Settings`; `MR 1/2 Recall`; `MR 1/2 Memory`; `MR Select Media = Slot 1` | `Single Shooting` correcte. `Bracket Settings` no acredita l'ordre ni l'autodisparador. `MR Select Media` no és el destí ordinari de gravació. |
| `IMG_2443.HEIC` | Camera Settings1 · AF1 · 5/14 | `Focus Mode = Manual Focus`; `Priority Set in AF-S = Balanced Emphasis`; `Priority Set in AF-C = Balanced Emphasis`; `Focus Area = Wide`; `Focus Settings`; `Swt. V/H AF Area = Off` | `Manual Focus` correcte. La resta no és gate del perfil. |
| `IMG_2444.HEIC` | Camera Settings1 · AF3 · 7/14 | `Pre-AF = —`; `Eye-Start AF = —`; `AF Area Regist. = On`; `Del. Reg. AF Area`; `AF Area Auto Clear = Off`; `Disp. cont. AF area = On` | No cobert i sense contradicció. Els guions indiquen funcions no disponibles en l'estat actual, no una confirmació d'`Off`. |
| `IMG_2445.HEIC` | Camera Settings1 · Exposure1 · 9/14 | `Exposure Comp. = ±0.0`; `Reset EV Comp. = Reset`; `ISO = ISO 100`; `ISO AUTO Min. SS = Standard`; `Metering Mode = Multi`; `Face Prty in Mlti Mtr = Off` | `ISO 100` correcte. La resta no és gate del perfil. |
| `IMG_2446.HEIC` | Camera Settings1 · Flash · 11/14 | `Flash Mode = Flash Off`; `Flash Comp. = ±0.0`; `Exp.comp.set = Ambient&flash`; `Wireless Flash = Off`; `Red Eye Reduction = Off`; `External Flash Set.` | No cobert i sense contradicció. |
| `IMG_2447.HEIC` | Camera Settings1 · Focus Assist · 13/14 | `Focus Magnifier`; `Focus Magnif. Time = No Limit`; `Initial Focus Mag. = x1.0`; `AF in Focus Mag. = On`; `MF Assist = On`; `Peaking Setting` | Compatible amb l'enfocament manual; no és gate temporal. |
| `IMG_2448.HEIC` | Camera Settings2 · Movie1 · 1/9 | `Exposure Mode = —`; `S&Q Exposure Mode = —`; `File Format = XAVC S 4K`; `Record Setting = 25p 60M`; `S&Q Settings`; `Proxy Recording = Off` | Configuració de vídeo, no substitueix el format fotogràfic i no afecta el perfil. |
| `IMG_2449.HEIC` | Camera Settings2 · Movie3 · 3/9 | `Audio Out Timing = Live`; `Wind Noise Reduct. = Off`; `Marker Display = Off`; `Marker Settings`; `Video Light Mode = Power Link`; `Movie w/ shutter = Off` | No cobert i sense contradicció. |
| `IMG_2450.HEIC` | Camera Settings2 · Zoom · 5/9 | `Zoom = —`; `Zoom Setting = Optical zoom only`; `Zoom Ring Rotate = —` | No cobert i irrellevant amb l'AP130GTX. |
| `IMG_2451.HEIC` | Camera Settings2 · Display/Auto Review2 · 7/9 | `Cont. Shoot. Length = Shoot.-Only Display`; `Auto Review = Off` | `Auto Review = Off` correcte. |
| `IMG_2452.HEIC` | Camera Settings2 · Custom Operation2 · 9/9 | `Dial Ev Comp = Off`; `MOVIE Button = Always`; `Lock Operation Parts = Off`; `Audio signals = On`; `Function Ring(Lens) = Power Focus` | No hi ha gate divergent. `Audio signals = On` queda registrat, però no hi ha cap guany temporal acreditat per canviar-lo. |
| `IMG_2453.HEIC` | Network2 · 2/3 | `Wi-Fi Settings`; `Bluetooth Settings`; `Loc. Info. Link Set.`; `Edit Device Name`; `Imp Root Certificate`; `Reset Network Set.` | Són submenús. No acredita `Ctrl w/ Smartphone` ni `Airplane Mode`, que són a una altra pantalla. |
| `IMG_2454.HEIC` | Playback1 · 1/4 | `Protect`; `Rotate`; `Delete`; `Rating`; `Rating Set(Custom Key)`; `Specify Printing` | Reproducció; no afecta la captura. |
| `IMG_2455.HEIC` | Playback3 · 3/4 | `Select PB Media = Slot 1`; `View Mode`; `Image Index`; `Display as Group = Off`; `Display Rotation = Auto`; `Image Jump Setting` | `Select PB Media` és només reproducció i no acredita `Prioritize Rec. Media`. |
| `IMG_2456.HEIC` | Setup1 · 1/7 | `Monitor Brightness = Manual`; `Viewfinder Bright. = Auto`; `Finder Color Temp. = ±0`; `Gamma Disp. Assist = Off`; `Volume Settings = 0`; `Delete confirm. = "Cancel" first` | No cobert i sense contradicció. |
| `IMG_2457.HEIC` | Setup2 · 2/7 | `Display Quality = Standard`; `Pwr Save Start Time = 30 Min`; `Auto Pwr OFF Temp. = Standard`; `NTSC/PAL Selector`; `Cleaning Mode`; `Touch Operation = Off` | `30 Min` correcte. `Auto Pwr OFF Temp. = Standard` queda registrat, però encara no és un gate congelat. |
| `IMG_2458.HEIC` | Setup4 · 4/7 | `4K Output Sel. = —`; `USB Connection = PC Remote`; `USB LUN Setting = Multi`; `USB Power Supply = On`; `PC Remote Settings`; `Language = English` | `PC Remote` i alimentació USB correctes. El submenú no acredita les dues opcions internes de ruta. `USB LUN = Multi` queda registrat sense atribuir-li impacte en PC Remote. |
| `IMG_2459.HEIC` | Setup6 · 6/7 | `Rec. Media Settings`; `Select REC Folder`; `New Folder`; `Folder Name = Standard Form`; `Recover Image DB`; `Display Media Info.` | `Rec. Media Settings` és un submenú: no acredita slot, mode ni canvi automàtic de targeta. |
| `IMG_2460.HEIC` | Camera Settings1 · Quality/Image Size1 · 1/14 | Mateixos cinc valors de `IMG_2441`; `APS-C/Super 35mm` com a submenú | Corrobora `IMG_2441`, tot i que la fotografia té moviment i sobreimpressió. |

## 4. Evidència no visible al lot i confirmació manual posterior

Les fotografies no acrediten visualment els interiors següents. Pere va
confirmar manualment el 28-07-2026 que havia recorregut el checklist complet
abans del `screen` T020900 i del `qualify` T021121; aquesta declaració consta
als dos resultats com `operator_confirmed_manual_checklist=true`. Això va ser
vàlid per als assajos, però no amplia retroactivament el contingut de les
fotografies i s'ha de repetir al camp.

Per deixar també evidència visual exhaustiva, una sola fotografia de cada
pantalla o submenú següent seria suficient:

1. `Camera Settings1 → APS-C/Super 35mm`:
   `Shooting = Manual` i `Shoot.: Manual = Off`.
2. `Camera Settings1 → Bracket Settings`:
   `Bracket order = − → 0 → +` i `Selftimer during Brkt = Off`.
3. Pantalla que contingui `Interval Shooting = Off`.
4. Pantalla que contingui `Long Exposure NR = Off` i
   `High ISO NR = Off`.
5. `Camera Settings2 → Shutter/SteadyShot`:
   `Release w/o Lens = Enable`, `Release w/o Card = Disable`,
   `Silent Shooting = On` i `SteadyShot = Off`.
6. `Setup → Rec. Media Settings`:
   `Prioritize Rec. Media = Slot 1`, `Recording Mode = Standard` i
   `Auto Switch Media = Off`; Slot 2 buit.
7. `Setup → PC Remote Settings`:
   `Still Img. Save Dest. = PC+Camera` i
   `RAW+J PC Save Img = JPEG Only`.
8. `Network1`:
   `Ctrl w/ Smartphone = Off` i `Airplane Mode = On`.
9. `Setup → Version`: `ILCE-7M3`, `Ver. 4.04`.

`DRO/Auto HDR = Off`, `M`, `ISO 100`, `1/8000`, `Single Shot`,
`Sensor Crop = Off`, `RAW+JPEG (Std)`, `card+sdram`, identitat, bateria i
cua ja tenen evidència PTP recent. Els paràmetres que gphoto no exposa
continuen requerint confirmació manual.

## 5. Decisions que no s'han de prendre encara

- No canviar `Audio signals = On` només per intuïció: no és un gate de
  qualitat ni hi ha una millora temporal mesurada.
- No canviar `USB LUN Setting = Multi`: la sessió PC Remote ha passat
  preflight i aquest valor no s'ha demostrat com a causa de `Connecting…`.
- `Auto Pwr OFF Temp. = Standard` mereix una prova tèrmica separada abans
  de decidir si es congela a `High`; no s'ha d'introduir una nova variable
  just abans del gate de velocitat.

## 6. Empremtes SHA-256 de les evidències

```text
46c6fda1fc50ab0cb84280889561af63cd290827d710f85ed377b3d8a0746b79  IMG_2441.HEIC
e2938bb8c0c684513a576c25f458b6bca1eaf91e1fecb511a82415ca42dc476f  IMG_2442.HEIC
9f122edad775f67b6582ee71176e3ed2269d7c4132c3dc1e25329f6e2df46a7e  IMG_2443.HEIC
dc7e6053f8aab106a594a0f9a6aa97f80c0626adb5759c78ee751cba78cda900  IMG_2444.HEIC
a726a0d11f7d54e3e62b66d619810a309c1b0747ee0b7d26ab959a5d61b2df8e  IMG_2445.HEIC
9f3d12ee5b2ddeaf830b785adcefb1d64ca6374e1c2fa3e6b015a40dd95601e3  IMG_2446.HEIC
71a4c28eed1adba5fd2d029065d0f2397add7cad69ca7467a5350a08256ff981  IMG_2447.HEIC
8308c0edcd5ef27fc5fed36e0dfff9ed4aae613c218cc0a1790c111fbd4bf5dd  IMG_2448.HEIC
bbb8ce3dfd21e371283805b317db12989d243810c96d58c1c802352062fba106  IMG_2449.HEIC
d0c824cbfa8d0e47c64bf33b8978b211736fd38446f9b3bba09be687779f7344  IMG_2450.HEIC
31097bc0e8367c18c712baae42ee72b272ec36f20ae918a3cacb2ce5767e104a  IMG_2451.HEIC
f0f0a499c77625529a7fd8f0a209f58bb90a3c794692ac0517c26978973a5e34  IMG_2452.HEIC
963d66e88c4236565d83d96140dc1b07dd97cc8101725e27e95480c0db7db07c  IMG_2453.HEIC
0fc32eba80526d73c852fa513ab2a9b6befa9c08792a0400f7f6ff8d4bb1d92a  IMG_2454.HEIC
e1cf5f26c0cb7b72fe54e730c0ed5a85203355ccdd2e0584b6f14267e62dbdbc  IMG_2455.HEIC
2f2a5f43e94413b2367cf7647d9df67f62ca31bcf6b07c1a74cd6234cb49c53b  IMG_2456.HEIC
b72d7148708b8eafdb1fff1b0f4de035882805a9957c044866abf2348d7a7205  IMG_2457.HEIC
99e30371d93e28c80e58e28921ffc848eb6b44952e9a8e40eabb5e868b4c6d42  IMG_2458.HEIC
5256f8a2eca1b0a3a28ae85a259c15f6203ac466402d75f9b9ab57d7d2a2e296  IMG_2459.HEIC
5cade7c1a5c1c1acdd4d6d005cc7c7b53396858f1bb06440c32418f4e6cf1c3e  IMG_2460.HEIC
```
