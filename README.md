# Gluetun status – Home Assistant custom component

This is a Home Assistant custom integration that reads VPN status information from a [Gluetun](https://github.com/qdm12/gluetun) instance via its **HTTP Control Server**. It exposes sensors for:
- **Public IP address** from `/v1/publicip/ip`
- **Country** from `/v1/publicip/ip`
- **City** from `/v1/publicip/ip`
- **Location** from `/v1/publicip/ip`
- **Organization** from `/v1/publicip/ip`
- **Postal Code** from `/v1/publicip/ip`
- **Public Ip** from `/v1/publicip/ip`
- **Region** from `/v1/publicip/ip`
- **Status** from `/v1/openvpn/status`
- **Timezone** from `/v1/publicip/ip`
> Ensure Gluetun’s HTTP Control Server is enabled and reachable from Home Assistant. (These endpoints reflect the project’s existing behavior.)

## Installation

### HACS (as a custom repository)

1. In Home Assistant, open **HACS → Integrations**.  
2. Click **⋯ (three dots)** → **Custom repositories**.  
3. Paste `https://github.com/madcowGit/gluetun_cc` and select **Type: Integration**, then click **Add**.  
4. Back in HACS, search for **Gluetun (custom component)** and click **Install**.  
5. Restart Home Assistant when prompted.

### Manual

Copy the `custom_components/gluetun_cc/` directory into your HA `config/custom_components/` and restart.

## Requirements

- A running **Gluetun** with the **HTTP Control Server** enabled and accessible (e.g., `http://<gluetun-host>:8000`).

## Configuration (UI)

1. Go to **Settings → Devices & services → Add integration** and search for **Gluetun (custom component)**.  
2. Enter the HTTP Control Server details.  
3. Finish the flow; entities for VPN status, public IP, and country (if available) will be created.
## Acknowledgments

- Thanks to **qdm12** for the Gluetun project.

# Apache License

Version 2.0, January 2004

http://www.apache.org/licenses/

Copyright 2025 madcowGit

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

