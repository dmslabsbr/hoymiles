# Hoymiles Solar Data Gateway - Edge Add-on

This add-on connects your Hoymiles cloud plant to Home Assistant through MQTT.

Important notes:

- Edge is a development branch and may be less stable than the stable version.
- The integration uses an unofficial API and can break when cloud behavior changes.

## Who This Is For

This README is for Home Assistant end users who want to:

- install the add-on,
- configure login, plant, and MQTT settings,
- understand what each option does and when to use it.

Developer and project-internal documents were moved to the doc directory.

## Install In Home Assistant

1. Open Home Assistant.
2. Go to Settings -> Add-ons -> Add-on Store.
3. Add this repository URL:
   [https://github.com/dmslabsbr/hoymiles]
4. Install Hoymiles Solar Data Gateway Edge.
5. Configure options (see full option guide below).
6. Start the add-on.
7. Check Log output for successful login, data polling, and MQTT publishing.

## Quick Start Configuration

Fill at least these fields first:

- HOYMILES_USER
- HOYMILES_PASSWORD
- HOYMILES_PLANT_ID

Then choose MQTT mode:

- Internal Home Assistant MQTT: keep External_MQTT_Server as false.
- External MQTT broker: set External_MQTT_Server to true and fill MQTT_Host, MQTT_User, MQTT_Pass (and TLS settings if needed).

## Full Option Reference

Source of truth: config.json options/schema in this add-on.

### Required Cloud Access

- HOYMILES_USER
  - What it does: Hoymiles account username/email used to authenticate.
  - Use when: always required.

- HOYMILES_PASSWORD
  - What it does: Hoymiles account password.
  - Use when: always required.

- HOYMILES_PLANT_ID
  - What it does: plant/site identifier used for data queries.
  - Use when: always required.

### Cloud/API Compatibility

- USE_ESTAR
  - What it does: enables ESTAR compatibility mode.
  - Use when: your account/environment requires ESTAR-specific behavior.

- EXPERIMENTAL_CUSTOM_API_URLS
  - What it does: allows custom cloud API endpoints.
  - Use when: only for advanced compatibility troubleshooting or non-default regional endpoints.

- API_GATEWAY_BASE_URL
  - What it does: custom base URL for gateway-style endpoints.
  - Use when: EXPERIMENTAL_CUSTOM_API_URLS is true and you need a custom gateway host.

- API_VERSIONED_BASE_URL
  - What it does: custom base URL for versioned API endpoints.
  - Use when: EXPERIMENTAL_CUSTOM_API_URLS is true and versioned API host differs.

- API_COOKIE_DOMAIN
  - What it does: custom cookie domain used during authentication/session handling.
  - Use when: cookies are scoped to a different domain in your environment.

### API Version Debug Controls

- DEBUG_FORCE_API_VERSION
  - What it does: overrides automatic API version selection.
  - Use when: debugging login/data compatibility only.

- DEBUG_API_VERSION
  - What it does: forced API version value (0 or 3).
  - Use when: DEBUG_FORCE_API_VERSION is true and you need to test a specific API path.

### MQTT Connection

- External_MQTT_Server
  - What it does: switches between Home Assistant internal MQTT credentials and an external broker.
  - Use when: set true for external broker, false for Home Assistant internal broker.

- MQTT_Host
  - What it does: hostname/IP of external MQTT broker.
  - Use when: External_MQTT_Server is true.

- MQTT_User
  - What it does: username for external MQTT broker authentication.
  - Use when: External_MQTT_Server is true and broker requires auth.

- MQTT_Pass
  - What it does: password for external MQTT broker authentication.
  - Use when: External_MQTT_Server is true and broker requires auth.

- MQTT_TLS
  - What it does: enables TLS for MQTT connection.
  - Use when: broker requires encrypted MQTT.

- MQTT_TLS_PORT
  - What it does: TLS port used for MQTT (default 8883).
  - Use when: MQTT_TLS is true or broker uses a non-standard secure port.

### Home Assistant Discovery Topics

- MQTT_DISCOVERY_PREFIX
  - What it does: Home Assistant MQTT discovery root topic (default homeassistant).
  - Use when: you use a custom discovery prefix.

- MQTT_NODE_ID
  - What it does: node identifier used in topic/entity naming.
  - Use when: you run multiple instances or want distinct topic namespaces.

### Data and Availability Timing

- HA_EXPIRE_TIME
  - What it does: Home Assistant entity expire_after value (seconds).
  - Use when: tuning how quickly entities become unavailable if updates stop.

- GET_DATA_INTERVAL
  - What it does: interval between cloud data fetches (seconds).
  - Use when: balancing data freshness vs API load.

- HASS_INTERVAL
  - What it does: interval for Home Assistant publication/update loop (seconds).
  - Use when: tuning entity update cadence.

- Auto_update_token
  - What it does: enables periodic token refresh.
  - Use when: sessions expire in your environment and you want proactive token renewal.

### Troubleshooting and Logging

- DEVELOPERS_MODE
  - What it does: enables additional developer/debug behavior.
  - Use when: troubleshooting only.

- LOG_LEVEL
  - What it does: controls verbosity of logs.
  - Allowed values: DEBUG, INFO, WARNING, ERROR, CRITICAL.
  - Use when: set DEBUG for diagnostics, INFO for normal use.

## Recommended Safe Defaults

For most users:
- Keep EXPERIMENTAL_CUSTOM_API_URLS as false.
- Keep DEBUG_FORCE_API_VERSION as false.
- Keep DEVELOPERS_MODE as false.
- Use INFO log level.

## Troubleshooting Basics

- Login errors:
  - verify HOYMILES_USER/HOYMILES_PASSWORD,
  - verify your plant ID.
- No entities in Home Assistant:
  - verify MQTT connectivity,
  - verify discovery prefix and node id,
  - review add-on logs.
- Intermittent cloud/API issues:
  - enable Auto_update_token,
  - use DEBUG_FORCE_API_VERSION only for temporary diagnostics.

## Additional Documentation

Technical and project/internal markdown files are in the doc directory.
