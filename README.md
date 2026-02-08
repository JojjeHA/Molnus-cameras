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
- Molnus login via `/auth/token`
- Latest image via `/images/get`
- Camera entity uses Molnus CDN image URL

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

Open Molnus in a browser and log in:

- https://molnus.com/#/camera-list

Open Developer Tools (F12) → **Network** tab, then open the image gallery.

You should see a request like:

https://molnus.com/images/get?CameraId=
<UUID>&offset=0&limit=50&wildlifeRequired=false


The value after `CameraId=` is your camera UUID.

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
  - `deviceFilename`
  - `CameraId`
  - `ImagePredictions`
  - `species_labels`
  - `species_top`
  - `species_top_accuracy`
    
species_labels and species_top can be used in Home Assistant automations to trigger notifications for specific species (e.g. SUS_SCROFA for wild boar).
## Camera
**Molnus Latest**
- Displays the latest image inside Home Assistant
Screenshot: https://github.com/user-attachments/assets/0c88548d-a64c-446d-aa1e-943ece6239b1
---

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
  - action: notify.mobile_app_iphone
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
For Example 2 you'll need to know the name of the species and you can log that by using this automation:
```yaml
alias: Molnus – Logga artklassning
mode: queued
trigger:
  - platform: state
    entity_id: sensor.molnus_latest_image_id
condition: []
action:
  - service: logbook.log
    data:
      name: Molnus
      message: >
        Ny bild. species_top={{ state_attr('sensor.molnus_latest_image_id','species_top') }}
        labels={{ state_attr('sensor.molnus_latest_image_id','species_labels') }}
```



