---
tags: [chart, natal]
chart_id: {{chart_id}}
birth_date: {{birth_date}}
birth_time: {{birth_time}}
birth_place: {{birth_place}}
created: {{created_date}}
---

# Natal Chart: {{display_name}}

## Birth Data

| Field | Value |
|---|---|
| Date | {{birth_date}} |
| Time | {{birth_time}} ({{timezone}}) |
| UTC | {{utc_datetime}} |
| Location | {{location_name}} ({{latitude}}, {{longitude}}) |

## Planetary Positions

| Planet | Longitude | Sign | Degree | House | Retrograde |
|---|---|---|---|---|---|
{{#planets}}
| {{name}} | {{longitude}}° | {{sign}} | {{sign_degree}}° | {{house}} | {{#retrograde}}R{{/retrograde}} |
{{/planets}}

## House Cusps (Placidus)

| House | Cusp | Sign | Degree |
|---|---|---|---|
{{#houses}}
| {{number}} ({{angle_name}}) | {{cusp}}° | {{sign}} | {{cusp_degree}}° |
{{/houses}}

## Major Aspects

| Planet 1 | Planet 2 | Aspect | Angle | Orb | Applying |
|---|---|---|---|---|---|
{{#aspects}}
| {{planet1}} | {{planet2}} | {{type}} | {{angle}}° | {{orb}}° | {{#applying}}Yes{{/applying}}{{^applying}}No{{/applying}} |
{{/aspects}}

## Phase Analysis

{{#phase_analysis}}
### {{planet}}: P <{{Z}}.{{z}} : {{H}}.{{h}} : D={{D}}>

**Z-phase (Sign): {{Z}} - {{phase_name}}**
- Microphase: {{z}}
- From domicile ({{domicile}}): {{calculation}}

**H-phase (House): {{H}} - {{house_phase_name}}**
- Microphase: {{h}}
- In {{house}}th house from ASC

**D-sanction ({{dispositor}}): {{D}} - {{dispositor_phase_name}}**
- {{dispositor}} in {{dispositor_sign}}, {{D}}th from {{dispositor_domicile}}

{{/phase_analysis}}

## Analysis Notes

<!-- Add interpretation notes here -->

## Related Files

- [[{{chart_id}}_canvas.json]]
- [[chart_wheel.svg]]
- [[aspect_grid.svg]]
- [[PACK_MANIFEST.yaml]]

## Related Charts

- Progressed: [[{{chart_id}}_progressed_{{year}}]]
- Solar return: [[{{chart_id}}_solar_return_{{year}}]]
