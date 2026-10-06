# Persona sprites, full resolution

Three original characters, written for the rooftop (2026-10-06); same temperaments and stakes as the
personas they replaced, which borrowed characters from games (kept locally, never published).

Rendered with flux7-studio on 2026-10-06 (`POST /keyframe`, model `krea2_turbo_fp8_scaled`, style
"pixel art", 768x1024, seed 7, on a flat green chroma background; the prompt is embedded in each PNG).
The viewer's sprites (`hoshi7/web/sprites/`) are cut from these by `tools/sprites.py`: the green
background removed by a flood fill from the borders, the figure cropped and scaled down without
smoothing (vesper 144 px high, ledger7 112, mote 96).

| file | persona |
| --- | --- |
| vesper.png | VESPER, the roof's old climate controller (INTJ): an upright control console like an old command post, an amber gauge for an eye, steam pipes for hair, verdigris oxide |
| ledger7.png | LEDGER-7, a hydroponics maintenance drone (ISFJ): a small hovering greenhouse drone, cream and copper shell, a probe arm and a folded watering nozzle, a green status light, a logbook engraved on its side |
| mote.png | MOTE, a small salvage robot (ENFP): six thin legs like a cricket, a body of mismatched parts (a radio knob, a piece of antenna), two large lens eyes, a satchel of finds |
