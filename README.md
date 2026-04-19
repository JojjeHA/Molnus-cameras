<p align="center">
  <img src="assets/molnus-logo.png" width="350">
</p>

# Molnus Home Assistant Integration


A custom Home Assistant integration for **Molnus** wildlife cameras.

It connects to the Molnus cloud, fetches the latest images for a selected camera, and exposes:

- ✅ `sensor` entity: Latest image ID + useful attributes (url, captureDate, thumbnail, etc)
- ✅ `camera` entity: Shows the latest photo directly inside Home Assistant

> ⚠️ Unofficial integration. Not affiliated with Molnus.

---

## Features

- UI setup via **Config Flow**
- Cloud polling via `DataUpdateCoordinator`
- Secure Molnus login
- Automatic token renewal
- Fetches latest images from Molnus cloud API
- Camera entity displays latest image in Home Assistant
- Species prediction attributes for automations
- Compatible with latest Molnus API platform changes

---

# Installation

## ✅ Install with HACS (Recommended)

### 1) Add this repository to HACS
In Home Assistant:

**HACS → Integrations → 3 dots → Custom repositories**

Add:

- Repository: `https://github.com/JojjeHA/Molnus-cameras`
- Category: **Integration**

### 2) Install
Go to:

**HACS → Integrations → Molnus → Download**

### 3) Restart Home Assistant
Restart is required after installing via HACS.

### 4) Add the integration
Go to:

**Settings → Devices & services → Add integration → Molnus**

You will need:

- Molnus email
- Molnus password
- Camera ID (UUID)

---

## Manual installation (Alternative)

Copy this folder into your Home Assistant config:

/config/custom_components/molnus/


Then restart Home Assistant.

---

# Finding the Camera ID (UUID)

Open image gallery for your camera.

The UUID is shown in the browser address after: camera=

Example:
https://molnus.com/#/image-gallery?camera=4d7e3d36-a011-42bf-a14c-b2f639a78g3f

---

# Entities

## Sensor
**Molnus Latest Image ID**
- State: Latest image ID (numeric)
- Attributes:
  - `url`
  - `thumbnailUrl`
  - `captureDate`
  - `createdAt`
  - `updatedAt`
  - `deviceFilename`
  - `CameraId`
  - `ImagePredictions`
  - `species_labels`
  - `species_top`
  - `species_top_accuracy`
    
Species detection usage

Use species_labels or species_top in automations.

Example labels:

`SUS_SCROFA` = Wild boar

`CAPREOLUS` = Roe deer

## Camera
**Molnus Latest**
- Displays the latest image inside Home Assistant
- Recommended lovelace card:
```yaml
type: picture-entity
entity: camera.molnus_latest
show_name: false
show_state: false
```
Screenshot: https://github.com/user-attachments/assets/0c88548d-a64c-446d-aa1e-943ece6239b1
---
## API Compatibility
This integration is updated for the newer Molnus cloud platform.

Current endpoints used internally:

Auth: `/auth/token`

Images: `/images?cameraId=...`

Hosted at:
https://client-api.molnus.com

# Example Automations
Automation Example 1:
```yaml
alias: "📸 Molnus: Ny bild från viltkameran"
mode: single
trigger:
  - platform: state
    entity_id: sensor.molnus_latest_image_id

condition:
  - condition: template
    value_template: "{{ trigger.from_state is not none }}"
  - condition: template
    value_template: "{{ trigger.from_state.state not in ['unknown','unavailable'] }}"

action:
  - service: notify.mobile_app_iphone
    data:
      title: "📸 Ny bild registrerad!"
      message: >
        Tid: {{ state_attr('sensor.molnus_latest_image_id', 'captureDate') }}
      data:
        image: "{{ state_attr('sensor.molnus_latest_image_id', 'url') }}"
```

---
Automation Example 2:
```yaml
alias: "Molnus – Vildsvin före 21"
mode: single

trigger:
  - platform: state
    entity_id: sensor.molnus_latest_image_id

condition:
  - condition: template
    value_template: >
      {{ trigger.to_state is not none and trigger.to_state.state not in ['unknown','unavailable',''] }}

  - condition: time
    before: "21:00:00"

  - condition: template
    value_template: >
      {% set labels = state_attr('sensor.molnus_latest_image_id','species_labels') or [] %}
      {{ 'SUS_SCROFA' in labels }}

action:
  - service: notify.mobile_app_iphone
    data:
      title: "🐗 Vildsvin upptäckt"
      message: "Molnus klassning: SUS_SCROFA"
      data:
        image: "{{ state_attr('sensor.molnus_latest_image_id','url') }}"
        push:
          sound:
            name: default
            critical: 1
            volume: 1.0

```
---
Example 3 – Log detected species:
```yaml
alias: Molnus – Logga artklassning
mode: queued

trigger:
  - platform: state
    entity_id: sensor.molnus_latest_image_id

action:
  - service: logbook.log
    data:
      name: Molnus
      message: >
        Ny bild.
        species_top={{ state_attr('sensor.molnus_latest_image_id','species_top') }}
        labels={{ state_attr('sensor.molnus_latest_image_id','species_labels') }}
```
# Troubleshooting
Sensor is `unknown`

Check:

- Correct camera UUID
- Molnus login credentials
- Camera has uploaded images
- Integration reloaded after update
  
No picture shown

Use the built-in camera entity:
```yaml
type: picture-entity
entity: camera.molnus_latest
```
Integration stopped after Molnus update

Update to latest version in HACS.
# Disclaimer
**This is an unofficial community integration and may require updates if Molnus changes their cloud API in the future.**
